from apps.core.models import Organization, Notification
from apps.suppliers.models import Supplier
from apps.documents.models import SupplierDocument
from apps.compliance.models import ComplianceIssue
from apps.approvals.models import ApprovalRequest

def global_context(request):
    is_guest = getattr(request, 'is_guest', False) or request.session.get('is_guest', False)

    if not request.user.is_authenticated and not is_guest:
        org = Organization.objects.first()
    else:
        org = getattr(request.user, 'organization', None) or Organization.objects.first()

    if not org:
        return {'is_guest': is_guest}

    unread_notifications = Notification.objects.filter(organization=org, is_read=False)[:5]
    unread_count = Notification.objects.filter(organization=org, is_read=False).count()
    pending_approvals_count = ApprovalRequest.objects.filter(organization=org, status=ApprovalRequest.Status.PENDING).count()
    open_compliance_issues_count = ComplianceIssue.objects.filter(organization=org, status=ComplianceIssue.Status.OPEN).count()

    return {
        'current_org': org,
        'is_guest': is_guest,
        'unread_notifications_count': unread_count,
        'notifications_list': unread_notifications,
        'pending_approvals_count': pending_approvals_count,
        'open_compliance_issues_count': open_compliance_issues_count,
    }
