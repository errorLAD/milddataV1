from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from apps.inventory.models import Product, ProductCategory, Warehouse, StockMovement, MovementType, ProductType
from apps.core.models import AuditLog

@login_required
def product_list_view(request):
    org = request.organization
    products = Product.objects.filter(organization=org)
    
    filter_type = request.GET.get('filter')
    if filter_type == 'low_stock':
        products = [p for p in products if p.is_low_stock]
    elif filter_type == 'out_of_stock':
        products = products.filter(stock_quantity__lte=0, product_type=ProductType.PHYSICAL)

    physical_count = Product.objects.filter(organization=org, product_type=ProductType.PHYSICAL).count()
    inventory_value = sum(p.stock_quantity * p.purchase_price for p in Product.objects.filter(organization=org, product_type=ProductType.PHYSICAL))
    low_stock_count = len([p for p in Product.objects.filter(organization=org, product_type=ProductType.PHYSICAL) if p.is_low_stock])

    return render(request, 'inventory/product_list.html', {
        'products': products,
        'physical_count': physical_count,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'filter_type': filter_type
    })

@login_required
def product_create_view(request):
    org = request.organization
    if request.method == 'POST':
        p = Product.objects.create(
            organization=org,
            name=request.POST.get('name'),
            sku=request.POST.get('sku'),
            barcode=request.POST.get('barcode'),
            unit=request.POST.get('unit', 'pcs'),
            purchase_price=float(request.POST.get('purchase_price', 0.0)),
            selling_price=float(request.POST.get('selling_price', 0.0)),
            reorder_level=int(request.POST.get('reorder_level', 5)),
            stock_quantity=int(request.POST.get('stock_quantity', 0)),
            product_type=request.POST.get('product_type', ProductType.PHYSICAL)
        )
        # Log initial movement
        if p.stock_quantity > 0:
            StockMovement.objects.create(
                organization=org, product=p, quantity_change=p.stock_quantity,
                movement_type=MovementType.STOCK_IN, reference="Initial Stock", created_by=request.user
            )
        AuditLog.objects.create(
            organization=org, user=request.user, action="Product Created",
            model_name="Product", record_id=str(p.id), details=f"Product {p.name} created."
        )
        return redirect('product_list')
    categories = ProductCategory.objects.filter(organization=org)
    warehouses = Warehouse.objects.filter(organization=org)
    return render(request, 'inventory/product_form.html', {'categories': categories, 'warehouses': warehouses})

@login_required
def product_detail_view(request, prod_id):
    org = request.organization
    product = get_object_or_404(Product, id=prod_id, organization=org)
    movements = StockMovement.objects.filter(product=product)[:15]
    return render(request, 'inventory/product_detail.html', {'product': product, 'movements': movements})

@login_required
def stock_movement_list_view(request):
    org = request.organization
    movements = StockMovement.objects.filter(organization=org)
    return render(request, 'inventory/movement_list.html', {'movements': movements})

@login_required
def stock_adjust_view(request, prod_id):
    org = request.organization
    product = get_object_or_404(Product, id=prod_id, organization=org)
    if request.method == 'POST':
        change = int(request.POST.get('quantity_change', 0))
        m_type = request.POST.get('movement_type', MovementType.ADJUSTMENT)
        notes = request.POST.get('notes', '')
        
        if m_type in [MovementType.STOCK_OUT, MovementType.DAMAGE] and change > 0:
            change = -change
            
        product.stock_quantity += change
        product.save()
        
        StockMovement.objects.create(
            organization=org, product=product, quantity_change=change,
            movement_type=m_type, notes=notes, created_by=request.user
        )
        AuditLog.objects.create(
            organization=org, user=request.user, action="Stock Adjusted",
            model_name="Product", record_id=str(product.id), details=f"{product.name} stock changed by {change} ({m_type})."
        )
        return redirect('product_detail', prod_id=product.id)
    return render(request, 'inventory/stock_adjust_form.html', {'product': product, 'movement_types': MovementType.choices})

@login_required
def barcode_scanner_view(request):
    return render(request, 'inventory/barcode_scanner.html')

@login_required
def barcode_lookup_api(request):
    code = request.GET.get('code', '').strip()
    org = request.organization
    product = Product.objects.filter(organization=org, barcode=code).first()
    if not product:
        product = Product.objects.filter(organization=org, sku=code).first()
    
    if product:
        return JsonResponse({
            'found': True,
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'barcode': product.barcode,
            'price': float(product.selling_price),
            'stock': product.stock_quantity,
            'unit': product.unit,
            'currency': org.currency_symbol
        })
    return JsonResponse({'found': False, 'message': 'Product not found'})
