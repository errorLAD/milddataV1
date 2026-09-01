from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from decimal import Decimal
import datetime

from apps.inventory.models import Product, ProductCategory, ProductUnit, Warehouse, Inventory, StockMovement
from apps.purchasing.models import PurchaseOrderItem
from apps.sales.models import InvoiceItem
from apps.core.models import AuditLog

@login_required
def product_list_view(request):
    org = request.organization
    products = Product.objects.filter(organization=org, is_archived=False)

    q = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('type', '')

    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(barcode__icontains=q))

    if category_id:
        products = products.filter(category_id=category_id)

    if type_filter:
        products = products.filter(product_type=type_filter)

    categories = ProductCategory.objects.filter(organization=org)
    units = ProductUnit.objects.filter(organization=org)
    warehouses = Warehouse.objects.filter(organization=org)

    total_products = products.count()
    low_stock_count = 0
    out_of_stock_count = 0
    total_val = Decimal('0.00')

    product_data = []
    for p in products:
        val = p.inventory_value
        total_val += val
        st = p.status
        if st == 'Low Stock':
            low_stock_count += 1
        elif st == 'Out of Stock':
            out_of_stock_count += 1

        if status_filter and st != status_filter:
            continue

        product_data.append(p)

    context = {
        'products': product_data,
        'categories': categories,
        'units': units,
        'warehouses': warehouses,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_val': total_val,
        'q': q,
        'selected_category': category_id,
        'selected_status': status_filter,
        'selected_type': type_filter,
    }
    return render(request, 'inventory/product_list.html', context)

@login_required
def product_create_view(request):
    org = request.organization
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip()
        barcode = request.POST.get('barcode', '').strip()
        product_type = request.POST.get('product_type', 'PHYSICAL')
        category_id = request.POST.get('category_id')
        unit_id = request.POST.get('unit_id')
        brand = request.POST.get('brand', '').strip()
        description = request.POST.get('description', '').strip()
        purchase_price = Decimal(request.POST.get('purchase_price', '0.00') or '0.00')
        selling_price = Decimal(request.POST.get('selling_price', '0.00') or '0.00')
        reorder_level = int(request.POST.get('reorder_level', '10') or '10')
        opening_stock = int(request.POST.get('opening_stock', '0') or '0')
        warehouse_id = request.POST.get('warehouse_id')

        if not name or not sku:
            messages.error(request, "Product Name and SKU are required.")
            return redirect('product_list')

        if Product.objects.filter(organization=org, sku=sku).exists():
            messages.error(request, f"Product SKU '{sku}' already exists.")
            return redirect('product_list')

        with transaction.atomic():
            cat = ProductCategory.objects.filter(id=category_id, organization=org).first() if category_id else None
            unit = ProductUnit.objects.filter(id=unit_id, organization=org).first() if unit_id else None

            p = Product.objects.create(
                organization=org,
                name=name,
                sku=sku,
                barcode=barcode,
                product_type=product_type,
                category=cat,
                unit=unit,
                brand=brand,
                description=description,
                purchase_price=purchase_price,
                selling_price=selling_price,
                reorder_level=reorder_level,
                opening_stock=opening_stock
            )

            # Assign opening stock to warehouse
            if product_type == 'PHYSICAL' and opening_stock > 0:
                wh = Warehouse.objects.filter(id=warehouse_id, organization=org).first() or Warehouse.objects.filter(organization=org, is_primary=True).first()
                if not wh:
                    wh = Warehouse.objects.create(organization=org, name='Main Warehouse', code='WH-MAIN', is_primary=True)

                Inventory.objects.create(
                    organization=org,
                    product=p,
                    warehouse=wh,
                    quantity=opening_stock
                )
                StockMovement.objects.create(
                    organization=org,
                    product=p,
                    warehouse=wh,
                    movement_type='ADJUSTMENT',
                    quantity=opening_stock,
                    quantity_before=0,
                    quantity_after=opening_stock,
                    reference='OPENING_STOCK',
                    user=request.user,
                    notes='Opening stock on product creation'
                )

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Product Created',
                object_type='Product',
                object_repr=f"{p.name} ({p.sku})"
            )

        messages.success(request, f"Product '{p.name}' created successfully.")
        return redirect('product_detail', product_id=p.id)

    return redirect('product_list')

@login_required
def product_detail_view(request, product_id):
    org = request.organization
    product = get_object_or_404(Product, id=product_id, organization=org)

    # Warehouse Inventory Levels
    inventory_levels = Inventory.objects.filter(product=product)
    warehouses = Warehouse.objects.filter(organization=org)

    # Purchases History
    po_items = PurchaseOrderItem.objects.filter(product=product).select_related('purchase_order', 'purchase_order__supplier')[:10]

    # Sales History
    invoice_items = InvoiceItem.objects.filter(product=product).select_related('invoice', 'invoice__customer')[:10]

    # Stock Movement History Timeline
    movements = StockMovement.objects.filter(product=product)[:15]

    categories = ProductCategory.objects.filter(organization=org)
    units = ProductUnit.objects.filter(organization=org)

    context = {
        'product': product,
        'inventory_levels': inventory_levels,
        'warehouses': warehouses,
        'po_items': po_items,
        'invoice_items': invoice_items,
        'movements': movements,
        'categories': categories,
        'units': units,
    }
    return render(request, 'inventory/product_detail.html', context)

@login_required
def product_edit_view(request, product_id):
    org = request.organization
    product = get_object_or_404(Product, id=product_id, organization=org)

    if request.method == 'POST':
        product.name = request.POST.get('name', product.name).strip()
        product.barcode = request.POST.get('barcode', product.barcode).strip()
        product.brand = request.POST.get('brand', product.brand).strip()
        product.description = request.POST.get('description', product.description).strip()
        product.purchase_price = Decimal(request.POST.get('purchase_price', product.purchase_price))
        product.selling_price = Decimal(request.POST.get('selling_price', product.selling_price))
        product.reorder_level = int(request.POST.get('reorder_level', product.reorder_level))

        category_id = request.POST.get('category_id')
        unit_id = request.POST.get('unit_id')
        product.category = ProductCategory.objects.filter(id=category_id, organization=org).first() if category_id else None
        product.unit = ProductUnit.objects.filter(id=unit_id, organization=org).first() if unit_id else None
        product.save()

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action='Product Edited',
            object_type='Product',
            object_repr=f"{product.name} ({product.sku})"
        )

        messages.success(request, f"Product '{product.name}' updated successfully.")
        return redirect('product_detail', product_id=product.id)

    return redirect('product_detail', product_id=product.id)

@login_required
def product_archive_view(request, product_id):
    org = request.organization
    product = get_object_or_404(Product, id=product_id, organization=org)
    product.is_archived = True
    product.save()
    messages.info(request, f"Product '{product.name}' archived.")
    return redirect('product_list')

@login_required
def warehouse_list_view(request):
    org = request.organization
    warehouses = Warehouse.objects.filter(organization=org)
    products = Product.objects.filter(organization=org, is_archived=False)

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        is_primary = request.POST.get('is_primary') == 'on'

        if name and code:
            if is_primary:
                Warehouse.objects.filter(organization=org).update(is_primary=False)
            wh = Warehouse.objects.create(
                organization=org,
                name=name,
                code=code,
                address=address,
                is_primary=is_primary
            )
            messages.success(request, f"Warehouse '{wh.name}' created.")
            return redirect('warehouse_list')

    wh_data = []
    for wh in warehouses:
        levels = Inventory.objects.filter(warehouse=wh)
        stock_units = sum(item.quantity for item in levels)
        item_types = levels.count()
        val = sum(Decimal(item.quantity) * item.product.purchase_price for item in levels)
        wh_data.append({
            'wh': wh,
            'stock_units': stock_units,
            'item_types': item_types,
            'val': val
        })

    return render(request, 'inventory/warehouse_list.html', {'warehouses': wh_data, 'products': products})

@login_required
def stock_transfer_view(request):
    org = request.organization
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        source_wh_id = request.POST.get('source_warehouse_id')
        target_wh_id = request.POST.get('target_warehouse_id')
        qty = int(request.POST.get('quantity', '0') or '0')
        notes = request.POST.get('notes', '').strip()

        if source_wh_id == target_wh_id:
            messages.error(request, "Source and destination warehouses must be different.")
            return redirect('stock_movements')

        product = get_object_or_404(Product, id=product_id, organization=org)
        src_wh = get_object_or_404(Warehouse, id=source_wh_id, organization=org)
        tgt_wh = get_object_or_404(Warehouse, id=target_wh_id, organization=org)

        src_inv, _ = Inventory.objects.get_or_create(organization=org, product=product, warehouse=src_wh, defaults={'quantity': 0})
        tgt_inv, _ = Inventory.objects.get_or_create(organization=org, product=product, warehouse=tgt_wh, defaults={'quantity': 0})

        if src_inv.available_quantity < qty:
            messages.error(request, f"Insufficient available stock in {src_wh.name}. Available: {src_inv.available_quantity}.")
            return redirect('stock_movements')

        with transaction.atomic():
            # Deduct from source
            before_src = src_inv.quantity
            src_inv.quantity -= qty
            src_inv.save()

            StockMovement.objects.create(
                organization=org,
                product=product,
                warehouse=src_wh,
                movement_type='TRANSFER',
                quantity=-qty,
                quantity_before=before_src,
                quantity_after=src_inv.quantity,
                reference=f"Transfer to {tgt_wh.code}",
                user=request.user,
                notes=notes
            )

            # Add to target
            before_tgt = tgt_inv.quantity
            tgt_inv.quantity += qty
            tgt_inv.save()

            StockMovement.objects.create(
                organization=org,
                product=product,
                warehouse=tgt_wh,
                movement_type='TRANSFER',
                quantity=qty,
                quantity_before=before_tgt,
                quantity_after=tgt_inv.quantity,
                reference=f"Transfer from {src_wh.code}",
                user=request.user,
                notes=notes
            )

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Stock Transferred',
                object_type='Inventory',
                object_repr=f"{product.name} ({qty} units {src_wh.code} -> {tgt_wh.code})"
            )

        messages.success(request, f"Transferred {qty} units of '{product.name}' from {src_wh.name} to {tgt_wh.name}.")
        return redirect('stock_movements')

    return redirect('stock_movements')

@login_required
def stock_adjustment_view(request):
    org = request.organization
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        warehouse_id = request.POST.get('warehouse_id')
        movement_type = request.POST.get('movement_type', 'ADJUSTMENT')
        quantity_change = int(request.POST.get('quantity_change', '0') or '0')
        notes = request.POST.get('notes', '').strip()

        product = get_object_or_404(Product, id=product_id, organization=org)
        wh = get_object_or_404(Warehouse, id=warehouse_id, organization=org)

        inv, _ = Inventory.objects.get_or_create(organization=org, product=product, warehouse=wh, defaults={'quantity': 0})

        with transaction.atomic():
            before_q = inv.quantity
            inv.quantity = max(0, inv.quantity + quantity_change)
            inv.save()

            StockMovement.objects.create(
                organization=org,
                product=product,
                warehouse=wh,
                movement_type=movement_type,
                quantity=quantity_change,
                quantity_before=before_q,
                quantity_after=inv.quantity,
                reference='ADJUSTMENT',
                user=request.user,
                notes=notes
            )

            AuditLog.objects.create(
                organization=org,
                user=request.user,
                action='Stock Adjusted',
                object_type='Inventory',
                object_repr=f"{product.name} @ {wh.code} ({quantity_change:+d} units)"
            )

        messages.success(request, f"Adjusted stock for '{product.name}' at {wh.name} by {quantity_change:+d} units.")
        return redirect('stock_movements')

    return redirect('stock_movements')

@login_required
def stock_movements_view(request):
    org = request.organization
    movements = StockMovement.objects.filter(organization=org)

    product_id = request.GET.get('product')
    warehouse_id = request.GET.get('warehouse')
    movement_type = request.GET.get('type')

    if product_id:
        movements = movements.filter(product_id=product_id)
    if warehouse_id:
        movements = movements.filter(warehouse_id=warehouse_id)
    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    products = Product.objects.filter(organization=org, is_archived=False)
    warehouses = Warehouse.objects.filter(organization=org)

    context = {
        'movements': movements[:100],
        'products': products,
        'warehouses': warehouses,
        'selected_product': product_id,
        'selected_warehouse': warehouse_id,
        'selected_type': movement_type,
    }
    return render(request, 'inventory/stock_movements.html', context)
