import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy

from core.mixins import TenantRequiredMixin
from .models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate, WhatsAppCampaign, Tag
from .ai_parser import parse_customer_message
from .voice_transcription import transcribe_audio_file
from customers.models import Customer
from udhaar.models import Udhaar
from settings_app.models import BusinessSettings
from notifications.models import Notification

class WhatsAppInboxView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        conversations = WhatsAppConversation.objects.filter(business=business).order_by('-last_message_at')
        
        active_customer_id = request.GET.get('customer_id')
        active_conv = None

        if active_customer_id:
            customer = get_object_or_404(Customer, pk=active_customer_id, business=business)
            active_conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=customer)
        elif conversations.exists():
            active_conv = conversations.first()

        active_messages = active_conv.messages.all() if active_conv else []
        active_udhaar = active_conv.customer.udhaars.exclude(status='Paid').first() if active_conv else None

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            msgs_data = [{
                'id': m.id,
                'sender': m.sender,
                'text': m.message_text,
                'is_voice_note': m.is_voice_note,
                'transcript': m.transcript,
                'audio_url': m.audio_file.url if m.audio_file else '',
                'time': m.timestamp.strftime('%I:%M %p'),
                'status': m.status
            } for m in active_messages]
            return JsonResponse({'messages': msgs_data})

        return render(request, 'whatsapp/inbox.html', {
            'conversations': conversations,
            'active_conv': active_conv,
            'active_messages': active_messages,
            'active_udhaar': active_udhaar
        })

class SendMessageView(TenantRequiredMixin, View):
    def post(self, request, conv_id):
        conv = get_object_or_404(WhatsAppConversation, pk=conv_id, business=request.business)
        text = request.POST.get('message_text', '').strip()
        if text:
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='business',
                message_text=text,
                status='Sent'
            )
            conv.save()
        return redirect(f"/whatsapp/?customer_id={conv.customer.pk}")

class ToggleHumanTakeoverView(TenantRequiredMixin, View):
    def post(self, request, conv_id):
        conv = get_object_or_404(WhatsAppConversation, pk=conv_id, business=request.business)
        conv.is_human_takeover = not conv.is_human_takeover
        conv.save()
        status_str = "paused" if conv.is_human_takeover else "resumed"
        messages.info(request, f"AI automation for {conv.customer.name} is now {status_str}.")
        return redirect(f"/whatsapp/?customer_id={conv.customer.pk}")

class SendPaymentLinkView(TenantRequiredMixin, View):
    def post(self, request, conv_id):
        conv = get_object_or_404(WhatsAppConversation, pk=conv_id, business=request.business)
        settings_obj = BusinessSettings.objects.filter(business=request.business).first()
        active_udhaar = conv.customer.udhaars.exclude(status='Paid').first()

        amt_str = f"₹{active_udhaar.remaining_amount:,.2f}" if active_udhaar else "your balance"
        upi = settings_obj.upi_id if settings_obj and settings_obj.upi_id else "Business UPI"
        link = settings_obj.payment_link if settings_obj and settings_obj.payment_link else ""

        msg_body = f"Namaste {conv.customer.name}, aap {amt_str} ka bhugtan yahan kar sakte hain:\n"
        if link:
            msg_body += f"Payment Link: {link}\n"
        msg_body += f"UPI ID: {upi}\nPayment ke baad transaction ref yahin bhej dijiye."

        WhatsAppMessage.objects.create(
            conversation=conv,
            sender='business',
            message_text=msg_body,
            status='Sent'
        )
        messages.success(request, "Payment link sent to customer!")
        return redirect(f"/whatsapp/?customer_id={conv.customer.pk}")

class CampaignListView(TenantRequiredMixin, ListView):
    model = WhatsAppCampaign
    template_name = 'whatsapp/campaign_list.html'
    context_object_name = 'campaigns'
    paginate_by = 20

class CampaignCreateView(TenantRequiredMixin, View):
    def get(self, request):
        tags = Tag.objects.filter(business=request.business)
        customers = Customer.objects.filter(business=request.business, accepts_marketing=True)
        return render(request, 'whatsapp/campaign_form.html', {
            'tags': tags,
            'customers': customers
        })

    def post(self, request):
        business = request.business
        title = request.POST.get('title')
        text = request.POST.get('message_text')
        image = request.FILES.get('image')
        target_type = request.POST.get('target_type')
        tag_id = request.POST.get('target_tag')

        tag = Tag.objects.filter(pk=tag_id, business=business).first() if tag_id else None

        # Build recipient queryset respecting accepts_marketing=True
        recipients = Customer.objects.filter(business=business, accepts_marketing=True)
        if target_type == 'tag' and tag:
            recipients = recipients.filter(tags=tag)
        elif target_type == 'selected':
            selected_ids = request.POST.getlist('selected_customers')
            recipients = recipients.filter(id__in=selected_ids)

        campaign = WhatsAppCampaign.objects.create(
            business=business,
            title=title,
            message_text=text,
            image=image,
            target_type=target_type,
            target_tag=tag,
            sent_count=recipients.count()
        )

        # Dispatch Broadcast Messages (logged separately as Campaign messages)
        for cust in recipients:
            conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=cust)
            msg_content = f"📢 [CAMPAIGN: {title}]\n" + text.replace('{{customer_name}}', cust.name)
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=msg_content,
                status='Sent'
            )

        messages.success(request, f"Broadcast Campaign '{title}' dispatched to {recipients.count()} customers!")
        return redirect('whatsapp:campaign_list')

@method_decorator(csrf_exempt, name='dispatch')
class WhatsAppWebhookView(View):
    """
    Webhook receiving text or voice notes.
    """
    def post(self, request):
        phone = request.POST.get('phone', '').strip()
        msg_text = request.POST.get('message', '').strip()
        audio_file = request.FILES.get('audio')

        # Handle JSON body if posted as JSON
        if not phone and request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                phone = data.get('phone', '').strip()
                msg_text = data.get('message', '').strip()
            except Exception:
                pass

        if not phone:
            return JsonResponse({'error': 'Missing customer phone number'}, status=400)

        customer = Customer.objects.filter(phone__icontains=phone[-10:]).first()
        if not customer:
            return JsonResponse({'status': 'ignored', 'reason': 'Customer phone not registered'})

        business = customer.business
        settings_obj = BusinessSettings.objects.filter(business=business).first()
        conv, _ = WhatsAppConversation.objects.get_or_create(business=business, customer=customer)

        is_voice = False
        transcript = ""

        # Process Audio Voice Note
        if audio_file:
            is_voice = True
            msg = WhatsAppMessage.objects.create(
                conversation=conv,
                sender='customer',
                message_text="[🎤 Voice Note Audio]",
                is_voice_note=True,
                audio_file=audio_file,
                status='Read'
            )
            res = transcribe_audio_file(msg.audio_file.path)
            transcript = res['transcript']
            msg.transcript = transcript
            msg.message_text = f"🎤 Voice Note (transcribed): {transcript}"
            msg.save()
            msg_text = transcript
        else:
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='customer',
                message_text=msg_text,
                status='Read'
            )

        if conv.is_human_takeover:
            return JsonResponse({'status': 'success', 'action': 'human_takeover_active'})

        # Check conversation type and message content for Sales vs Recovery routing
        from products.models import Product
        from sales_agent.models import SalesAgentSettings, DraftOrder, SalesBlastHistory
        from sales_agent.ai_parser import parse_sales_message

        products = Product.objects.filter(business=business)
        sales_settings, _ = SalesAgentSettings.objects.get_or_create(business=business)

        msg_lower = msg_text.lower()
        sales_keywords = ['price', 'stock', 'rate', 'cost', 'buy', 'chahiye', 'kitne ka', 'available', 'order', 'daam', 'kharidna', 'bhejo', 'pack']
        has_prod_match = any(p.name.lower() in msg_lower for p in products)
        is_sales_msg = (conv.conversation_type == 'sales') or has_prod_match or any(k in msg_lower for k in sales_keywords)

        reply_text = ""
        intent = "unknown"

        if is_sales_msg and sales_settings.is_enabled:
            conv.conversation_type = 'sales'
            conv.save()

            recent_msgs = conv.messages.all().order_by('-timestamp')[:6]
            sales_res = parse_sales_message(msg_text, products, customer.name, conversation_messages=recent_msgs, business=business)
            intent = sales_res['intent']
            reply_text = sales_res['auto_reply']

            # Update blast history reply count if applicable
            latest_blast = SalesBlastHistory.objects.filter(business=business).order_by('-sent_at').first()
            if latest_blast:
                latest_blast.reply_count += 1
                latest_blast.save()

            # Create Draft Order if buying intent confirmed
            if sales_res['create_draft_order'] and sales_settings.auto_draft_orders:
                draft = DraftOrder.objects.create(
                    business=business,
                    customer=customer,
                    product=sales_res['matched_product'],
                    quantity=sales_res['quantity'],
                    unit_price=sales_res['unit_price'],
                    total_amount=sales_res['total_amount'],
                    status='Pending Owner Confirmation',
                    notes=f"AI Inbound WhatsApp Order ({msg_text})"
                )
                Notification.objects.create(
                    business=business,
                    title=f"New AI Draft Order: {customer.name}",
                    message=f"{customer.name} requested {sales_res['quantity']}x {sales_res['matched_product'].name} (₹{sales_res['total_amount']:,.2f})",
                    category='Sale',
                    link='/sales-agent/'
                )

            if sales_res['needs_owner']:
                conv.is_human_takeover = True
                conv.save()
                Notification.objects.create(
                    business=business,
                    title=f"Sales Handoff Needed: {customer.name}",
                    message=f"{customer.name} message requires owner attention: '{msg_text}'",
                    category='General',
                    link='/sales-agent/'
                )

        else:
            # AI Parser for Udhaar Recovery
            parsed = parse_customer_message(msg_text)
            intent = parsed['intent']
            active_udhaar = customer.udhaars.exclude(status='Paid').first()

            if intent == 'promise' and active_udhaar:
                p_date = parsed['promised_date']
                p_amt = parsed['promised_amount'] or active_udhaar.remaining_amount
                active_udhaar.promised_date = p_date
                active_udhaar.promised_amount = p_amt
                active_udhaar.status = 'Payment Promised'
                active_udhaar.save()

                Notification.objects.create(
                    business=business,
                    title=f"Payment Promised: {customer.name}",
                    message=f"{customer.name} promised to pay ₹{p_amt:,.2f} on {p_date.strftime('%d %b %Y')}.",
                    category='Promise',
                    link=f'/udhaar/{active_udhaar.pk}/'
                )
                reply_text = f"Dhanyawad {customer.name}! Humne aapki payment date {p_date.strftime('%d %b %Y')} note kar li hai."

            elif intent == 'ready_to_pay':
                upi = settings_obj.upi_id if settings_obj and settings_obj.upi_id else "Business UPI"
                link = settings_obj.payment_link if settings_obj and settings_obj.payment_link else ""
                reply_text = f"Bilkul {customer.name}! Aap yahan payment kar sakte hain:\n"
                if link: reply_text += f"Payment Link: {link}\n"
                reply_text += f"UPI ID: {upi}\nPayment ke baad confirmation ref yahin bhej dijiye."

            elif intent == 'paid_claimed' and active_udhaar:
                active_udhaar.verification_status = 'Payment Claimed'
                active_udhaar.save()
                Notification.objects.create(
                    business=business,
                    title=f"Payment Claimed: {customer.name}",
                    message=f"{customer.name} claims payment done. Please verify.",
                    category='Payment Received',
                    link=f'/udhaar/{active_udhaar.pk}/'
                )
                reply_text = f"Dhanyawad {customer.name}! Aapka claim receive ho gaya hai. Verify karke balance update karenge."

            elif intent == 'dispute' and active_udhaar:
                active_udhaar.status = 'Disputed'
                active_udhaar.save()
                conv.is_human_takeover = True
                conv.save()
                Notification.objects.create(
                    business=business,
                    title=f"Dispute Flagged: {customer.name}",
                    message=f"{customer.name} disputed balance: '{msg_text}'. Recovery paused.",
                    category='Dispute',
                    link=f'/udhaar/{active_udhaar.pk}/'
                )
                reply_text = f"Namaste {customer.name}, aapka dispute log ho gaya hai. Store owner jald hi contact karenge."

        if reply_text:
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=reply_text,
                status='Sent'
            )

        return JsonResponse({
            'status': 'success',
            'is_voice_note': is_voice,
            'transcript': transcript,
            'parsed_intent': intent,
            'auto_reply': reply_text
        })

class WhatsAppSandboxView(TenantRequiredMixin, View):
    def get(self, request):
        customers = Customer.objects.filter(business=request.business)
        return render(request, 'whatsapp/sandbox.html', {'customers': customers})
