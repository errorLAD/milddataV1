import time
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import timedelta

from apps.core.models import Organization, User, ActivityLog, Notification
from apps.suppliers.models import Supplier, OnboardingTemplate, DocumentType, DocumentRequirement
from apps.documents.models import SupplierDocument
from apps.compliance.models import ComplianceIssue
from apps.approvals.models import ApprovalRequest
from apps.core.security import guest_forbidden

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            request.session['is_guest'] = False
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'auth/login.html')


def register_view(request):
    if request.method == 'POST':
        org_name = request.POST.get('org_name', 'My Company Inc.')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if User.objects.filter(username=email).exists():
            messages.error(request, "An account with this email already exists.")
            return redirect('register')

        org = Organization.objects.create(name=org_name, slug=org_name.lower().replace(' ', '-'))
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            organization=org,
            role=User.Role.ADMIN
        )
        login(request, user)
        request.session['is_guest'] = False
        messages.success(request, f"Account created successfully for {org_name}!")
        return redirect('dashboard')

    return render(request, 'auth/register.html')


def guest_login_view(request):
    """
    Initializes a temporary guest access session.
    """
    request.session.flush()
    request.session['is_guest'] = True
    request.session['guest_created_at'] = time.time()
    messages.info(request, "You are now exploring SupplierOS in Guest Mode (Demo Sandbox Access).")
    return redirect('dashboard')


def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, "Logged out successfully.")
    return redirect('login')


@guest_forbidden
def templates_list_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    templates = OnboardingTemplate.objects.filter(organization=org).prefetch_related('requirements__document_type')
    doc_types = DocumentType.objects.filter(organization=org)

    if request.method == 'POST':
        name = request.POST.get('name')
        category = request.POST.get('supplier_category')
        description = request.POST.get('description')
        selected_docs = request.POST.getlist('document_types')

        template = OnboardingTemplate.objects.create(
            organization=org,
            name=name,
            supplier_category=category,
            description=description
        )

        for dt_id in selected_docs:
            dt = DocumentType.objects.filter(id=dt_id).first()
            if dt:
                DocumentRequirement.objects.create(
                    template=template,
                    document_type=dt,
                    is_mandatory=True
                )

        messages.success(request, f"Onboarding Template '{template.name}' created.")
        return redirect('templates_list')

    context = {
        'templates': templates,
        'doc_types': doc_types,
    }
    return render(request, 'core/templates_list.html', context)


def notifications_list_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    notifications = Notification.objects.filter(organization=org)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'mark_all_read':
            notifications.update(is_read=True)
            messages.success(request, "All notifications marked as read.")
            return redirect('notifications_list')

    context = {
        'notifications': notifications,
    }
    return render(request, 'core/notifications_list.html', context)


def activity_log_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    logs = ActivityLog.objects.filter(organization=org).select_related('user')[:100]

    context = {
        'logs': logs,
    }
    return render(request, 'core/activity_log.html', context)


def global_search_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    query = request.GET.get('q', '').strip()

    suppliers = []
    documents = []
    compliance_issues = []
    approvals = []

    if query:
        suppliers = Supplier.objects.filter(
            organization=org
        ).filter(
            Q(legal_name__icontains=query) |
            Q(trading_name__icontains=query) |
            Q(company_email__icontains=query) |
            Q(category__icontains=query)
        )[:10]

        documents = SupplierDocument.objects.filter(
            organization=org
        ).filter(
            Q(document_type__name__icontains=query) |
            Q(supplier__legal_name__icontains=query) |
            Q(file_name__icontains=query)
        ).select_related('supplier', 'document_type')[:10]

        compliance_issues = ComplianceIssue.objects.filter(
            organization=org
        ).filter(
            Q(title__icontains=query) |
            Q(supplier__legal_name__icontains=query) |
            Q(description__icontains=query)
        ).select_related('supplier')[:10]

        approvals = ApprovalRequest.objects.filter(
            organization=org
        ).filter(
            Q(supplier__legal_name__icontains=query)
        ).select_related('supplier')[:10]

    context = {
        'query': query,
        'suppliers': suppliers,
        'documents': documents,
        'compliance_issues': compliance_issues,
        'approvals': approvals,
    }
    return render(request, 'core/global_search.html', context)


def reports_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()

    status_counts = Supplier.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    category_counts = Supplier.objects.filter(organization=org).values('category').annotate(count=Count('id'))
    doc_status_counts = SupplierDocument.objects.filter(organization=org).values('status').annotate(count=Count('id'))

    avg_compliance = Supplier.objects.filter(organization=org).aggregate(Avg('compliance_score'))['compliance_score__avg'] or 82

    context = {
        'status_counts': status_counts,
        'category_counts': category_counts,
        'doc_status_counts': doc_status_counts,
        'avg_compliance': int(avg_compliance),
    }
    return render(request, 'core/reports.html', context)


@guest_forbidden
def settings_view(request):
    org = getattr(request.user, 'organization', None) or Organization.objects.first()
    users = User.objects.filter(organization=org)
    doc_types = DocumentType.objects.filter(organization=org)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_org':
            if org:
                org.name = request.POST.get('org_name', org.name)
                org.domain = request.POST.get('domain', org.domain)
                org.save()
                messages.success(request, "Organization settings saved.")
        elif action == 'add_doc_type':
            name = request.POST.get('doc_name')
            code = request.POST.get('doc_code', name.lower().replace(' ', '_'))
            days = int(request.POST.get('expiry_days', 365))
            DocumentType.objects.create(
                organization=org,
                name=name,
                code=code,
                default_expiry_days=days
            )
            messages.success(request, f"Document type '{name}' created.")

        return redirect('settings')

    context = {
        'org': org,
        'users': users,
        'doc_types': doc_types,
        'roles': User.Role.choices,
    }
    return render(request, 'core/settings.html', context)
