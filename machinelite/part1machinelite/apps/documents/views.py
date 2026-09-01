from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from datetime import date, timedelta

from .models import MachineDocument
from .utils import validate_uploaded_file, generate_safe_filename
from apps.machines.models import Machine
from apps.operators.models import Operator
from apps.tenants.models import AuditLog
from apps.tenants.decorators import guest_restricted

def document_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    documents = MachineDocument.objects.filter(organization=tenant)
    machines = Machine.objects.filter(organization=tenant)
    operators = Operator.objects.filter(organization=tenant)

    # Status filter
    doc_filter = request.GET.get('status', '')
    doc_type = request.GET.get('type', '')

    today = date.today()
    if doc_filter == 'expired':
        documents = documents.filter(expiry_date__lt=today)
    elif doc_filter == 'warning':
        documents = documents.filter(expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30))
    elif doc_filter == 'valid':
        documents = documents.filter(expiry_date__gt=today + timedelta(days=30))

    if doc_type:
        documents = documents.filter(doc_type=doc_type)

    expired_count = MachineDocument.objects.filter(organization=tenant, expiry_date__lt=today).count()
    warning_count = MachineDocument.objects.filter(organization=tenant, expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)).count()
    valid_count = MachineDocument.objects.filter(organization=tenant, expiry_date__gt=today + timedelta(days=30)).count()

    context = {
        'documents': documents,
        'machines': machines,
        'operators': operators,
        'doc_filter': doc_filter,
        'doc_type': doc_type,
        'expired_count': expired_count,
        'warning_count': warning_count,
        'valid_count': valid_count,
        'total_count': expired_count + warning_count + valid_count,
    }
    return render(request, 'documents/list.html', context)

@guest_restricted
def add_document(request):
    if request.method == 'POST':
        tenant = request.tenant
        title = request.POST.get('title', '').strip()
        doc_type = request.POST.get('doc_type', 'insurance')
        doc_number = request.POST.get('doc_number', '').strip()
        expiry_date = request.POST.get('expiry_date')
        machine_id = request.POST.get('machine')
        operator_id = request.POST.get('operator')
        notes = request.POST.get('notes', '').strip()

        # Secure file validation
        file_obj = request.FILES.get('document_file')
        if file_obj:
            try:
                validate_uploaded_file(file_obj)
            except ValidationError as e:
                messages.error(request, f"Security Alert: {e.message}")
                return redirect('document_list')

        machine = Machine.objects.filter(pk=machine_id, organization=tenant).first() if machine_id else None
        operator = Operator.objects.filter(pk=operator_id, organization=tenant).first() if operator_id else None

        doc = MachineDocument.objects.create(
            organization=tenant,
            title=title,
            doc_type=doc_type,
            doc_number=doc_number,
            expiry_date=expiry_date,
            machine=machine,
            operator=operator,
            notes=notes
        )

        AuditLog.objects.create(
            organization=tenant,
            user=request.user if request.user.is_authenticated else None,
            action=f"Added compliance document '{title}' ({doc_number})",
            target_model="MachineDocument",
            details=f"Expiry: {expiry_date}"
        )

        messages.success(request, f"Document '{title}' registered successfully.")
        return redirect('document_list')
    return redirect('document_list')
