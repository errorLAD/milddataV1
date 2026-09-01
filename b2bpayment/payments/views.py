from django.shortcuts import render
from django.views.generic import ListView
from django.db.models import Sum, Q
from django.utils import timezone

from core.mixins import TenantRequiredMixin
from .models import Payment

class PaymentListView(TenantRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        method = self.request.GET.get('method', '').strip()
        verif = self.request.GET.get('verification', '').strip()

        if query:
            qs = qs.filter(Q(customer__name__icontains=query) | Q(reference_id__icontains=query))
        if method:
            qs = qs.filter(payment_method=method)
        if verif:
            qs = qs.filter(verification_status=verif)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_payments = Payment.objects.filter(business=self.request.business)
        today = timezone.now().date()

        context['total_received'] = all_payments.filter(status='Paid').aggregate(s=Sum('amount'))['s'] or 0
        context['today_received'] = all_payments.filter(status='Paid', created_at__date=today).aggregate(s=Sum('amount'))['s'] or 0
        context['pending_verification_count'] = all_payments.filter(verification_status='Pending Verification').count()

        context['search_query'] = self.request.GET.get('q', '')
        context['method_filter'] = self.request.GET.get('method', '')
        context['verification_filter'] = self.request.GET.get('verification', '')
        return context
