from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import datetime

from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem, PurchaseBill
from apps.inventory.models import Product, Warehouse, Inventory, StockMovement
from apps.finance.models import Payment
from apps.core.models import AuditLog, Notification

# --- SUPPLIERS ---
@login_required
def supplier_list_view(request):
    org = request.organization
    suppliers = Supplier.objects.filter(organization=org)
    q = request.GET.get('q', '').strip()
    if q:
        suppliers = suppliers.filter(Q(company_name__icontains=q) | Q(contact_person__icontains=q) | Q(email__icontains=q))

    context = {
        'suppliers': suppliers,
        'q': q,
        'total_suppliers': suppliers.count(),
    }
    return render(request, 'purchasing/supplier_list.html', context)

@login_required
def supplier_create_view(request):
    org = request.organization
    if request.method == 'POST':
        company_name = request.POST.get('company_name', '').strip()
        contact_person = request.POST.get('contact_person', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        country = request.POST.get('country', 'United States')
        address = request.POST.get('address', '').strip()
        payment_terms = request.POST.get('payment_terms', 'Net 30')
        tax_id = request.POST.get('tax_id', '').strip()

        if company_name:
            sup = Supplier.objects.create(
                organization=org,
                company_name=company_name,
                contact_person=contact_person,
                email=email,
                phone=phone,
                country=country,
                address=address,
                payment_terms=payment_terms,
                currency=org.currency_code,
                tax_id=tax_id
            )
            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Supplier Created',
                object_type='Supplier',
                object_repr=sup.company_name
            )
            messages.success(request, f"Supplier '{sup.company_name}' created.")
            return redirect('supplier_detail', supplier_id=sup.id)

    return redirect('supplier_list')

@login_required
def supplier_detail_view(request, supplier_id):
    org = request.organization
    supplier = get_object_or_404(Supplier, id=supplier_id, organization=org)

    purchase_orders = PurchaseOrder.objects.filter(supplier=supplier)
    bills = PurchaseBill.objects.filter(supplier=supplier)
    payments = Payment.objects.filter(supplier=supplier, payment_type='PAYABLE')

    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders,
        'bills': bills,
        'payments': payments,
    }
    return render(request, 'purchasing/supplier_detail.html', context)

# --- PURCHASE ORDERS ---
@login_required
def po_list_view(request):
    org = request.organization
    orders = PurchaseOrder.objects.filter(organization=org)

    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    suppliers = Supplier.objects.filter(organization=org)
    warehouses = Warehouse.objects.filter(organization=org)

    context = {
        'orders': orders,
        'suppliers': suppliers,
        'warehouses': warehouses,
        'selected_status': status_filter,
    }
    return render(request, 'purchasing/po_list.html', context)

@login_required
def po_create_view(request):
    org = request.organization
    if request.method == 'POST':
        supplier_id = request.POST.get('supplier_id')
        warehouse_id = request.POST.get('warehouse_id')
        order_date_str = request.POST.get('order_date') or datetime.date.today().strftime('%Y-%m-%d')
        expected_delivery_str = request.POST.get('expected_delivery')
        notes = request.POST.get('notes', '').strip()

        supplier = get_object_or_404(Supplier, id=supplier_id, organization=org)
        warehouse = get_object_or_404(Warehouse, id=warehouse_id, organization=org)

        # Generate PO number
        last_po = PurchaseOrder.objects.filter(organization=org).order_by('-id').first()
        seq = (last_po.id + 1) if last_po else 1001
        po_number = f"{org.po_prefix}{seq}"

        with transaction.atomic():
            po = PurchaseOrder.objects.create(
                organization=org,
                supplier=supplier,
                po_number=po_number,
                order_date=order_date_str,
                expected_delivery=expected_delivery_str if expected_delivery_str else None,
                warehouse=warehouse,
                status='DRAFT',
                payment_terms=supplier.payment_terms,
                notes=notes,
                created_by=request.user
            )

            # Process line items from POST
            product_ids = request.POST.getlist('product_id[]')
            quantities = request.POST.getlist('quantity[]')
            unit_costs = request.POST.getlist('unit_cost[]')

            for pid, qty_str, cost_str in zip(product_ids, quantities, unit_costs):
                if pid and qty_str:
                    prod = Product.objects.filter(id=pid, organization=org).first()
                    if prod:
                        qty = int(qty_str or '1')
                        cost = Decimal(cost_str or '0.00')
                        PurchaseOrderItem.objects.create(
                            purchase_order=po,
                            product=prod,
                            quantity=qty,
                            unit_cost=cost,
                            tax_rate=org.tax_rate
                        )

            po.recalculate_totals()

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Purchase Order Created',
                object_type='PurchaseOrder',
                object_repr=po.po_number
            )

        messages.success(request, f"Purchase Order {po.po_number} created.")
        return redirect('po_detail', po_id=po.id)

    suppliers = Supplier.objects.filter(organization=org)
    warehouses = Warehouse.objects.filter(organization=org)
    products = Product.objects.filter(organization=org, is_archived=False)

    return render(request, 'purchasing/po_form.html', {
        'suppliers': suppliers,
        'warehouses': warehouses,
        'products': products,
    })

@login_required
def po_detail_view(request, po_id):
    org = request.organization
    po = get_object_or_404(PurchaseOrder, id=po_id, organization=org)
    goods_receipts = GoodsReceipt.objects.filter(purchase_order=po)
    bills = PurchaseBill.objects.filter(purchase_order=po)

    context = {
        'po': po,
        'goods_receipts': goods_receipts,
        'bills': bills,
    }
    return render(request, 'purchasing/po_detail.html', context)

@login_required
def po_status_update_view(request, po_id):
    org = request.organization
    po = get_object_or_404(PurchaseOrder, id=po_id, organization=org)
    new_status = request.POST.get('status')

    if new_status in dict(PurchaseOrder.STATUS_CHOICES):
        po.status = new_status
        po.save()

        # If PO is Approved, auto-create a PurchaseBill in OPEN status
        if new_status == 'APPROVED' and not po.bills.exists():
            bill_num = f"{org.bill_prefix}{po.po_number.replace(org.po_prefix, '')}"
            due_dt = datetime.date.today() + datetime.timedelta(days=30)
            PurchaseBill.objects.create(
                organization=org,
                supplier=po.supplier,
                purchase_order=po,
                bill_number=bill_num,
                bill_date=datetime.date.today(),
                due_date=due_dt,
                status='OPEN',
                total_amount=po.total_amount,
                notes=f'Auto-created upon PO {po.po_number} approval'
            )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"PO Status Changed to {new_status}",
            object_type='PurchaseOrder',
            object_repr=po.po_number
        )

        messages.success(request, f"Purchase Order {po.po_number} status updated to {po.get_status_display()}.")

    return redirect('po_detail', po_id=po.id)

# --- GOODS RECEIVING WORKFLOW ---
@login_required
def goods_receipt_create_view(request, po_id):
    org = request.organization
    po = get_object_or_404(PurchaseOrder, id=po_id, organization=org)

    if request.method == 'POST':
        receipt_num = f"GRN-{po.po_number.replace(org.po_prefix, '')}-{GoodsReceipt.objects.filter(purchase_order=po).count() + 1}"
        receipt_date = request.POST.get('receipt_date') or datetime.date.today().strftime('%Y-%m-%d')
        notes = request.POST.get('notes', '').strip()

        item_ids = request.POST.getlist('item_id[]')
        received_qtys = request.POST.getlist('quantity_received[]')

        with transaction.atomic():
            receipt = GoodsReceipt.objects.create(
                organization=org,
                purchase_order=po,
                receipt_number=receipt_num,
                receipt_date=receipt_date,
                warehouse=po.warehouse,
                received_by=request.user,
                notes=notes
            )

            all_completed = True
            any_received = False

            for item_id_str, recv_str in zip(item_ids, received_qtys):
                if item_id_str and recv_str:
                    qty_recv = int(recv_str or '0')
                    if qty_recv > 0:
                        po_item = PurchaseOrderItem.objects.get(id=item_id_str, purchase_order=po)
                        po_item.received_quantity += qty_recv
                        po_item.save()

                        GoodsReceiptItem.objects.create(
                            goods_receipt=receipt,
                            po_item=po_item,
                            product=po_item.product,
                            quantity_received=qty_recv
                        )

                        # Inventory increase automatically!
                        if po_item.product.product_type == 'PHYSICAL':
                            inv, _ = Inventory.objects.get_or_create(organization=org, product=po_item.product, warehouse=po.warehouse, defaults={'quantity': 0})
                            before_q = inv.quantity
                            inv.quantity += qty_recv
                            inv.save()

                            StockMovement.objects.create(
                                organization=org,
                                product=po_item.product,
                                warehouse=po.warehouse,
                                movement_type='PURCHASE',
                                quantity=qty_recv,
                                quantity_before=before_q,
                                quantity_after=inv.quantity,
                                reference=po.po_number,
                                user=request.user,
                                notes=f"Goods Received on {receipt_num}"
                            )

                        any_received = True

            # Check if all items in PO are fully received
            for item in po.items.all():
                if item.received_quantity < item.quantity:
                    all_completed = False
                    break

            if all_completed:
                po.status = 'COMPLETED'
            elif any_received:
                po.status = 'PARTIALLY_RECEIVED'
            po.save()

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Goods Received',
                object_type='GoodsReceipt',
                object_repr=receipt.receipt_number
            )

        messages.success(request, f"Goods Receipt {receipt_num} processed. Inventory updated.")
        return redirect('po_detail', po_id=po.id)

    return render(request, 'purchasing/goods_receipt.html', {'po': po})
