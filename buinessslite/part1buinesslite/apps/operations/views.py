from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta, datetime

from apps.operations.models import Task, TaskStatus, TaskPriority, CalendarEvent, BusinessDocument, DocCategory
from apps.people.models import LeaveRequest
from apps.sales.models import Invoice, InvoiceStatus
from apps.core.models import AuditLog

@login_required
def task_list_view(request):
    org = request.organization
    view_type = request.GET.get('view', 'all')
    
    tasks = Task.objects.filter(organization=org)
    if view_type == 'my':
        tasks = tasks.filter(assigned_to=request.user)

    return render(request, 'operations/task_list.html', {'tasks': tasks, 'view_type': view_type})

@login_required
def task_create_view(request):
    org = request.organization
    if request.method == 'POST':
        t = Task.objects.create(
            organization=org,
            title=request.POST.get('title'),
            assigned_to=request.user if request.POST.get('assign_me') else None,
            due_date=request.POST.get('due_date') or None,
            priority=request.POST.get('priority', TaskPriority.MEDIUM),
            status=TaskStatus.TO_DO
        )
        AuditLog.objects.create(organization=org, user=request.user, action="Task Created", model_name="Task", record_id=str(t.id), details=f"Task '{t.title}' created.")
        return redirect('task_list')
    return render(request, 'operations/task_form.html', {'priorities': TaskPriority.choices})

@login_required
def update_task_status_view(request, task_id):
    org = request.organization
    task = get_object_or_404(Task, id=task_id, organization=org)
    new_status = request.POST.get('status')
    if new_status in TaskStatus.values:
        task.status = new_status
        task.save()
    return redirect('task_list')

@login_required
def calendar_view(request):
    org = request.organization
    today = timezone.now().date()
    
    events = []
    
    # 1. Leave events
    for l in LeaveRequest.objects.filter(organization=org, status='APPROVED'):
        events.append({
            'title': f"🌴 {l.employee.name} on Leave",
            'date': str(l.start_date),
            'type': 'Leave'
        })

    # 2. Invoice due dates
    for inv in Invoice.objects.filter(organization=org).exclude(status__in=[InvoiceStatus.PAID, InvoiceStatus.VOID]):
        events.append({
            'title': f"💰 Due: {inv.invoice_number} ({inv.customer.company_name})",
            'date': str(inv.due_date),
            'type': 'Invoice Due'
        })

    # 3. Tasks
    for t in Task.objects.filter(organization=org).exclude(status=TaskStatus.DONE):
        if t.due_date:
            events.append({
                'title': f"📋 Task: {t.title}",
                'date': str(t.due_date),
                'type': 'Task'
            })

    return render(request, 'operations/calendar.html', {'events': events, 'today': today})

@login_required
def business_document_list_view(request):
    org = request.organization
    docs = BusinessDocument.objects.filter(organization=org)
    return render(request, 'operations/document_list.html', {'docs': docs})

@login_required
def document_upload_view(request):
    org = request.organization
    if request.method == 'POST':
        doc = BusinessDocument.objects.create(
            organization=org,
            title=request.POST.get('title'),
            category=request.POST.get('category', DocCategory.BUSINESS),
            related_record=request.POST.get('related_record', ''),
            expiry_date=request.POST.get('expiry_date') or None
        )
        if request.FILES.get('file'):
            doc.file = request.FILES['file']
            doc.save()
        AuditLog.objects.create(organization=org, user=request.user, action="Document Uploaded", model_name="BusinessDocument", record_id=str(doc.id), details=f"Document '{doc.title}' uploaded.")
        return redirect('business_document_list')
    return render(request, 'operations/document_form.html', {'categories': DocCategory.choices})
