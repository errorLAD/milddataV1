from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt, GoodsReceiptItem, POStatus
from apps.inventory.models import Product, StockMovement, MovementType
from apps.core.models import AuditLog, Notification, NotificationType

@login_required
def supplier_list_view(request):
    org = request.organization
    suppliers = Supplier.objects.filter(organization=org)
    return render(request, 'purchasing/supplier_list.html', {'suppliers': suppliers})

@login_required
def supplier_create_view(request):
    org = request.organization
    if request.method == 'POST':
        s = Supplier.objects.create(
            organization=org,
            company_name=request.POST.get('company_name'),
            contact_person=request.POST.get('contact_person'),
            email=request.POST.get('email'),
            phone=request.POST.get('phone'),
            country=request.POST.get('country', org.country),
            payment_terms=request.POST.get('payment_terms', 'Net 30')
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Supplier Created", model_name="Supplier", record_id=str(s.id), details=f"Supplier {s.company_name} created.")
        return redirect('supplier_list')
    return render(request, 'purchasing/supplier_form.html')

@login_required
def supplier_detail_view(request, supp_id):
    org = request.organization
    supplier = get_object_or_404(Supplier, id=supp_id, organization=org)
    pos = PurchaseOrder.objects.filter(supplier=supplier)
    return render(request, 'purchasing/supplier_detail.html', {'supplier': supplier, 'pos': pos})

@login_required
def po_list_view(request):
    org = request.organization
    orders = PurchaseOrder.objects.filter(organization=org)
    return render(request, 'purchasing/po_list.html', {'orders': orders})

@login_required
def po_create_view(request):
    org = request.organization
    if request.method == 'POST':
        supp_id = request.POST.get('supplier_id')
        supplier = get_object_or_404(Supplier, id=supp_id, organization=org)
        po_num = f"{org.po_prefix}{PurchaseOrder.objects.filter(organization=org).count() + 1001}"
        
        po = PurchaseOrder.objects.create(
            organization=org,
            po_number=po_num,
            supplier=supplier,
            date=request.POST.get('date') or timezone.now().date(),
            expected_delivery=request.POST.get('expected_delivery') or None,
            status=POStatus.DRAFT
        )
        
        # Add line items
        prod_ids = request.POST.getlist('product_id')
        quantities = request.POST.getlist('quantity')
        unit_costs = request.POST.getlist('unit_cost')
        
        total = 0.0
        for i in range(len(prod_ids)):
            if prod_ids[i]:
                prod = Product.objects.get(id=prod_ids[i], organization=org)
                qty = int(quantities[i])
                cost = float(unit_costs[i])
                line = qty * cost
                total += line
                PurchaseOrderItem.objects.create(
                    purchase_order=po, product=prod, quantity=qty, unit_cost=cost, line_total=line
                )
        po.total_amount = total
        po.save()
        
        AuditLog.objects.create(organization=org, user=request.user, action="PO Created", model_name="PurchaseOrder", record_id=str(po.id), details=f"PO {po.po_number} created.")
        return redirect('po_detail', po_id=po.id)

    suppliers = Supplier.objects.filter(organization=org)
    products = Product.objects.filter(organization=org)
    low_stock_products = [p for p in products if p.is_low_stock] if request.GET.get('filter') == 'low_stock' else []
    return render(request, 'purchasing/po_form.html', {'suppliers': suppliers, 'products': products, 'low_stock_products': low_stock_products})

@login_required
def po_detail_view(request, po_id):
    org = request.organization
    po = get_object_or_404(PurchaseOrder, id=po_id, organization=org)
    items = po.items.all()
    receipts = po.receipts.all()
    return render(request, 'purchasing/po_detail.html', {'po': po, 'items': items, 'receipts': receipts})

@login_required
def receive_goods_view(request, po_id):
    org = request.organization
    po = get_object_or_404(PurchaseOrder, id=po_id, organization=org)
    
    if request.method == 'POST':
        receipt_num = f"GR-{GoodsReceipt.objects.filter(organization=org).count() + 1001}"
        gr = GoodsReceipt.objects.create(
            organization=org, purchase_order=po, receipt_number=receipt_num, received_date=timezone.now().date()
        )
        
        all_completed = True
        for item in po.items.all():
            recv_qty = int(request.POST.get(f'receive_{item.id}', 0))
            if recv_qty > 0:
                item.received_quantity += recv_qty
                item.save()
                
                GoodsReceiptItem.objects.create(goods_receipt=gr, product=item.product, quantity_received=recv_qty)
                
                # Automatically increase product stock!
                item.product.stock_quantity += recv_qty
                item.product.save()
                
                StockMovement.objects.create(
                    organization=org, product=item.product, quantity_change=recv_qty,
                    movement_type=MovementType.STOCK_IN, reference=f"GR: {receipt_num} ({po.po_number})", created_by=request.user
                )

            if item.received_quantity < item.quantity:
                all_completed = False

        po.status = POStatus.COMPLETED if all_completed else POStatus.PARTIAL
        po.save()

        Notification.objects.create(
            organization=org, title="Goods Received", message=f"Goods received for {po.po_number}.",
            notification_type=NotificationType.PO_RECEIVED, link=f"/purchasing/orders/{po.id}/"
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Goods Received", model_name="GoodsReceipt", record_id=str(gr.id), details=f"Received goods for PO {po.po_number}.")
        return redirect('po_detail', po_id=po.id)

    return render(request, 'purchasing/receive_goods_form.html', {'po': po})
