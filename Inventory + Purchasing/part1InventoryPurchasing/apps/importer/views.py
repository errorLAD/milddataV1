from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from decimal import Decimal
import csv
import io

from apps.inventory.models import Product, ProductCategory, ProductUnit, Warehouse, Inventory, StockMovement
from apps.sales.models import Customer
from apps.purchasing.models import Supplier
from apps.core.models import AuditLog

@login_required
def import_csv_view(request):
    org = request.organization
    entity_type = request.POST.get('entity_type', 'products') if request.method == 'POST' else request.GET.get('entity_type', 'products')

    preview_rows = []
    has_errors = False
    valid_count = 0
    error_count = 0

    if request.method == 'POST' and 'csv_file' in request.FILES:
        csv_file = request.FILES['csv_file']
        decoded_file = csv_file.read().decode('utf-8-sig', errors='replace')
        io_string = io.StringIO(decoded_file)
        reader = csv.DictReader(io_string)

        action = request.POST.get('action', 'preview')

        if action == 'confirm':
            # Execute actual import from session data or re-parse
            io_string.seek(0)
            reader = csv.DictReader(io_string)
            imported_count = 0

            with transaction.atomic():
                if entity_type == 'products':
                    primary_wh = Warehouse.objects.filter(organization=org, is_primary=True).first() or Warehouse.objects.filter(organization=org).first()
                    for row in reader:
                        sku = row.get('SKU', '').strip()
                        name = row.get('Name', '').strip()
                        if sku and name and not Product.objects.filter(organization=org, sku=sku).exists():
                            cost = Decimal(row.get('Purchase Price', '0.00') or '0.00')
                            price = Decimal(row.get('Selling Price', '0.00') or '0.00')
                            reorder = int(row.get('Reorder Level', '10') or '10')
                            stock = int(row.get('Opening Stock', '0') or '0')

                            p = Product.objects.create(
                                organization=org,
                                name=name,
                                sku=sku,
                                barcode=row.get('Barcode', '').strip(),
                                brand=row.get('Brand', '').strip(),
                                purchase_price=cost,
                                selling_price=price,
                                reorder_level=reorder,
                                opening_stock=stock
                            )
                            if stock > 0 and primary_wh:
                                Inventory.objects.create(organization=org, product=p, warehouse=primary_wh, quantity=stock)
                                StockMovement.objects.create(
                                    organization=org, product=p, warehouse=primary_wh,
                                    movement_type='ADJUSTMENT', quantity=stock,
                                    quantity_before=0, quantity_after=stock,
                                    reference='CSV_IMPORT', user=request.user
                                )
                            imported_count += 1

                elif entity_type == 'customers':
                    for row in reader:
                        company = row.get('Company Name', '').strip()
                        if company:
                            Customer.objects.create(
                                organization=org,
                                company_name=company,
                                contact_person=row.get('Contact Person', '').strip(),
                                email=row.get('Email', '').strip(),
                                phone=row.get('Phone', '').strip(),
                                country=row.get('Country', 'United States').strip()
                            )
                            imported_count += 1

                elif entity_type == 'suppliers':
                    for row in reader:
                        company = row.get('Company Name', '').strip()
                        if company:
                            Supplier.objects.create(
                                organization=org,
                                company_name=company,
                                contact_person=row.get('Contact Person', '').strip(),
                                email=row.get('Email', '').strip(),
                                phone=row.get('Phone', '').strip(),
                                country=row.get('Country', 'United States').strip()
                            )
                            imported_count += 1

                AuditLog.objects.create(
                    organization=org,
                    user=request.user,
                    action=f"CSV Import ({entity_type.title()})",
                    object_type=entity_type.title(),
                    object_repr=f"Imported {imported_count} records"
                )

            messages.success(request, f"Successfully imported {imported_count} {entity_type}.")
            return redirect('import_csv')

        else:
            # Preview Validation Logic
            row_idx = 1
            for row in reader:
                row_idx += 1
                row_errors = []

                if entity_type == 'products':
                    name = row.get('Name', '').strip()
                    sku = row.get('SKU', '').strip()
                    if not name:
                        row_errors.append("Missing product Name")
                    if not sku:
                        row_errors.append("Missing SKU")
                    elif Product.objects.filter(organization=org, sku=sku).exists():
                        row_errors.append(f"Duplicate SKU '{sku}' exists in system")

                elif entity_type == 'customers' or entity_type == 'suppliers':
                    company = row.get('Company Name', '').strip()
                    if not company:
                        row_errors.append("Missing Company Name")

                is_valid = len(row_errors) == 0
                if is_valid:
                    valid_count += 1
                else:
                    error_count += 1
                    has_errors = True

                preview_rows.append({
                    'index': row_idx,
                    'data': row,
                    'is_valid': is_valid,
                    'errors': ", ".join(row_errors)
                })

    context = {
        'entity_type': entity_type,
        'preview_rows': preview_rows,
        'has_errors': has_errors,
        'valid_count': valid_count,
        'error_count': error_count,
    }
    return render(request, 'importer/import_csv.html', context)

@login_required
def download_template_csv(request):
    entity_type = request.GET.get('type', 'products')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="stockflow_{entity_type}_template.csv"'
    writer = csv.writer(response)

    if entity_type == 'products':
        writer.writerow(['Name', 'SKU', 'Barcode', 'Brand', 'Purchase Price', 'Selling Price', 'Reorder Level', 'Opening Stock'])
        writer.writerow(['Wireless Keyboard K-10', 'KB-1001', '8801920192', 'LogiTech', '25.00', '45.00', '10', '50'])
    elif entity_type == 'customers':
        writer.writerow(['Company Name', 'Contact Person', 'Email', 'Phone', 'Country'])
        writer.writerow(['Acme Tech Solutions', 'John Doe', 'john@acme.com', '+1 555 0199', 'United States'])
    elif entity_type == 'suppliers':
        writer.writerow(['Company Name', 'Contact Person', 'Email', 'Phone', 'Country'])
        writer.writerow(['Global Distro Corp', 'Jane Smith', 'jane@distro.com', '+44 20 7123 9999', 'United Kingdom'])

    return response
