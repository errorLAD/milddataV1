from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Q

from apps.machines.models import Machine
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.documents.models import MachineDocument
from apps.finance.models import RevenueLog, ExpenseLog

def global_search_api(request):
    """
    Permission-aware Global Search API.
    Strictly scoped to request.tenant.
    """
    tenant = getattr(request, 'tenant', None)
    query = request.GET.get('q', '').strip()

    if not tenant or not query or len(query) < 2:
        return JsonResponse({'results': []})

    results = []

    # 1. Search Heavy Equipment
    machines = Machine.objects.filter(
        organization=tenant
    ).filter(
        Q(name__icontains=query) | Q(reg_number__icontains=query) | Q(make_model__icontains=query)
    )[:5]

    for m in machines:
        results.append({
            'category': 'Equipment',
            'title': m.name,
            'subtitle': f"Reg: {m.reg_number} • {m.get_category_display()} ({m.current_meter} {m.unit_label})",
            'url': f"/machines/{m.pk}/",
            'badge': m.status.upper()
        })

    # 2. Search Compliance Documents
    documents = MachineDocument.objects.filter(
        organization=tenant
    ).filter(
        Q(title__icontains=query) | Q(doc_number__icontains=query)
    )[:4]

    for d in documents:
        results.append({
            'category': 'Document',
            'title': d.title,
            'subtitle': f"Doc #: {d.doc_number} • Exp: {d.expiry_date}",
            'url': '/documents/',
            'badge': d.doc_type.upper()
        })

    # 3. Search Service & Repair Records
    maint_records = MaintenanceLog.objects.filter(
        organization=tenant
    ).filter(
        Q(parts_replaced__icontains=query) | Q(vendor_mechanic__icontains=query) | Q(machine__name__icontains=query)
    )[:4]

    for ml in maint_records:
        cost_val = float(ml.cost) if ml.cost else 0.0
        results.append({
            'category': 'Maintenance',
            'title': f"{ml.machine.name} - {ml.get_service_type_display()}",
            'subtitle': f"Date: {ml.date} • Cost: ₹{cost_val:,.2f} • Vendor: {ml.vendor_mechanic or 'In-House'}",
            'url': '/maintenance/',
            'badge': 'SERVICE'
        })

    # 4. Search Financial Invoices
    revenues = RevenueLog.objects.filter(
        organization=tenant
    ).filter(
        Q(client_name__icontains=query) | Q(machine__name__icontains=query)
    )[:4]

    for r in revenues:
        amt_val = float(r.amount) if r.amount else 0.0
        results.append({
            'category': 'Invoice',
            'title': f"₹{amt_val:,.2f} - {r.client_name}",
            'subtitle': f"Machine: {r.machine.name} • Date: {r.date}",
            'url': '/finance/profit-loss/',
            'badge': 'REVENUE'
        })

    return JsonResponse({'results': results})
