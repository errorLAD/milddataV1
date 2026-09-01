import json
import io
import datetime
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.contrib import messages
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import get_template

from core.mixins import TenantRequiredMixin
from .models import Sale, SaleItem
from .forms import SaleForm
from products.models import Product
from customers.models import Customer
from udhaar.models import Udhaar
from payments.models import Payment
from notifications.models import Notification

class SaleListView(TenantRequiredMixin, ListView):
    model = Sale
    template_name = 'sales/sale_list.html'
    context_object_name = 'sales'
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        query = self.request.GET.get('q', '').strip()
        method_filter = self.request.GET.get('method', '').strip()

        if query:
            qs = qs.filter(Q(invoice_number__icontains=query) | Q(customer__name__icontains=query) | Q(customer__phone__icontains=query))
        if method_filter:
            qs = qs.filter(payment_method=method_filter)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['method_filter'] = self.request.GET.get('method', '')
        return context

class SaleCreateView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        customers = Customer.objects.filter(business=business)
        products = Product.objects.filter(business=business)
        
        preselected_customer_id = request.GET.get('customer_id')
        form = SaleForm(business=business, initial={'customer': preselected_customer_id})
        
        return render(request, 'sales/sale_form.html', {
            'form': form,
            'customers': customers,
            'products': products
        })

    def post(self, request):
        business = request.business
        form = SaleForm(request.POST, business=business)
        
        if form.is_valid():
            customer = form.cleaned_data['customer']
            total = form.cleaned_data['total_amount']
            discount = form.cleaned_data['discount'] or 0
            paid = form.cleaned_data['paid_amount'] or 0
            net_total = total - discount
            udhaar_amt = max(0, net_total - paid)

            # Soft Block Credit Limit Enforcement
            confirm_overlimit = request.POST.get('confirm_credit_overlimit')
            if udhaar_amt > 0 and customer.credit_limit and customer.credit_limit > 0:
                current_outstanding = customer.get_outstanding_udhaar
                projected_total = current_outstanding + udhaar_amt
                if projected_total > customer.credit_limit and confirm_overlimit != 'yes':
                    messages.warning(
                        request,
                        f"CREDIT LIMIT WARNING: This sale will increase {customer.name}'s outstanding to ₹{projected_total:,.2f}, exceeding their ₹{customer.credit_limit:,.2f} credit limit! Check the confirmation box below to proceed."
                    )
                    customers = Customer.objects.filter(business=business)
                    products = Product.objects.filter(business=business)
                    return render(request, 'sales/sale_form.html', {
                        'form': form,
                        'customers': customers,
                        'products': products,
                        'overlimit_warning': True,
                        'projected_outstanding': projected_total,
                        'customer_credit_limit': customer.credit_limit
                    })

            with transaction.atomic():
                sale = form.save(commit=False)
                sale.business = business
                
                # Generate Unique Invoice Number
                date_str = timezone.now().strftime("%Y%m%d")
                rand_num = random.randint(1000, 9999)
                sale.invoice_number = f"INV-{date_str}-{rand_num}"

                sale.total_amount = net_total
                sale.paid_amount = paid
                sale.udhaar_amount = udhaar_amt
                sale.save()

                # Line Items
                product_ids = request.POST.getlist('product_id[]')
                quantities = request.POST.getlist('quantity[]')
                unit_prices = request.POST.getlist('unit_price[]')

                for p_id, qty, price in zip(product_ids, quantities, unit_prices):
                    if p_id and int(qty) > 0:
                        prod = Product.objects.filter(business=business, pk=p_id).first()
                        p_name = prod.name if prod else "Custom Item"
                        q = int(qty)
                        u_price = float(price)
                        subt = q * u_price

                        SaleItem.objects.create(
                            sale=sale,
                            product=prod,
                            product_name=p_name,
                            quantity=q,
                            unit_price=u_price,
                            subtotal=subt
                        )

                        # Decrement Product Stock
                        if prod:
                            prod.stock_quantity = max(0, prod.stock_quantity - q)
                            prod.save()

                # If Paid > 0, Record Payment
                if paid > 0:
                    Payment.objects.create(
                        business=business,
                        customer=sale.customer,
                        sale=sale,
                        amount=paid,
                        payment_method=sale.payment_method,
                        reference_id=f"POS-{sale.invoice_number}",
                        status='Paid',
                        verification_status='Verified',
                        notes="Initial sale payment"
                    )

                # If Udhaar > 0, Automatically Create Udhaar Record
                if udhaar_amt > 0:
                    due_date = form.cleaned_data.get('due_date') or (timezone.now().date() + datetime.timedelta(days=7))

                    Udhaar.objects.create(
                        business=business,
                        customer=sale.customer,
                        sale=sale,
                        total_amount=udhaar_amt,
                        paid_amount=0,
                        remaining_amount=udhaar_amt,
                        due_date=due_date,
                        status='Due',
                        verification_status='Verified'
                    )

                messages.success(request, f"Sale #{sale.invoice_number} successfully recorded!")
                return redirect('sales:detail', pk=sale.pk)

        customers = Customer.objects.filter(business=business)
        products = Product.objects.filter(business=business)
        return render(request, 'sales/sale_form.html', {
            'form': form,
            'customers': customers,
            'products': products
        })

class SaleDetailView(TenantRequiredMixin, DetailView):
    model = Sale
    template_name = 'sales/sale_detail.html'
    context_object_name = 'sale'

class SaleInvoicePDFView(TenantRequiredMixin, View):
    def get(self, request, pk):
        sale = get_object_or_404(Sale, pk=pk, business=request.business)
        template = get_template('sales/invoice_pdf.html')
        html = template.render({'sale': sale, 'business': request.business})
        
        try:
            from xhtml2pdf import pisa
            result = io.BytesIO()
            pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
            if not pdf.err:
                response = HttpResponse(result.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="Invoice_{sale.invoice_number}.pdf"'
                return response
        except Exception:
            pass

        # Fallback to HTML render for direct browser printing
        return HttpResponse(html)
