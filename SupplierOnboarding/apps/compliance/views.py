from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Avg, Count
from django.utils import timezone
from apps.core.models import Organization, ActivityLog
from apps.compliance.models import ComplianceIssue
from apps.suppliers.models import Supplier
from apps.documents.models import SupplierDocument

from apps.core.security import guest_forbidden

@guest_forbidden
def compliance_center_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    issues = ComplianceIssue.objects.filter(organization=org).select_related('supplier', 'document')

    # Metrics
    avg_score = Supplier.objects.filter(organization=org).aggregate(Avg('compliance_score'))['compliance_score__avg'] or 82
    compliance_score = int(avg_score)
    
    critical_issues_count = issues.filter(severity=ComplianceIssue.Severity.CRITICAL, status=ComplianceIssue.Status.OPEN).count()
    expiring_docs_count = SupplierDocument.objects.filter(organization=org, status=SupplierDocument.Status.EXPIRING_SOON).count()
    missing_docs_count = SupplierDocument.objects.filter(organization=org, status=SupplierDocument.Status.MISSING).count()
    rejected_docs_count = SupplierDocument.objects.filter(organization=org, status=SupplierDocument.Status.REJECTED).count()

    # Filtering
    severity_filter = request.GET.get('severity', '')
    status_filter = request.GET.get('status', 'OPEN')

    if severity_filter:
        issues = issues.filter(severity=severity_filter)
    if status_filter != 'ALL':
        issues = issues.filter(status=status_filter)

    if request.method == 'POST':
        issue_id = request.POST.get('issue_id')
        action = request.POST.get('action')
        if issue_id and action == 'resolve':
            issue = get_object_or_404(ComplianceIssue, id=issue_id, organization=org)
            issue.status = ComplianceIssue.Status.RESOLVED
            issue.resolved_at = timezone.now()
            issue.resolved_by = request.user if request.user.is_authenticated else None
            issue.save()

            ActivityLog.objects.create(
                organization=org,
                user=request.user if request.user.is_authenticated else None,
                action='Compliance Issue Resolved',
                object_type='ComplianceIssue',
                object_id=str(issue.id),
                object_name=issue.title
            )

            messages.success(request, f"Compliance issue '{issue.title}' resolved.")
            return redirect('compliance_center')

    context = {
        'issues': issues,
        'compliance_score': compliance_score,
        'critical_issues_count': critical_issues_count,
        'expiring_docs_count': expiring_docs_count,
        'missing_docs_count': missing_docs_count,
        'rejected_docs_count': rejected_docs_count,
        'severity_filter': severity_filter,
        'status_filter': status_filter,
        'severities': ComplianceIssue.Severity.choices,
    }
    return render(request, 'compliance/compliance_center.html', context)
