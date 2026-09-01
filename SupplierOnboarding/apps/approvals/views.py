from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from apps.core.models import Organization, ActivityLog, Notification
from apps.approvals.models import ApprovalRequest
from apps.suppliers.models import Supplier
from apps.documents.models import SupplierDocument

def approvals_list_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    approvals = ApprovalRequest.objects.filter(organization=org).select_related('supplier', 'reviewer')

    status_filter = request.GET.get('status', 'PENDING')
    if status_filter != 'ALL':
        approvals = approvals.filter(status=status_filter)

    context = {
        'approvals': approvals,
        'status_filter': status_filter,
        'statuses': ApprovalRequest.Status.choices,
    }
    return render(request, 'approvals/approvals_list.html', context)


from apps.core.security import guest_forbidden

@guest_forbidden
def approval_detail_view(request, approval_id):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    approval = get_object_or_404(ApprovalRequest, id=approval_id, organization=org)
    supplier = approval.supplier

    documents = SupplierDocument.objects.filter(supplier=supplier)
    missing_docs = documents.filter(status=SupplierDocument.Status.MISSING).count()
    unverified_docs = documents.filter(status=SupplierDocument.Status.PENDING_REVIEW).count()

    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')
        rejection_reason = request.POST.get('rejection_reason', '')

        if action == 'approve':
            approval.status = ApprovalRequest.Status.APPROVED
            approval.reviewer = request.user if request.user.is_authenticated else None
            approval.reviewed_at = timezone.now()
            approval.comments = comments
            approval.save()

            supplier.status = Supplier.Status.APPROVED
            supplier.approved_at = timezone.now()
            supplier.approved_by = request.user if request.user.is_authenticated else None
            supplier.save()

            ActivityLog.objects.create(
                organization=org,
                user=request.user if request.user.is_authenticated else None,
                action='Supplier Approved',
                object_type='Supplier',
                object_id=str(supplier.id),
                object_name=supplier.legal_name,
                details=f"Comments: {comments}"
            )

            Notification.objects.create(
                organization=org,
                title="Supplier Approved",
                message=f"{supplier.legal_name} has been approved as an active supplier.",
                notification_type=Notification.Type.APPROVAL,
                link=f"/suppliers/{supplier.id}/"
            )

            messages.success(request, f"Supplier '{supplier.legal_name}' approved successfully!")

        elif action == 'reject':
            approval.status = ApprovalRequest.Status.REJECTED
            approval.reviewer = request.user if request.user.is_authenticated else None
            approval.reviewed_at = timezone.now()
            approval.rejection_reason = rejection_reason
            approval.save()

            supplier.status = Supplier.Status.REJECTED
            supplier.save()

            ActivityLog.objects.create(
                organization=org,
                user=request.user if request.user.is_authenticated else None,
                action='Supplier Rejected',
                object_type='Supplier',
                object_id=str(supplier.id),
                object_name=supplier.legal_name,
                details=f"Rejection Reason: {rejection_reason}"
            )

            messages.error(request, f"Supplier '{supplier.legal_name}' rejected.")

        return redirect('approvals_list')

    context = {
        'approval': approval,
        'supplier': supplier,
        'documents': documents,
        'missing_docs': missing_docs,
        'unverified_docs': unverified_docs,
    }
    return render(request, 'approvals/approval_detail.html', context)
