from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from core.mixins import TenantRequiredMixin
from .models import Customer
from .forms import CustomerForm
from whatsapp.models import Tag

class CustomerListView(TenantRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        search_query = self.request.GET.get('q', '').strip()
        status_filter = self.request.GET.get('status', '').strip()
        has_udhaar = self.request.GET.get('has_udhaar', '').strip()
        tag_filter = self.request.GET.get('tag', '').strip()
        risk_filter = self.request.GET.get('risk', '').strip()

        if search_query:
            qs = qs.filter(Q(name__icontains=search_query) | Q(phone__icontains=search_query) | Q(address__icontains=search_query))
        if status_filter:
            qs = qs.filter(status=status_filter)
        if tag_filter:
            qs = qs.filter(tags__id=tag_filter)
        
        if has_udhaar == 'yes':
            qs = [c for c in qs if c.get_outstanding_udhaar > 0]

        if risk_filter:
            qs = [c for c in qs if c.risk_score['level'].lower().startswith(risk_filter.lower())]

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['has_udhaar'] = self.request.GET.get('has_udhaar', '')
        context['tag_filter'] = self.request.GET.get('tag', '')
        context['risk_filter'] = self.request.GET.get('risk', '')
        context['all_tags'] = Tag.objects.filter(business=self.request.business)
        return context

class CustomerCreateView(TenantRequiredMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'
    success_url = reverse_lazy('customers:list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['business'] = self.request.business
        return kwargs

    def form_valid(self, form):
        form.instance.business = self.request.business
        messages.success(self.request, f"Customer '{form.instance.name}' created successfully!")
        return super().form_valid(form)

class CustomerUpdateView(TenantRequiredMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/customer_form.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['business'] = self.request.business
        return kwargs

    def get_success_url(self):
        return reverse_lazy('customers:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, "Customer details updated!")
        return super().form_valid(form)

class CustomerDetailView(TenantRequiredMixin, DetailView):
    model = Customer
    template_name = 'customers/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object

        # Sales History
        sales = customer.sales.all().order_by('-sale_date')
        context['sales'] = sales

        # Payments History
        payments = customer.payments.all().order_by('-created_at')
        context['payments'] = payments

        # Udhaar History
        udhaars = customer.udhaars.all().order_by('-created_at')
        context['udhaars'] = udhaars

        # Collection-focused analytics
        last_payment = payments.first()
        context['last_payment'] = last_payment

        # Average payment delay calculation
        paid_udhaars = udhaars.filter(status='Paid', due_date__isnull=False)
        delay_sum = 0
        delay_count = 0
        for u in paid_udhaars:
            p = payments.filter(udhaar=u).order_by('-created_at').first()
            if p:
                d = (p.created_at.date() - u.due_date).days
                if d > 0:
                    delay_sum += d
                    delay_count += 1
        context['avg_payment_delay'] = round(delay_sum / delay_count, 1) if delay_count else 0

        # Collection Activities
        from b2bcollections.models import CollectionActivity
        activities = CollectionActivity.objects.filter(udhaar__customer=customer).select_related('udhaar')
        context['collection_activities'] = activities[:30]

        # Referrals list
        context['referrals'] = customer.referrals.all()
        context['all_tags'] = Tag.objects.filter(business=self.request.business)

        # WhatsApp Messages
        from whatsapp.models import WhatsAppMessage, WhatsAppConversation
        from settings_app.models import BusinessSettings
        from django.urls import reverse
        context['business_settings'] = BusinessSettings.objects.filter(business=self.request.business).first()
        context['statement_url'] = self.request.build_absolute_uri(reverse('customers:public_detail', kwargs={'pk': customer.pk}))
        conv = WhatsAppConversation.objects.filter(business=self.request.business, customer=customer).first()
        messages_qs = conv.messages.all().order_by('-timestamp')[:20] if conv else []
        context['whatsapp_messages'] = messages_qs
        context['whatsapp_conversation'] = conv

        # Combined Chronological Collection Timeline
        timeline_items = []
        for s in sales:
            timeline_items.append({
                'type': 'sale',
                'icon': 'bi-receipt',
                'badge': 'primary',
                'title': f"Invoice Generated #{s.invoice_number}",
                'amount': s.total_amount,
                'description': f"Invoice Total: ₹{s.total_amount:,.2f} (Paid: ₹{s.paid_amount:,.2f}, Due on Credit: ₹{s.udhaar_amount:,.2f})",
                'timestamp': s.created_at
            })
        for u in udhaars:
            if u.promised_date:
                timeline_items.append({
                    'type': 'promise',
                    'icon': 'bi-handshake',
                    'badge': 'warning' if u.promise_broken else 'info',
                    'title': "Promise Missed" if u.promise_broken else "Payment Promised",
                    'amount': u.promised_amount or u.remaining_amount,
                    'description': f"Commitment to pay ₹{u.promised_amount or u.remaining_amount:,.2f} on {u.promised_date.strftime('%d %b %Y')}",
                    'timestamp': u.updated_at if u.promise_broken else u.created_at
                })
        for act in activities:
            timeline_items.append({
                'type': 'activity',
                'icon': act.icon,
                'badge': act.badge_class,
                'title': act.get_activity_type_display(),
                'amount': act.amount,
                'description': f"{act.description} (by {act.performed_by or 'System'})",
                'timestamp': act.created_at
            })
        for p in payments:
            timeline_items.append({
                'type': 'payment',
                'icon': 'bi-check-circle-fill',
                'badge': 'success',
                'title': f"Payment Received ({p.payment_method})",
                'amount': p.amount,
                'description': f"₹{p.amount:,.2f} received. Ref: {p.reference_id or 'Cash'} - Status: {p.status}",
                'timestamp': p.created_at
            })
        if conv:
            for m in conv.messages.all():
                desc = m.message_text
                if m.is_voice_note:
                    desc = f"🎤 Voice Note Transcript: {m.transcript or desc}"
                timeline_items.append({
                    'type': 'whatsapp',
                    'icon': 'bi-whatsapp',
                    'badge': 'success' if m.sender == 'customer' else 'primary',
                    'title': f"WhatsApp from {m.sender.title()}",
                    'amount': None,
                    'description': desc,
                    'timestamp': m.timestamp
                })

        timeline_items.sort(key=lambda x: x['timestamp'], reverse=True)
        context['timeline'] = timeline_items[:40]

        return context

class CustomerPublicDetailView(DetailView):
    model = Customer
    template_name = 'customers/customer_public_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.object
        context['business'] = customer.business
        context['sales'] = customer.sales.all().order_by('-sale_date')
        context['payments'] = customer.payments.all().order_by('-created_at')
        context['udhaars'] = customer.udhaars.all().order_by('-created_at')

        from settings_app.models import BusinessSettings
        from django.urls import reverse
        context['business_settings'] = BusinessSettings.objects.filter(business=customer.business).first()
        context['statement_url'] = self.request.build_absolute_uri(reverse('customers:public_detail', kwargs={'pk': customer.pk}))
        return context

