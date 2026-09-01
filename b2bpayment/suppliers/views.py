import csv
import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Sum, Q

from core.mixins import TenantRequiredMixin
from products.models import Product
from .models import Supplier, SupplierPurchase, SupplierPurchaseItem, SupplierPayment
from .forms import SupplierForm, SupplierPurchaseForm, SupplierPaymentForm

class SupplierListView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        suppliers = Supplier.objects.filter(business=business)

        q = request.GET.get('q', '').strip()
        if q:
            suppliers = suppliers.filter(
                Q(supplier_name__icontains=q) |
                Q(phone__icontains=q) |
                Q(business_name__icontains=q)
            )

        # Calculate metrics
        tot_purchases = sum([s.total_purchases for s in suppliers])
        tot_paid = sum([s.total_paid for s in suppliers])
        tot_payable = sum([s.outstanding_payable for s in suppliers])

        return render(request, 'suppliers/supplier_list.html', {
            'suppliers': suppliers,
            'q': q,
            'tot_purchases': tot_purchases,
            'tot_paid': tot_paid,
            'tot_payable': tot_payable
        })

class SupplierDetailView(TenantRequiredMixin, View):
    def get(self, request, pk):
        business = request.business
        supplier = get_object_or_404(Supplier, pk=pk, business=business)
        purchases = supplier.purchases.all()
        payments = supplier.payments.all()

        today = timezone.now().date()
        due_today = purchases.filter(due_date=today, status__in=['Due', 'Overdue', 'Partially Paid']).aggregate(s=Sum('total_purchase'))['s'] or 0
        due_soon = purchases.filter(due_date__gt=today, due_date__lte=today + datetime.timedelta(days=7)).aggregate(s=Sum('total_purchase'))['s'] or 0

        return render(request, 'suppliers/supplier_detail.html', {
            'supplier': supplier,
            'purchases': purchases,
            'payments': payments,
            'due_today': due_today,
            'due_soon': due_soon
        })

class SupplierCreateView(TenantRequiredMixin, View):
    def get(self, request):
        form = SupplierForm()
        return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add New Supplier'})

    def post(self, request):
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.business = request.business
            supplier.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' added successfully!")
            return redirect('suppliers:detail', pk=supplier.pk)
        return render(request, 'suppliers/supplier_form.html', {'form': form, 'title': 'Add New Supplier'})

class SupplierUpdateView(TenantRequiredMixin, View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
        form = SupplierForm(instance=supplier)
        return render(request, 'suppliers/supplier_form.html', {'form': form, 'supplier': supplier, 'title': f'Edit Supplier: {supplier.supplier_name}'})

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            form.save()
            messages.success(request, f"Supplier '{supplier.supplier_name}' updated!")
            return redirect('suppliers:detail', pk=supplier.pk)
        return render(request, 'suppliers/supplier_form.html', {'form': form, 'supplier': supplier, 'title': f'Edit Supplier: {supplier.supplier_name}'})

class SupplierDeleteView(TenantRequiredMixin, View):
    def get(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
        return render(request, 'suppliers/supplier_delete.html', {'supplier': supplier})

    def post(self, request, pk):
        supplier = get_object_or_404(Supplier, pk=pk, business=request.business)
        name = supplier.supplier_name
        supplier.delete()
        messages.success(request, f"Supplier '{name}' removed.")
        return redirect('suppliers:list')

class SupplierPurchaseCreateView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        suppliers = Supplier.objects.filter(business=business)
        products = Product.objects.filter(business=business)
        
        supplier_id = request.GET.get('supplier_id')
        selected_supplier = Supplier.objects.filter(pk=supplier_id, business=business).first() if supplier_id else None

        return render(request, 'suppliers/purchase_form.html', {
            'suppliers': suppliers,
            'products': products,
            'selected_supplier': selected_supplier,
            'today_str': timezone.now().strftime('%Y-%m-%dT%H:%M')
        })

    def post(self, request):
        business = request.business
        supplier_id = request.POST.get('supplier')
        supplier = get_object_or_404(Supplier, pk=supplier_id, business=business)

        purchase_date_str = request.POST.get('purchase_date')
        due_date_str = request.POST.get('due_date')
        parsed_due_date = None
        if due_date_str:
            try:
                parsed_due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                parsed_due_date = None

        manual_total = float(request.POST.get('total_purchase') or 0.0)
        credit_amount_input = float(request.POST.get('credit_amount') or 0.0)
        paid_amount = float(request.POST.get('paid_amount') or 0.0)
        notes = request.POST.get('notes', '').strip()

        # Create Purchase record
        purchase = SupplierPurchase.objects.create(
            business=business,
            supplier=supplier,
            purchase_date=purchase_date_str if purchase_date_str else timezone.now(),
            due_date=parsed_due_date,
            paid_amount=paid_amount,
            notes=notes
        )

        # Process Line Items (Optional)
        product_ids = request.POST.getlist('product_id[]')
        quantities = request.POST.getlist('quantity[]')
        cost_prices = request.POST.getlist('cost_price[]')

        item_totals_sum = 0.0

        for p_id, qty_str, cp_str in zip(product_ids, quantities, cost_prices):
            if not p_id:
                continue
            try:
                prod = Product.objects.get(pk=p_id, business=business)
                qty = int(qty_str or 1)
                cp = float(cp_str or prod.cost_price or 0.0)
                item_total = qty * cp

                SupplierPurchaseItem.objects.create(
                    business=business,
                    purchase=purchase,
                    product=prod,
                    quantity=qty,
                    cost_price=cp,
                    total=item_total
                )

                # Inventory Auto Increment
                prod.stock_quantity += qty
                prod.cost_price = cp  # Update product cost price
                prod.save()

                item_totals_sum += item_total
            except (Product.DoesNotExist, ValueError):
                pass

        if manual_total > 0:
            final_total = manual_total
        elif item_totals_sum > 0:
            final_total = item_totals_sum
        elif credit_amount_input > 0:
            final_total = paid_amount + credit_amount_input
        else:
            final_total = paid_amount

        purchase.total_purchase = final_total
        purchase.credit_amount = credit_amount_input if credit_amount_input > 0 else max(0.0, final_total - paid_amount)
        purchase.update_status()

        messages.success(request, f"Supplier Purchase recorded for ₹{final_total:,.2f}. Outstanding Payable: ₹{purchase.remaining_payable:,.2f}")
        return redirect('suppliers:payable_list')

class SupplierPurchaseUpdateView(TenantRequiredMixin, View):
    def get(self, request, pk):
        business = request.business
        purchase = get_object_or_404(SupplierPurchase, pk=pk, business=business)
        suppliers = Supplier.objects.filter(business=business)
        return render(request, 'suppliers/purchase_edit_form.html', {
            'purchase': purchase,
            'suppliers': suppliers,
            'purchase_date_str': purchase.purchase_date.strftime('%Y-%m-%dT%H:%M') if purchase.purchase_date else '',
            'due_date_str': purchase.due_date.strftime('%Y-%m-%d') if purchase.due_date else ''
        })

    def post(self, request, pk):
        business = request.business
        purchase = get_object_or_404(SupplierPurchase, pk=pk, business=business)

        supplier_id = request.POST.get('supplier')
        if supplier_id:
            purchase.supplier = get_object_or_404(Supplier, pk=supplier_id, business=business)

        purchase_date_str = request.POST.get('purchase_date')
        if purchase_date_str:
            purchase.purchase_date = purchase_date_str

        due_date_str = request.POST.get('due_date')
        if due_date_str:
            try:
                purchase.due_date = datetime.datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                purchase.due_date = None
        else:
            purchase.due_date = None

        tot_p = float(request.POST.get('total_purchase') or 0.0)
        credit_amount_input = float(request.POST.get('credit_amount') or 0.0)
        pd_a = float(request.POST.get('paid_amount') or 0.0)

        if tot_p > 0:
            final_total = tot_p
        elif credit_amount_input > 0:
            final_total = pd_a + credit_amount_input
        else:
            final_total = pd_a

        purchase.total_purchase = final_total
        purchase.paid_amount = pd_a
        purchase.credit_amount = credit_amount_input if credit_amount_input > 0 else max(0.0, final_total - pd_a)
        purchase.notes = request.POST.get('notes', '').strip()
        purchase.update_status()

        messages.success(request, f"Purchase #{purchase.pk} updated! Total: ₹{tot_p:,.2f}, Remaining Payable: ₹{purchase.remaining_payable:,.2f}")
        return redirect('suppliers:payable_list')

class SupplierPurchaseDeleteView(TenantRequiredMixin, View):
    def get(self, request, pk):
        purchase = get_object_or_404(SupplierPurchase, pk=pk, business=request.business)
        return render(request, 'suppliers/purchase_delete.html', {'purchase': purchase})

    def post(self, request, pk):
        purchase = get_object_or_404(SupplierPurchase, pk=pk, business=request.business)
        pk_val = purchase.pk
        purchase.delete()
        messages.success(request, f"Supplier Purchase #{pk_val} deleted.")
        return redirect('suppliers:payable_list')

class SupplierPayableListView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        purchases = SupplierPurchase.objects.filter(business=business)
        suppliers = Supplier.objects.filter(business=business)

        status_filter = request.GET.get('status')
        supplier_filter = request.GET.get('supplier_id')
        
        if status_filter:
            purchases = purchases.filter(status=status_filter)
        if supplier_filter:
            purchases = purchases.filter(supplier_id=supplier_filter)

        today = timezone.now().date()
        this_month_start = today.replace(day=1)

        # Summary Cards
        active_purchases = SupplierPurchase.objects.filter(business=business).exclude(status='Paid')
        total_payable = sum([p.remaining_payable for p in active_purchases])
        
        overdue_purchases = active_purchases.filter(status='Overdue')
        overdue_payable = sum([p.remaining_payable for p in overdue_purchases])

        due_today_purchases = active_purchases.filter(due_date=today)
        due_today = sum([p.remaining_payable for p in due_today_purchases])

        due_soon_purchases = active_purchases.filter(due_date__gt=today, due_date__lte=today + datetime.timedelta(days=7))
        due_soon = sum([p.remaining_payable for p in due_soon_purchases])

        paid_this_month = SupplierPayment.objects.filter(business=business, date__date__gte=this_month_start).aggregate(s=Sum('amount'))['s'] or 0

        return render(request, 'suppliers/supplier_payable_list.html', {
            'purchases': purchases,
            'suppliers': suppliers,
            'status_filter': status_filter,
            'supplier_filter': supplier_filter,
            'total_payable': total_payable,
            'overdue_payable': overdue_payable,
            'due_today': due_today,
            'due_soon': due_soon,
            'paid_this_month': paid_this_month
        })

class SupplierPaymentCreateView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        supplier_id = request.POST.get('supplier_id')
        purchase_id = request.POST.get('purchase_id')
        amount_str = request.POST.get('amount')
        payment_method = request.POST.get('payment_method', 'UPI')
        reference = request.POST.get('reference', '').strip()
        notes = request.POST.get('notes', '').strip()

        supplier = get_object_or_404(Supplier, pk=supplier_id, business=business)
        purchase = SupplierPurchase.objects.filter(pk=purchase_id, business=business).first() if purchase_id else None

        try:
            amt = float(amount_str)
            if amt <= 0:
                raise ValueError("Amount must be greater than zero.")

            pay = SupplierPayment.objects.create(
                business=business,
                supplier=supplier,
                supplier_purchase=purchase,
                amount=amt,
                payment_method=payment_method,
                reference=reference,
                notes=notes
            )
            messages.success(request, f"Supplier Payment of ₹{amt:,.2f} recorded to '{supplier.supplier_name}'.")
        except ValueError as e:
            messages.error(request, f"Failed to record payment: {str(e)}")

        return redirect(request.META.get('HTTP_REFERER', 'suppliers:payable_list'))

def export_suppliers_csv(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
        return HttpResponse("Unauthorized", status=401)
    business = request.user.profile.business

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Supplier Name', 'Phone', 'Business Name', 'Total Purchases', 'Total Paid', 'Outstanding Payable'])

    suppliers = Supplier.objects.filter(business=business)
    for s in suppliers:
        writer.writerow([s.supplier_name, s.phone, s.business_name, s.total_purchases, s.total_paid, s.outstanding_payable])

    return response

def export_purchases_csv(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
        return HttpResponse("Unauthorized", status=401)
    business = request.user.profile.business

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_purchases_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Supplier', 'Purchase Date', 'Total Purchase', 'Paid Amount', 'Remaining Payable', 'Due Date', 'Status'])

    purchases = SupplierPurchase.objects.filter(business=business)
    for p in purchases:
        writer.writerow([p.supplier.supplier_name, p.purchase_date.strftime('%Y-%m-%d'), p.total_purchase, p.paid_amount, p.remaining_payable, p.due_date, p.status])

    return response

def export_payments_csv(request):
    if not request.user.is_authenticated or not hasattr(request.user, 'profile'):
        return HttpResponse("Unauthorized", status=401)
    business = request.user.profile.business

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="supplier_payments_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Supplier', 'Payment Date', 'Amount', 'Payment Method', 'Reference', 'Notes'])

    payments = SupplierPayment.objects.filter(business=business)
    for pay in payments:
        writer.writerow([pay.supplier.supplier_name, pay.date.strftime('%Y-%m-%d %H:%M'), pay.amount, pay.payment_method, pay.reference, pay.notes])

    return response
