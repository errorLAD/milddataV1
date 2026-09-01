from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, Count
import datetime

from core.mixins import TenantRequiredMixin
from .models import DraftOrder, SalesBlastHistory, CustomerProductBlastLog, SalesAgentSettings, SalesAgentTemplate

def seed_default_templates(business):
    if SalesAgentTemplate.objects.filter(business=business).exists():
        return

    defaults = [
        ('welcome', 'Welcome Message', 'Namaste {{customer_name}}! Main aapka AI Sales Assistant hoon. Aap humare products ke baare mein pooch sakte hain (Price, Stock, Order).'),
        ('product_inquiry', 'Product Inquiry Response', 'Namaste {{customer_name}}! {{product_name}} ka price ₹{{price}} per unit hai. Available stock: {{stock}} units.'),
        ('price_reply', 'Product Price Reply', 'Namaste {{customer_name}}! {{product_name}} ki price ₹{{price}} per unit hai.'),
        ('stock_reply', 'Stock Availability Reply', 'Namaste {{customer_name}}! {{product_name}} abhi stock mein available hai ({{stock}} units). Price: ₹{{price}}.'),
        ('recommendation', 'Product Recommendation', 'Namaste {{customer_name}}! Aapke liye best available options: {{recommendations}}. Aap isme se koi bhi order kar sakte hain!'),
        ('customer_interested', 'Customer Interested / Quantity Prompt', 'Ji bilkul {{customer_name}}! {{product_name}} (₹{{price}}) ke kitne packets / units chahiye? (e.g. 1 packet, 2 packets)'),
        ('order_confirmation', 'Order Confirmation / Draft', 'Namaste {{customer_name}}! Aapka order for {{quantity}}x {{product_name}} (Total: ₹{{total_amount}}) draft order me log ho gaya hai. Store owner ki approval ke baad final confirmation message aayega! Dhanyawad.'),
        ('payment_message', 'Payment Message / Link', 'Namaste {{customer_name}}! Aap {{total_amount}} ka payment {{payment_link}} par kar sakte hain.'),
        ('order_status', 'Order Status Message', 'Namaste {{customer_name}}! Aapka order status updated hai. Store owner jald hi dispatch details share karenge.'),
        ('followup', 'Follow-up Message', 'Namaste {{customer_name}}! Kya aapko {{product_name}} ke baare me koi help chahiye?'),
        ('out_of_stock', 'Out-of-Stock Message', 'Namaste {{customer_name}}! Maaf kijiyega, {{product_name}} abhi Out of Stock hai. Store owner restock hote hi aapko notify karenge.'),
        ('human_handoff', 'Human Handoff Message', 'Namaste {{customer_name}}! Aapka inquiry message receive ho gaya hai. Store owner jald hi aapko contact karenge.'),
        ('general', 'General AI Reply', 'Namaste {{customer_name}}! Main aapki help ke liye yahan hoon. Aap product info ya order ke baare me pooch sakte hain.'),
    ]

    for m_type, name, content in defaults:
        SalesAgentTemplate.objects.create(
            business=business,
            message_type=m_type,
            name=name,
            content=content,
            is_active=True
        )

class DashboardView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        today = timezone.now().date()
        seed_default_templates(business)

        # Settings
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=business)

        # Sales Conversations
        sales_conversations = WhatsAppConversation.objects.filter(
            business=business,
            conversation_type='sales'
        ).order_by('-last_message_at')

        # Pending Draft Orders
        pending_drafts = DraftOrder.objects.filter(
            business=business,
            status='Pending Owner Confirmation'
        ).order_by('-created_at')

        # Today's AI-driven Sales
        today_approved = DraftOrder.objects.filter(
            business=business,
            status='Approved',
            created_at__date=today
        )
        today_sales_count = today_approved.count()
        today_sales_value = today_approved.aggregate(s=Sum('total_amount'))['s'] or 0

        # Pending Handoffs
        pending_handoffs_count = sales_conversations.filter(is_human_takeover=True).count()

        # Conversion Stats
        total_inquiries = sales_conversations.count()
        total_orders_placed = DraftOrder.objects.filter(business=business).count()
        conversion_percent = round((total_orders_placed / total_inquiries * 100), 1) if total_inquiries > 0 else 0

        return render(request, 'sales_agent/dashboard.html', {
            'settings': settings_obj,
            'sales_conversations': sales_conversations[:15],
            'pending_drafts': pending_drafts,
            'today_sales_count': today_sales_count,
            'today_sales_value': today_sales_value,
            'pending_handoffs_count': pending_handoffs_count,
            'total_inquiries': total_inquiries,
            'total_orders_placed': total_orders_placed,
            'conversion_percent': conversion_percent,
        })

class ApproveDraftOrderView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        draft = get_object_or_404(DraftOrder, pk=pk, business=business)

        if draft.status == 'Approved':
            messages.info(request, f"Draft Order #{draft.id} is already approved.")
            return redirect('sales_agent:dashboard')

        # Create real Sale record
        inv_no = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        sale = Sale.objects.create(
            business=business,
            invoice_number=inv_no,
            customer=draft.customer,
            total_amount=draft.total_amount,
            paid_amount=draft.total_amount,
            udhaar_amount=0,
            sale_date=timezone.now().date(),
            payment_status='Paid',
            notes=f"AI Draft Order #{draft.id} approved by owner."
        )

        # Create SaleItem
        if draft.product:
            SaleItem.objects.create(
                sale=sale,
                product=draft.product,
                quantity=draft.quantity,
                unit_price=draft.unit_price,
                total_price=draft.total_amount
            )
            # Deduct Product Stock
            draft.product.stock_quantity = max(0, draft.product.stock_quantity - draft.quantity)
            draft.product.save()

        # Create Payment Record
        Payment.objects.create(
            business=business,
            customer=draft.customer,
            sale=sale,
            amount=draft.total_amount,
            payment_method='Cash',
            reference_id=f"AI-DRAFT-{draft.id}",
            status='Paid',
            notes="Payment for AI Sales Agent Draft Order"
        )

        # Mark Draft as Approved
        draft.status = 'Approved'
        draft.converted_sale = sale
        draft.save()

        # Notify Customer on WhatsApp
        conv, _ = WhatsAppConversation.objects.get_or_create(
            business=business,
            customer=draft.customer,
            defaults={'conversation_type': 'sales'}
        )
        prod_name = draft.product.name if draft.product else "Items"
        msg_text = f"🎉 Namaste {draft.customer.name}! Aapka order ({draft.quantity}x {prod_name} = ₹{draft.total_amount:,.2f}) APPROVE ho gaya hai! Invoice #{sale.invoice_number} generate ho chuka hai. Product dispatch ke liye ready hai. Dhanyawad!"
        WhatsAppMessage.objects.create(
            conversation=conv,
            sender='system',
            message_text=msg_text,
            status='Sent'
        )

        messages.success(request, f"Draft Order #{draft.id} APPROVED! Created Sale Invoice #{sale.invoice_number}.")
        return redirect('sales_agent:dashboard')

class RejectDraftOrderView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        draft = get_object_or_404(DraftOrder, pk=pk, business=business)

        draft.status = 'Rejected'
        draft.save()

        # Notify Customer on WhatsApp
        conv = WhatsAppConversation.objects.filter(business=business, customer=draft.customer).first()
        if conv:
            prod_name = draft.product.name if draft.product else "Item"
            msg_text = f"Namaste {draft.customer.name}, aapka recent draft request for {prod_name} currently accept nahi ho paya hai. Store owner se sampark karein."
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=msg_text,
                status='Sent'
            )

        messages.info(request, f"Draft Order #{draft.id} rejected.")
        return redirect('sales_agent:dashboard')

class ImportBlastView(TenantRequiredMixin, View):
    def get(self, request):
        form = PDFUploadForm()
        return render(request, 'sales_agent/import_blast.html', {
            'form': form,
            'preview_rows': None,
            'is_scanned': False,
            'error': None
        })

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            parse_res = parse_customer_pdf(pdf_file)

            if parse_res['is_scanned'] or parse_res['error']:
                return render(request, 'sales_agent/import_blast.html', {
                    'form': form,
                    'preview_rows': None,
                    'is_scanned': True,
                    'error': parse_res['error']
                })

            return render(request, 'sales_agent/import_blast.html', {
                'form': form,
                'preview_rows': parse_res['rows'],
                'is_scanned': False,
                'error': None
            })

        return render(request, 'sales_agent/import_blast.html', {
            'form': form,
            'preview_rows': None,
            'is_scanned': False,
            'error': 'Invalid PDF form submission.'
        })

class ConfirmImportView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        indices = request.POST.getlist('row_indices')

        created_count = 0
        updated_count = 0

        for idx in indices:
            name = request.POST.get(f'name_{idx}', '').strip()
            phone = request.POST.get(f'phone_{idx}', '').strip()
            notes = request.POST.get(f'notes_{idx}', '').strip()

            if not phone:
                continue

            # Match against existing customer by phone
            clean_phone = phone[-10:]
            cust = Customer.objects.filter(business=business, phone__icontains=clean_phone).first()

            if cust:
                if name and cust.name.startswith('Customer'):
                    cust.name = name
                if notes and not cust.notes:
                    cust.notes = notes
                cust.accepts_marketing = True
                cust.save()
                updated_count += 1
            else:
                Customer.objects.create(
                    business=business,
                    name=name or f"Customer {clean_phone}",
                    phone=phone,
                    notes=notes,
                    accepts_marketing=True,
                    status='Active'
                )
                created_count += 1

        messages.success(request, f"Import Confirmed! Created {created_count} new customer records and updated {updated_count} existing customers.")
        return redirect('sales_agent:send_blast')

class SendBlastView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        form = SalesBlastForm(business=business)
        customers = Customer.objects.filter(business=business, accepts_marketing=True)

        return render(request, 'sales_agent/send_blast.html', {
            'form': form,
            'customers': customers
        })

    def post(self, request):
        business = request.business
        form = SalesBlastForm(request.POST, business=business)
        
        prod_id = request.POST.get('product')
        template_id = request.POST.get('template')
        custom_msg = request.POST.get('custom_message', '').strip()
        recipient_target = request.POST.get('recipient_target', 'all')
        selected_cust_ids = request.POST.getlist('selected_customers')

        product = get_object_or_404(Product, pk=prod_id, business=business)
        template = WhatsAppMessageTemplate.objects.filter(pk=template_id, business=business).first() if template_id else None

        # Build recipient queryset
        recipients = Customer.objects.filter(business=business, accepts_marketing=True)
        if recipient_target == 'selected' and selected_cust_ids:
            recipients = recipients.filter(id__in=selected_cust_ids)

        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=business)
        anti_spam_hours = settings_obj.anti_spam_window_hours or 24
        now = timezone.now()

        sent_count = 0
        skipped_count = 0

        for cust in recipients:
            # Check Anti-Spam Hygiene Window
            log_entry = CustomerProductBlastLog.objects.filter(business=business, customer=cust, product=product).first()
            if log_entry:
                hours_diff = (now - log_entry.last_blasted_at).total_seconds() / 3600.0
                if hours_diff < anti_spam_hours:
                    skipped_count += 1
                    continue

            # Base message text
            if custom_msg:
                body = custom_msg
            elif template:
                body = template.content
            else:
                body = "Namaste {name}! {product} abhi stock me available hai, price ₹{price}. Reply karein agar aap interested hain!"

            # Replace Placeholders
            body = body.replace('{name}', cust.name)
            body = body.replace('{product}', product.name)
            body = body.replace('{price}', f"₹{product.selling_price:,.2f}")

            # Send WhatsApp Message
            conv, _ = WhatsAppConversation.objects.get_or_create(
                business=business,
                customer=cust,
                defaults={'conversation_type': 'sales'}
            )
            conv.conversation_type = 'sales'
            conv.save()

            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=body,
                status='Sent'
            )

            # Update Blast Log
            if not log_entry:
                CustomerProductBlastLog.objects.create(business=business, customer=cust, product=product, last_blasted_at=now)
            else:
                log_entry.last_blasted_at = now
                log_entry.save()

            sent_count += 1

        # Create Blast History Record
        SalesBlastHistory.objects.create(
            business=business,
            product=product,
            template=template,
            recipient_count=sent_count,
            reply_count=0
        )

        msg_str = f"Sales Blast for '{product.name}' dispatched to {sent_count} customers!"
        if skipped_count > 0:
            msg_str += f" ({skipped_count} skipped due to {anti_spam_hours}h anti-spam window)."
        messages.success(request, msg_str)
        return redirect('sales_agent:blast_history')

class BlastHistoryListView(TenantRequiredMixin, ListView):
    model = SalesBlastHistory
    template_name = 'sales_agent/blast_history.html'
    context_object_name = 'blasts'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().filter(business=self.request.business)

class SalesAgentSettingsView(TenantRequiredMixin, View):
    def get(self, request):
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=request.business)
        form = SalesAgentSettingsForm(instance=settings_obj)
        return render(request, 'sales_agent/settings.html', {'form': form})

    def post(self, request):
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=request.business)
        form = SalesAgentSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "AI Sales Agent Settings updated successfully!")
            return redirect('sales_agent:settings')
        return render(request, 'sales_agent/settings.html', {'form': form})

class TemplateListView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        seed_default_templates(business)
        templates = SalesAgentTemplate.objects.filter(business=business).order_by('message_type', 'name')
        choices = SalesAgentTemplate.MESSAGE_TYPE_CHOICES
        return render(request, 'sales_agent/templates_list.html', {
            'templates': templates,
            'choices': choices
        })

class TemplateSaveView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        t_id = request.POST.get('template_id')
        name = request.POST.get('name', '').strip()
        m_type = request.POST.get('message_type')
        content = request.POST.get('content', '').strip()
        is_active = request.POST.get('is_active') in ['on', 'true', '1']

        if t_id:
            tpl = get_object_or_404(SalesAgentTemplate, pk=t_id, business=business)
            tpl.name = name
            tpl.message_type = m_type
            tpl.content = content
            tpl.is_active = is_active
            tpl.save()
            messages.success(request, f"Template '{tpl.name}' updated successfully!")
        else:
            tpl = SalesAgentTemplate.objects.create(
                business=business,
                name=name,
                message_type=m_type,
                content=content,
                is_active=is_active
            )
            messages.success(request, f"New Template '{tpl.name}' created!")

        return redirect('sales_agent:templates_list')

class TemplateToggleActiveView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        tpl = get_object_or_404(SalesAgentTemplate, pk=pk, business=business)
        tpl.is_active = not tpl.is_active
        tpl.save()
        status_str = "ACTIVE" if tpl.is_active else "INACTIVE"
        messages.info(request, f"Template '{tpl.name}' status set to {status_str}.")
        return redirect('sales_agent:templates_list')

class TemplateDeleteView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        tpl = get_object_or_404(SalesAgentTemplate, pk=pk, business=business)
        tpl.delete()
        messages.success(request, "Template deleted.")
        return redirect('sales_agent:templates_list')
from .forms import PDFUploadForm, SalesBlastForm, SalesAgentSettingsForm
from .pdf_parser import parse_customer_pdf
from customers.models import Customer
from products.models import Product
from sales.models import Sale, SaleItem
from whatsapp.models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate
from payments.models import Payment

class DashboardView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        today = timezone.now().date()

        # Settings
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=business)

        # Sales Conversations
        sales_conversations = WhatsAppConversation.objects.filter(
            business=business,
            conversation_type='sales'
        ).order_by('-last_message_at')

        # Pending Draft Orders
        pending_drafts = DraftOrder.objects.filter(
            business=business,
            status='Pending Owner Confirmation'
        ).order_by('-created_at')

        # Today's AI-driven Sales
        today_approved = DraftOrder.objects.filter(
            business=business,
            status='Approved',
            created_at__date=today
        )
        today_sales_count = today_approved.count()
        today_sales_value = today_approved.aggregate(s=Sum('total_amount'))['s'] or 0

        # Pending Handoffs
        pending_handoffs_count = sales_conversations.filter(is_human_takeover=True).count()

        # Conversion Stats
        total_inquiries = sales_conversations.count()
        total_orders_placed = DraftOrder.objects.filter(business=business).count()
        conversion_percent = round((total_orders_placed / total_inquiries * 100), 1) if total_inquiries > 0 else 0

        return render(request, 'sales_agent/dashboard.html', {
            'settings': settings_obj,
            'sales_conversations': sales_conversations[:15],
            'pending_drafts': pending_drafts,
            'today_sales_count': today_sales_count,
            'today_sales_value': today_sales_value,
            'pending_handoffs_count': pending_handoffs_count,
            'total_inquiries': total_inquiries,
            'total_orders_placed': total_orders_placed,
            'conversion_percent': conversion_percent,
        })

class ApproveDraftOrderView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        draft = get_object_or_404(DraftOrder, pk=pk, business=business)

        if draft.status == 'Approved':
            messages.info(request, f"Draft Order #{draft.id} is already approved.")
            return redirect('sales_agent:dashboard')

        # Create real Sale record
        inv_no = f"INV-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        sale = Sale.objects.create(
            business=business,
            invoice_number=inv_no,
            customer=draft.customer,
            total_amount=draft.total_amount,
            paid_amount=draft.total_amount,
            udhaar_amount=0,
            sale_date=timezone.now().date(),
            payment_status='Paid',
            notes=f"AI Draft Order #{draft.id} approved by owner."
        )

        # Create SaleItem
        if draft.product:
            SaleItem.objects.create(
                sale=sale,
                product=draft.product,
                quantity=draft.quantity,
                unit_price=draft.unit_price,
                total_price=draft.total_amount
            )
            # Deduct Product Stock
            draft.product.stock_quantity = max(0, draft.product.stock_quantity - draft.quantity)
            draft.product.save()

        # Create Payment Record
        Payment.objects.create(
            business=business,
            customer=draft.customer,
            sale=sale,
            amount=draft.total_amount,
            payment_method='Cash',
            reference_id=f"AI-DRAFT-{draft.id}",
            status='Paid',
            notes="Payment for AI Sales Agent Draft Order"
        )

        # Mark Draft as Approved
        draft.status = 'Approved'
        draft.converted_sale = sale
        draft.save()

        # Notify Customer on WhatsApp
        conv, _ = WhatsAppConversation.objects.get_or_create(
            business=business,
            customer=draft.customer,
            defaults={'conversation_type': 'sales'}
        )
        prod_name = draft.product.name if draft.product else "Items"
        msg_text = f"🎉 Namaste {draft.customer.name}! Aapka order ({draft.quantity}x {prod_name} = ₹{draft.total_amount:,.2f}) APPROVE ho gaya hai! Invoice #{sale.invoice_number} generate ho chuka hai. Product dispatch ke liye ready hai. Dhanyawad!"
        WhatsAppMessage.objects.create(
            conversation=conv,
            sender='system',
            message_text=msg_text,
            status='Sent'
        )

        messages.success(request, f"Draft Order #{draft.id} APPROVED! Created Sale Invoice #{sale.invoice_number}.")
        return redirect('sales_agent:dashboard')

class RejectDraftOrderView(TenantRequiredMixin, View):
    def post(self, request, pk):
        business = request.business
        draft = get_object_or_404(DraftOrder, pk=pk, business=business)

        draft.status = 'Rejected'
        draft.save()

        # Notify Customer on WhatsApp
        conv = WhatsAppConversation.objects.filter(business=business, customer=draft.customer).first()
        if conv:
            prod_name = draft.product.name if draft.product else "Item"
            msg_text = f"Namaste {draft.customer.name}, aapka recent draft request for {prod_name} currently accept nahi ho paya hai. Store owner se sampark karein."
            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=msg_text,
                status='Sent'
            )

        messages.info(request, f"Draft Order #{draft.id} rejected.")
        return redirect('sales_agent:dashboard')

class ImportBlastView(TenantRequiredMixin, View):
    def get(self, request):
        form = PDFUploadForm()
        return render(request, 'sales_agent/import_blast.html', {
            'form': form,
            'preview_rows': None,
            'is_scanned': False,
            'error': None
        })

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = request.FILES['pdf_file']
            parse_res = parse_customer_pdf(pdf_file)

            if parse_res['is_scanned'] or parse_res['error']:
                return render(request, 'sales_agent/import_blast.html', {
                    'form': form,
                    'preview_rows': None,
                    'is_scanned': True,
                    'error': parse_res['error']
                })

            return render(request, 'sales_agent/import_blast.html', {
                'form': form,
                'preview_rows': parse_res['rows'],
                'is_scanned': False,
                'error': None
            })

        return render(request, 'sales_agent/import_blast.html', {
            'form': form,
            'preview_rows': None,
            'is_scanned': False,
            'error': 'Invalid PDF form submission.'
        })

class ConfirmImportView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        indices = request.POST.getlist('row_indices')

        created_count = 0
        updated_count = 0

        for idx in indices:
            name = request.POST.get(f'name_{idx}', '').strip()
            phone = request.POST.get(f'phone_{idx}', '').strip()
            notes = request.POST.get(f'notes_{idx}', '').strip()

            if not phone:
                continue

            # Match against existing customer by phone
            clean_phone = phone[-10:]
            cust = Customer.objects.filter(business=business, phone__icontains=clean_phone).first()

            if cust:
                if name and cust.name.startswith('Customer'):
                    cust.name = name
                if notes and not cust.notes:
                    cust.notes = notes
                cust.accepts_marketing = True
                cust.save()
                updated_count += 1
            else:
                Customer.objects.create(
                    business=business,
                    name=name or f"Customer {clean_phone}",
                    phone=phone,
                    notes=notes,
                    accepts_marketing=True,
                    status='Active'
                )
                created_count += 1

        messages.success(request, f"Import Confirmed! Created {created_count} new customer records and updated {updated_count} existing customers.")
        return redirect('sales_agent:send_blast')

class SendBlastView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        form = SalesBlastForm(business=business)
        customers = Customer.objects.filter(business=business, accepts_marketing=True)

        return render(request, 'sales_agent/send_blast.html', {
            'form': form,
            'customers': customers
        })

    def post(self, request):
        business = request.business
        form = SalesBlastForm(request.POST, business=business)
        
        prod_id = request.POST.get('product')
        template_id = request.POST.get('template')
        custom_msg = request.POST.get('custom_message', '').strip()
        recipient_target = request.POST.get('recipient_target', 'all')
        selected_cust_ids = request.POST.getlist('selected_customers')

        product = get_object_or_404(Product, pk=prod_id, business=business)
        template = WhatsAppMessageTemplate.objects.filter(pk=template_id, business=business).first() if template_id else None

        # Build recipient queryset
        recipients = Customer.objects.filter(business=business, accepts_marketing=True)
        if recipient_target == 'selected' and selected_cust_ids:
            recipients = recipients.filter(id__in=selected_cust_ids)

        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=business)
        anti_spam_hours = settings_obj.anti_spam_window_hours or 24
        now = timezone.now()

        sent_count = 0
        skipped_count = 0

        for cust in recipients:
            # Check Anti-Spam Hygiene Window
            log_entry = CustomerProductBlastLog.objects.filter(business=business, customer=cust, product=product).first()
            if log_entry:
                hours_diff = (now - log_entry.last_blasted_at).total_seconds() / 3600.0
                if hours_diff < anti_spam_hours:
                    skipped_count += 1
                    continue

            # Base message text
            if custom_msg:
                body = custom_msg
            elif template:
                body = template.content
            else:
                body = "Namaste {name}! {product} abhi stock me available hai, price ₹{price}. Reply karein agar aap interested hain!"

            # Replace Placeholders
            body = body.replace('{name}', cust.name)
            body = body.replace('{product}', product.name)
            body = body.replace('{price}', f"₹{product.selling_price:,.2f}")

            # Send WhatsApp Message
            conv, _ = WhatsAppConversation.objects.get_or_create(
                business=business,
                customer=cust,
                defaults={'conversation_type': 'sales'}
            )
            conv.conversation_type = 'sales'
            conv.save()

            WhatsAppMessage.objects.create(
                conversation=conv,
                sender='system',
                message_text=body,
                status='Sent'
            )

            # Update Blast Log
            if not log_entry:
                CustomerProductBlastLog.objects.create(business=business, customer=cust, product=product, last_blasted_at=now)
            else:
                log_entry.last_blasted_at = now
                log_entry.save()

            sent_count += 1

        # Create Blast History Record
        SalesBlastHistory.objects.create(
            business=business,
            product=product,
            template=template,
            recipient_count=sent_count,
            reply_count=0
        )

        msg_str = f"Sales Blast for '{product.name}' dispatched to {sent_count} customers!"
        if skipped_count > 0:
            msg_str += f" ({skipped_count} skipped due to {anti_spam_hours}h anti-spam window)."
        messages.success(request, msg_str)
        return redirect('sales_agent:blast_history')

class BlastHistoryListView(TenantRequiredMixin, ListView):
    model = SalesBlastHistory
    template_name = 'sales_agent/blast_history.html'
    context_object_name = 'blasts'
    paginate_by = 20

    def get_queryset(self):
        return super().get_queryset().filter(business=self.request.business)

class SalesAgentSettingsView(TenantRequiredMixin, View):
    def get(self, request):
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=request.business)
        form = SalesAgentSettingsForm(instance=settings_obj)
        return render(request, 'sales_agent/settings.html', {'form': form})

    def post(self, request):
        settings_obj, _ = SalesAgentSettings.objects.get_or_create(business=request.business)
        form = SalesAgentSettingsForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "AI Sales Agent Settings updated successfully!")
            return redirect('sales_agent:settings')
        return render(request, 'sales_agent/settings.html', {'form': form})
