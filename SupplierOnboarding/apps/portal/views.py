from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.suppliers.models import Supplier, SupplierContact, SupplierBankDetails, SupplierTaxInformation
from apps.documents.models import SupplierDocument
from apps.approvals.models import ApprovalRequest
from apps.core.models import ActivityLog, Notification

def supplier_portal_view(request, token):
    supplier = get_object_or_404(Supplier, invitation_token=token)
    documents = SupplierDocument.objects.filter(supplier=supplier)
    
    # Calculate onboarding completion percentage
    total_steps = 4 + documents.count()
    completed_steps = 0
    
    # Check info completeness
    if supplier.legal_name and supplier.company_email and supplier.phone:
        completed_steps += 1
    if hasattr(supplier, 'tax_info') and supplier.tax_info.tax_id_number:
        completed_steps += 1
    if hasattr(supplier, 'bank_details') and supplier.bank_details.account_number:
        completed_steps += 1
    
    # Docs completeness
    uploaded_docs = documents.exclude(status=SupplierDocument.Status.MISSING).count()
    completed_steps += uploaded_docs
    if supplier.status == Supplier.Status.APPROVED or supplier.status == Supplier.Status.IN_REVIEW:
        completed_steps += 1

    completion_percentage = int((completed_steps / total_steps) * 100) if total_steps > 0 else 0
    if completion_percentage > 100:
        completion_percentage = 100

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_company':
            supplier.legal_name = request.POST.get('legal_name', supplier.legal_name)
            supplier.trading_name = request.POST.get('trading_name')
            supplier.phone = request.POST.get('phone')
            supplier.website = request.POST.get('website')
            supplier.address = request.POST.get('address')
            supplier.city = request.POST.get('city')
            supplier.state = request.POST.get('state')
            supplier.postal_code = request.POST.get('postal_code')
            supplier.save()
            messages.success(request, "Company details updated successfully.")

        elif action == 'save_tax':
            tax_info, _ = SupplierTaxInformation.objects.get_or_create(supplier=supplier)
            tax_info.tax_id_number = request.POST.get('tax_id_number')
            tax_info.gst_vat_number = request.POST.get('gst_vat_number')
            tax_info.tax_residency_country = request.POST.get('tax_residency_country', 'India')
            tax_info.save()
            messages.success(request, "Tax details saved successfully.")

        elif action == 'save_bank':
            bank, _ = SupplierBankDetails.objects.get_or_create(supplier=supplier)
            bank.bank_name = request.POST.get('bank_name')
            bank.account_name = request.POST.get('account_name')
            bank.account_number = request.POST.get('account_number')
            bank.swift_bic = request.POST.get('swift_bic')
            bank.iban = request.POST.get('iban')
            bank.save()
            messages.success(request, "Bank details saved successfully.")

        elif action == 'submit_for_review':
            supplier.status = Supplier.Status.IN_REVIEW
            supplier.onboarding_completed_at = timezone.now()
            supplier.save()

            # Create Approval Request for internal team
            ApprovalRequest.objects.create(
                organization=supplier.organization,
                supplier=supplier,
                status=ApprovalRequest.Status.PENDING,
                risk_flags=["Initial Onboarding Submission"]
            )

            # Log Activity
            ActivityLog.objects.create(
                organization=supplier.organization,
                action='Supplier Onboarding Submitted',
                object_type='Supplier',
                object_id=str(supplier.id),
                object_name=supplier.legal_name,
                details="Supplier completed portal onboarding checklist."
            )

            # Create Notification for team
            Notification.objects.create(
                organization=supplier.organization,
                title="New Supplier Onboarding Submitted",
                message=f"{supplier.legal_name} has submitted their onboarding details for approval.",
                notification_type=Notification.Type.APPROVAL,
                link=f"/suppliers/{supplier.id}/"
            )

            messages.success(request, "Onboarding submitted successfully! Our procurement team will review your application.")
            return redirect('portal_view', token=token)

        return redirect('portal_view', token=token)

    context = {
        'supplier': supplier,
        'documents': documents,
        'completion_percentage': completion_percentage,
        'token': token,
    }
    return render(request, 'portal/supplier_portal.html', context)


from django.core.exceptions import ValidationError
from apps.core.security import validate_file_upload

def portal_upload_document_view(request, token, doc_id):
    supplier = get_object_or_404(Supplier, invitation_token=token)
    doc = get_object_or_404(SupplierDocument, id=doc_id, supplier=supplier)

    if request.method == 'POST' and request.FILES.get('file'):
        file_obj = request.FILES['file']
        try:
            safe_name = validate_file_upload(file_obj)
        except ValidationError as e:
            messages.error(request, str(e))
            return redirect('portal_view', token=token)

        doc.file = file_obj
        doc.file_name = file_obj.name
        doc.file_size = file_obj.size
        doc.file_type = file_obj.name.split('.')[-1].upper() if '.' in file_obj.name else 'PDF'
        doc.status = SupplierDocument.Status.PENDING_REVIEW
        
        # Set dummy issue and expiry dates for verification tracking
        doc.issue_date = timezone.now().date()
        doc.expiry_date = timezone.now().date() + timezone.timedelta(days=365)
        
        # AI Extraction simulation
        doc.ai_extracted_data = {
            'company_name': supplier.legal_name,
            'document_type': doc.document_type.name,
            'file_name': file_obj.name,
            'status': 'Uploaded via Supplier Portal'
        }
        doc.ai_confidence = 0.95
        doc.ai_status = SupplierDocument.AIStatus.EXTRACTED
        doc.save()

        ActivityLog.objects.create(
            organization=supplier.organization,
            action='Document Uploaded via Portal',
            object_type='SupplierDocument',
            object_id=str(doc.id),
            object_name=f"{doc.document_type.name} ({supplier.legal_name})"
        )

        messages.success(request, f"Document '{doc.document_type.name}' uploaded successfully!")

    return redirect('portal_view', token=token)
