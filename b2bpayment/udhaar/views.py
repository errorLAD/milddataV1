from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.generic import ListView, DetailView, View, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q, F
import datetime

from core.mixins import TenantRequiredMixin
from .models import Udhaar
from .forms import UdhaarForm, PartialPaymentForm, ChangeDueDateForm, PromiseForm
from payments.models import Payment
from whatsapp.models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate
from settings_app.models import BusinessSettings

class UdhaarListView(TenantRequiredMixin, ListView):
    model = Udhaar
    template_name = 'udhaar/udhaar_list.html'
    context_object_name = 'udhaars'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        today = timezone.now().date()

        # Update overdue statuses dynamically
        for u in qs.exclude(status__in=['Paid', 'Disputed']):
            if u.due_date and u.due_date < today and u.status != 'Overdue':
                u.status = 'Overdue'
                u.save()

        query = self.request.GET.get('q', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        due_filter = self.request.GET.get('due', '').strip()

        if query:
            qs = qs.filter(Q(customer__name__icontains=query) | Q(customer__phone__icontains=query))
        if status_filter:
            qs = qs.filter(status=status_filter)
        
        if due_filter == 'overdue':
            qs = qs.filter(due_date__lt=today).exclude(status='Paid')
        elif due_filter == 'today':
            qs = qs.filter(due_date=today).exclude(status='Paid')
        elif due_filter == 'soon':
            next_week = today + datetime.timedelta(days=7)
            qs = qs.filter(due_date__gte=today, due_date__lte=next_week).exclude(status='Paid')

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_udhaars = Udhaar.objects.filter(business=self.request.business)
        today = timezone.now().date()

        context['total_outstanding'] = all_udhaars.exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0
        context['total_overdue'] = all_udhaars.filter(due_date__lt=today).exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0
        context['due_today_count'] = all_udhaars.filter(due_date=today).exclude(status='Paid').count()
        context['total_recovered'] = all_udhaars.aggregate(s=Sum('paid_amount'))['s'] or 0

        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['due_filter'] = self.request.GET.get('due', '')
        return context

class UdhaarCreateView(TenantRequiredMixin, CreateView):
    model = Udhaar
    form_class = UdhaarForm
    template_name = 'udhaar/udhaar_form.html'
    success_url = reverse_lazy('udhaar:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['business'] = self.request.business
        return kwargs

    def form_valid(self, form):
        form.instance.business = self.request.business
        amt = form.cleaned_data['total_amount']
        form.instance.remaining_amount = amt
        form.instance.paid_amount = 0
        form.instance.status = 'Due'

        # Ensure server-side due_date if not set
        if not form.cleaned_data.get('due_date'):
            form.instance.due_date = timezone.now().date()

        # Check product selection from inline form
        product_id = self.request.POST.get('product_id')
        if product_id:
            from products.models import Product
            prod = Product.objects.filter(pk=product_id, business=self.request.business).first()
            if prod:
                note_str = form.cleaned_data.get('notes', '').strip()
                form.instance.notes = f"Item: {prod.name}" + (f" ({note_str})" if note_str else "")

        messages.success(self.request, f"Udhaar record created for {form.instance.customer.name}!")
        response = super().form_valid(form)

        source = self.request.POST.get('source')
        if source == 'khata':
            return redirect(f"{reverse_lazy('customers:detail', kwargs={'pk': form.instance.customer.pk})}#khata-pane")
        return response

class UdhaarDetailView(TenantRequiredMixin, DetailView):
    model = Udhaar
    template_name = 'udhaar/udhaar_detail.html'
    context_object_name = 'udhaar'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        u = self.object
        context['payment_form'] = PartialPaymentForm(initial={'amount': u.remaining_amount})
        context['due_date_form'] = ChangeDueDateForm(initial={'new_due_date': u.due_date})
        context['promise_form'] = PromiseForm(initial={'promised_date': u.promised_date, 'promised_amount': u.promised_amount or u.remaining_amount})
        from django.urls import reverse
        context['payments'] = Payment.objects.filter(udhaar=u).order_by('-created_at')
        context['business_settings'] = BusinessSettings.objects.filter(business=self.request.business).first()
        context['statement_url'] = self.request.build_absolute_uri(reverse('customers:public_detail', kwargs={'pk': u.customer.pk}))
        return context

class RecordPartialPaymentView(TenantRequiredMixin, View):
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        form = PartialPaymentForm(request.POST)
        if form.is_valid():
            amt = form.cleaned_data['amount']
            method = form.cleaned_data.get('payment_method', 'Cash') or 'Cash'
            ref = form.cleaned_data.get('reference_id', '') or ''
            notes = form.cleaned_data.get('notes', '') or ''
            is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.POST.get('format') == 'json'

            if amt > u.remaining_amount:
                if is_ajax:
                    return JsonResponse({'status': 'error', 'message': f"Payment amount cannot exceed remaining balance of ₹{u.remaining_amount:,.2f}"}, status=400)
                messages.error(request, f"Payment amount cannot exceed remaining balance of ₹{u.remaining_amount:,.2f}")
                return redirect('udhaar:detail', pk=u.pk)

            # Deduct remaining
            u.paid_amount += amt
            u.remaining_amount -= amt
            u.update_status()

            # Create Payment Record with server timestamp
            payment = Payment.objects.create(
                business=request.business,
                customer=u.customer,
                udhaar=u,
                sale=u.sale,
                amount=amt,
                payment_method=method,
                reference_id=ref,
                status='Paid',
                verification_status='Verified',
                notes=notes or "Payment recorded"
            )

            if is_ajax:
                return JsonResponse({
                    'status': 'success',
                    'paid_amount': float(amt),
                    'total_paid': float(u.paid_amount),
                    'remaining_amount': float(u.remaining_amount),
                    'is_paid': u.status == 'Paid',
                    'payment_date': payment.created_at.strftime('%d %b %Y, %I:%M %p'),
                    'message': f"Payment of ₹{amt:,.2f} recorded!"
                })

            source = request.POST.get('source') or request.GET.get('source')
            if source == 'khata':
                messages.success(request, f"Payment of ₹{amt:,.2f} recorded!")
                return redirect(f"{reverse_lazy('customers:detail', kwargs={'pk': u.customer.pk})}#khata-pane")

            messages.success(request, f"Payment of ₹{amt:,.2f} recorded! Remaining balance: ₹{u.remaining_amount:,.2f}")
            return redirect('udhaar:detail', pk=u.pk)

        source = request.POST.get('source') or request.GET.get('source')
        if source == 'khata':
            messages.error(request, "Invalid payment details submitted.")
            return redirect(f"{reverse_lazy('customers:detail', kwargs={'pk': u.customer.pk})}#khata-pane")
        return redirect('udhaar:detail', pk=u.pk)

class ChangeDueDateView(TenantRequiredMixin, View):
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        form = ChangeDueDateForm(request.POST)
        if form.is_valid():
            new_date = form.cleaned_data['new_due_date']
            u.due_date = new_date
            u.update_status()
            messages.success(request, f"Due date updated to {new_date.strftime('%d %b %Y')}")
        return redirect('udhaar:detail', pk=u.pk)

class SetPromiseView(TenantRequiredMixin, View):
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        form = PromiseForm(request.POST)
        if form.is_valid():
            p_date = form.cleaned_data['promised_date']
            p_amt = form.cleaned_data['promised_amount'] or u.remaining_amount
            u.promised_date = p_date
            u.promised_amount = p_amt
            u.status = 'Payment Promised'
            u.save()
            messages.success(request, f"Payment promise set for {p_date.strftime('%d %b %Y')} (₹{p_amt:,.2f})")
        return redirect('udhaar:detail', pk=u.pk)

class SendReminderView(TenantRequiredMixin, View):
    def post(self, request, pk):
        u = get_object_or_404(Udhaar, pk=pk, business=request.business)
        settings = BusinessSettings.objects.filter(business=request.business).first()

        # Find or create WhatsApp conversation
        conv, _ = WhatsAppConversation.objects.get_or_create(
            business=request.business,
            customer=u.customer
        )

        template = WhatsAppMessageTemplate.objects.filter(business=request.business, trigger_type='Due Reminder').first()
        msg_body = f"Namaste {u.customer.name}, {request.business.name} se aapka Udhaar balance ₹{u.remaining_amount:,.2f} due date ({u.due_date.strftime('%d %b %Y')}) par pending hai."
        if settings and settings.upi_id:
            msg_body += f"\nAap is UPI ID par pay kar sakte hain: {settings.upi_id}"

        WhatsAppMessage.objects.create(
            conversation=conv,
            sender='business',
            message_text=msg_body,
            status='Sent'
        )

        u.last_reminder_sent = timezone.now()
        u.save()

        messages.success(request, f"WhatsApp reminder sent to {u.customer.name}!")
        return redirect('udhaar:detail', pk=u.pk)
