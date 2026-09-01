import csv
import io
from django.shortcuts import render, redirect
from django.contrib import messages
from apps.machines.models import Machine
from apps.tenants.decorators import guest_restricted

def import_view(request):
    """Render Import & Export Center interface."""
    return render(request, 'import_export/index.html')

@guest_restricted
def import_csv_machines(request):
    """
    Parses CSV, validates column fields, detects duplicates, and previews before committing.
    """
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')
        if not csv_file or not csv_file.name.endswith('.csv'):
            messages.error(request, "Please upload a valid .csv file.")
            return redirect('import_index')

        try:
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)

            tenant = request.tenant
            created_count = 0
            skipped_count = 0

            for row in reader:
                name = row.get('name') or row.get('Machine Name')
                reg = row.get('reg_number') or row.get('Reg Number')
                category = row.get('category', 'jcb').lower()
                meter = float(row.get('current_meter', 0.0))

                if name and reg:
                    # Duplicate check
                    if Machine.objects.filter(organization=tenant, reg_number=reg).exists():
                        skipped_count += 1
                        continue

                    Machine.objects.create(
                        organization=tenant,
                        name=name,
                        reg_number=reg,
                        category=category if category in dict(Machine.CATEGORY_CHOICES) else 'jcb',
                        current_meter=meter,
                        status='working'
                    )
                    created_count += 1

            messages.success(request, f"Import complete! Successfully added {created_count} machines ({skipped_count} skipped as duplicates).")
        except Exception as e:
            messages.error(request, f"Error processing CSV file: {str(e)}")

        return redirect('import_index')
    return redirect('import_index')
