from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta
import uuid

from apps.core.models import Organization, ActivityLog, Notification
from apps.suppliers.models import (
    Supplier, SupplierContact, SupplierBankDetails, SupplierTaxInformation,
    OnboardingTemplate, DocumentType, DocumentRequirement
)
from apps.documents.models import SupplierDocument
from apps.compliance.models import ComplianceIssue
from apps.approvals.models import ApprovalRequest

def dashboard_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    if not org:
        return render(request, 'dashboard.html', {'empty_state': True})

    total_suppliers = Supplier.objects.filter(organization=org).count()
    pending_onboarding = Supplier.objects.filter(organization=org, status__in=[Supplier.Status.PENDING, Supplier.Status.INVITED]).count()
    pending_approvals = ApprovalRequest.objects.filter(organization=org, status=ApprovalRequest.Status.PENDING).count()
    compliance_issues = ComplianceIssue.objects.filter(organization=org, status=ComplianceIssue.Status.OPEN).count()

    # Overall Compliance score
    avg_compliance = Supplier.objects.filter(organization=org).aggregate(Avg('compliance_score'))['compliance_score__avg'] or 82
    overall_compliance = int(avg_compliance)

    compliant_count = Supplier.objects.filter(organization=org, compliance_score__gte=80).count()
    at_risk_count = Supplier.objects.filter(organization=org, compliance_score__range=(60, 79)).count()
    non_compliant_count = Supplier.objects.filter(organization=org, compliance_score__lt=60).count()

    # Attention Required items
    attention_items = []
    # 1. Expiring / Expired docs
    expiring_docs = SupplierDocument.objects.filter(
        organization=org, 
        status__in=[SupplierDocument.Status.EXPIRING_SOON, SupplierDocument.Status.EXPIRED]
    ).select_related('supplier', 'document_type')[:3]
    
    for doc in expiring_docs:
        attention_items.append({
            'supplier': doc.supplier,
            'title': f"{doc.document_type.name} {'expires in' if doc.status == SupplierDocument.Status.EXPIRING_SOON else 'expired'}",
            'action_text': 'Request Document' if doc.status == SupplierDocument.Status.EXPIRED else 'View Supplier',
            'link': f"/documents/{doc.id}/",
            'type': 'doc'
        })

    # 2. Missing docs or approvals pending
    pending_approvals_list = ApprovalRequest.objects.filter(
        organization=org, 
        status=ApprovalRequest.Status.PENDING
    ).select_related('supplier')[:2]
    
    for app in pending_approvals_list:
        attention_items.append({
            'supplier': app.supplier,
            'title': 'Supplier approval pending internal review',
            'action_text': 'Review',
            'link': f"/approvals/{app.id}/",
            'type': 'approval'
        })

    # Recent Activity logs
    recent_activities = ActivityLog.objects.filter(organization=org)[:6]

    context = {
        'total_suppliers': total_suppliers,
        'pending_onboarding': pending_onboarding,
        'pending_approvals': pending_approvals,
        'compliance_issues': compliance_issues,
        'overall_compliance': overall_compliance,
        'compliant_count': compliant_count,
        'at_risk_count': at_risk_count,
        'non_compliant_count': non_compliant_count,
        'attention_items': attention_items,
        'recent_activities': recent_activities,
    }
    return render(request, 'dashboard.html', context)


def suppliers_list_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    suppliers = Supplier.objects.filter(organization=org).select_related('approved_by').prefetch_related('documents')

    # Filtering
    search_query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    category_filter = request.GET.get('category', '')
    country_filter = request.GET.get('country', '')

    if search_query:
        suppliers = suppliers.filter(
            Q(legal_name__icontains=search_query) |
            Q(trading_name__icontains=search_query) |
            Q(company_email__icontains=search_query)
        )
    if status_filter:
        suppliers = suppliers.filter(status=status_filter)
    if category_filter:
        suppliers = suppliers.filter(category=category_filter)
    if country_filter:
        suppliers = suppliers.filter(country=country_filter)

    categories = Supplier.objects.filter(organization=org).values_list('category', flat=True).distinct()
    countries = Supplier.objects.filter(organization=org).values_list('country', flat=True).distinct()

    context = {
        'suppliers': suppliers,
        'search_query': search_query,
        'status_filter': status_filter,
        'category_filter': category_filter,
        'country_filter': country_filter,
        'categories': categories,
        'countries': countries,
        'statuses': Supplier.Status.choices,
    }
    return render(request, 'suppliers/suppliers_list.html', context)


from apps.core.security import guest_forbidden

@guest_forbidden
def add_supplier_wizard_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    templates = OnboardingTemplate.objects.filter(organization=org)
    doc_types = DocumentType.objects.filter(organization=org)

    if request.method == 'POST':
        legal_name = request.POST.get('legal_name')
        trading_name = request.POST.get('trading_name')
        country = request.POST.get('country', 'India')
        category = request.POST.get('category', 'Manufacturing')
        website = request.POST.get('website')
        company_email = request.POST.get('company_email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        postal_code = request.POST.get('postal_code')
        contact_name = request.POST.get('contact_name')
        contact_title = request.POST.get('contact_title')
        contact_email = request.POST.get('contact_email')
        contact_phone = request.POST.get('contact_phone')
        selected_docs = request.POST.getlist('required_docs')

        # Create Supplier
        supplier = Supplier.objects.create(
            organization=org,
            legal_name=legal_name,
            trading_name=trading_name,
            country=country,
            category=category,
            website=website,
            company_email=company_email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            postal_code=postal_code,
            status=Supplier.Status.INVITED,
            invitation_sent_at=timezone.now(),
            onboarding_deadline=timezone.now().date() + timedelta(days=14)
        )

        # Primary Contact
        if contact_name and contact_email:
            SupplierContact.objects.create(
                supplier=supplier,
                name=contact_name,
                title=contact_title,
                email=contact_email,
                phone=contact_phone,
                is_primary=True
            )

        # Create missing/required document placeholders
        for doc_type_id in selected_docs:
            try:
                dt = DocumentType.objects.get(id=doc_type_id)
                SupplierDocument.objects.create(
                    organization=org,
                    supplier=supplier,
                    document_type=dt,
                    status=SupplierDocument.Status.MISSING
                )
            except DocumentType.DoesNotExist:
                pass

        # Create Activity Log
        ActivityLog.objects.create(
            organization=org,
            user=request.user if request.user.is_authenticated else None,
            action='Supplier Invited',
            object_type='Supplier',
            object_id=str(supplier.id),
            object_name=supplier.legal_name,
            details=f"Onboarding invitation sent to {supplier.company_email}"
        )

        messages.success(request, f"Invitation sent successfully to {supplier.legal_name}!")
        return redirect('supplier_invitation_sent', supplier_id=supplier.id)

    context = {
        'templates': templates,
        'doc_types': doc_types,
    }
    return render(request, 'suppliers/add_supplier_wizard.html', context)


def supplier_invitation_sent_view(request, supplier_id):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    supplier = get_object_or_404(Supplier, id=supplier_id, organization=org)
    required_docs = SupplierDocument.objects.filter(supplier=supplier)

    context = {
        'supplier': supplier,
        'required_docs': required_docs,
        'portal_url': f"/portal/{supplier.invitation_token}/",
    }
    return render(request, 'suppliers/supplier_invitation_sent.html', context)


def supplier_detail_view(request, supplier_id):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    supplier = get_object_or_404(Supplier, id=supplier_id, organization=org)
    active_tab = request.GET.get('tab', 'overview')

    documents = SupplierDocument.objects.filter(supplier=supplier)
    compliance_issues = ComplianceIssue.objects.filter(supplier=supplier)
    contacts = SupplierContact.objects.filter(supplier=supplier)
    bank_details = getattr(supplier, 'bank_details', None)
    tax_info = getattr(supplier, 'tax_info', None)
    approval_requests = ApprovalRequest.objects.filter(supplier=supplier)

    context = {
        'supplier': supplier,
        'active_tab': active_tab,
        'documents': documents,
        'compliance_issues': compliance_issues,
        'contacts': contacts,
        'bank_details': bank_details,
        'tax_info': tax_info,
        'approval_requests': approval_requests,
    }
    return render(request, 'suppliers/supplier_detail.html', context)
