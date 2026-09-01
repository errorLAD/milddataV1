from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.core.models import Organization, ActivityLog, Notification
from apps.documents.models import SupplierDocument
from apps.suppliers.models import Supplier, DocumentType
from apps.compliance.models import ComplianceIssue

def mock_ai_extraction_service(doc_name, doc_type_name, supplier_name):
    """
    Mock AI Document Processing Extraction service.
    Returns structured extracted fields with confidence levels.
    """
    import random
    from datetime import date, timedelta

    exp_date = (date.today() + timedelta(days=random.randint(10, 400))).strftime("%Y-%m-%d")
    policy_no = f"POL-{random.randint(100000, 999999)}"
    reg_no = f"REG-{random.randint(10000, 99999)}"
    tax_no = f"TAX-{random.randint(1000000, 9999999)}"

    extracted = {
        'company_name': supplier_name,
        'document_type': doc_type_name,
        'registration_number': reg_no,
        'tax_number': tax_no,
        'policy_number': policy_no,
        'expiry_date': exp_date,
        'address_matched': True
    }
    confidence = round(random.uniform(0.88, 0.99), 2)
    return extracted, confidence

def documents_list_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    documents = SupplierDocument.objects.filter(organization=org).select_related('supplier', 'document_type', 'verified_by')

    status_tab = request.GET.get('status', 'all')
    search_query = request.GET.get('q', '')

    if status_tab != 'all':
        documents = documents.filter(status=status_tab.upper())

    if search_query:
        documents = documents.filter(
            supplier__legal_name__icontains=search_query
        ) | documents.filter(
            document_type__name__icontains=search_query
        )

    context = {
        'documents': documents,
        'status_tab': status_tab,
        'search_query': search_query,
        'statuses': SupplierDocument.Status.choices,
    }
    return render(request, 'documents/documents_list.html', context)


from apps.core.security import guest_forbidden

@guest_forbidden
def document_detail_view(request, doc_id):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    doc = get_object_or_404(SupplierDocument, id=doc_id, organization=org)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            doc.status = SupplierDocument.Status.VERIFIED
            doc.verified_by = request.user if request.user.is_authenticated else None
            doc.verified_at = timezone.now()
            doc.save()

            # Recalculate supplier compliance score
            supplier = doc.supplier
            verified_count = SupplierDocument.objects.filter(supplier=supplier, status=SupplierDocument.Status.VERIFIED).count()
            total_count = SupplierDocument.objects.filter(supplier=supplier).count()
            if total_count > 0:
                supplier.compliance_score = int((verified_count / total_count) * 100)
                supplier.save()

            ActivityLog.objects.create(
                organization=org,
                user=request.user if request.user.is_authenticated else None,
                action='Document Verified',
                object_type='SupplierDocument',
                object_id=str(doc.id),
                object_name=f"{doc.document_type.name} ({supplier.legal_name})"
            )

            messages.success(request, f"Document '{doc.document_type.name}' verified successfully.")

        elif action == 'reject':
            rejection_reason = request.POST.get('rejection_reason', 'Document quality insufficient or invalid details.')
            doc.status = SupplierDocument.Status.REJECTED
            doc.rejection_reason = rejection_reason
            doc.save()

            # Create Compliance Issue
            ComplianceIssue.objects.create(
                organization=org,
                supplier=doc.supplier,
                document=doc,
                title=f"Rejected Document: {doc.document_type.name}",
                description=f"Reason: {rejection_reason}",
                severity=ComplianceIssue.Severity.HIGH,
                due_date=timezone.now().date() + timezone.timedelta(days=7)
            )

            ActivityLog.objects.create(
                organization=org,
                user=request.user if request.user.is_authenticated else None,
                action='Document Rejected',
                object_type='SupplierDocument',
                object_id=str(doc.id),
                object_name=f"{doc.document_type.name} ({doc.supplier.legal_name})",
                details=f"Reason: {rejection_reason}"
            )

            messages.error(request, f"Document rejected. Compliance issue logged for supplier.")

        elif action == 'confirm_ai':
            doc.ai_status = SupplierDocument.AIStatus.CONFIRMED
            doc.save()
            messages.success(request, "AI extracted data confirmed.")

        return redirect('document_detail', doc_id=doc.id)

    # Run AI extraction mock if not run
    if not doc.ai_extracted_data and doc.file:
        extracted, conf = mock_ai_extraction_service(doc.file_name or 'document.pdf', doc.document_type.name, doc.supplier.legal_name)
        doc.ai_extracted_data = extracted
        doc.ai_confidence = conf
        doc.ai_status = SupplierDocument.AIStatus.EXTRACTED
        doc.save()

    activities = ActivityLog.objects.filter(organization=org, object_id=str(doc.id))

    context = {
        'doc': doc,
        'activities': activities,
    }
    return render(request, 'documents/document_detail.html', context)
