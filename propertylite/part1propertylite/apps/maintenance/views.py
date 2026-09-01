from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MaintenanceTicket, Vendor, TicketMaterial, TicketLabour
from apps.properties.models import Property, Unit
from apps.core.models import User, AuditLog, Notification
from apps.core.utils.security import guest_restricted

@login_required
def ticket_list(request):
    org = request.user.organization
    tickets = MaintenanceTicket.objects.filter(organization=org)

    # View type (kanban or table)
    view_type = request.GET.get('view', 'kanban')
    
    # Priority/Status filters
    priority_filter = request.GET.get('priority')
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    new_tickets = tickets.filter(status=MaintenanceTicket.STATUS_NEW)
    in_progress_tickets = tickets.filter(status__in=[MaintenanceTicket.STATUS_ASSIGNED, MaintenanceTicket.STATUS_IN_PROGRESS, MaintenanceTicket.STATUS_WAITING])
    completed_tickets = tickets.filter(status=MaintenanceTicket.STATUS_COMPLETED)

    return render(request, 'maintenance/ticket_list.html', {
        'tickets': tickets,
        'new_tickets': new_tickets,
        'in_progress_tickets': in_progress_tickets,
        'completed_tickets': completed_tickets,
        'view_type': view_type,
        'priorities': MaintenanceTicket.PRIORITY_CHOICES,
    })

@login_required
def ticket_detail(request, pk):
    org = request.user.organization
    ticket = get_object_or_404(MaintenanceTicket, id=pk, organization=org)
    staff_users = User.objects.filter(organization=org, role=User.ROLE_MAINTENANCE_STAFF)
    vendors = Vendor.objects.filter(organization=org)

    if request.method == 'POST':
        if request.user.is_guest:
            messages.warning(request, "🔒 Guest Access Mode: Modifying tickets requires a full property manager account.")
            return redirect('guest_upgrade')

        action = request.POST.get('action')
        
        if action == 'add_material':
            mat_name = request.POST.get('material_name')
            qty = request.POST.get('quantity') or 1
            cost = request.POST.get('unit_cost') or 0
            TicketMaterial.objects.create(ticket=ticket, material_name=mat_name, quantity=qty, unit_cost=cost)
            messages.success(request, f"Material '{mat_name}' added to ticket!")

        elif action == 'add_labour':
            worker = request.POST.get('worker_name')
            hours = request.POST.get('hours') or 1
            rate = request.POST.get('rate') or 0
            TicketLabour.objects.create(ticket=ticket, worker_name=worker, hours=hours, rate=rate)
            messages.success(request, f"Labour entry added for '{worker}'!")

        elif action == 'update_status':
            new_status = request.POST.get('status')
            staff_id = request.POST.get('assigned_staff')
            vendor_id = request.POST.get('assigned_vendor')

            ticket.status = new_status
            if staff_id:
                ticket.assigned_staff = User.objects.filter(id=staff_id, organization=org).first()
            if vendor_id:
                ticket.assigned_vendor = Vendor.objects.filter(id=vendor_id, organization=org).first()
            ticket.save()

            Notification.objects.create(
                organization=org,
                recipient=ticket.tenant,
                title=f"Maintenance Ticket #{ticket.id} Updated",
                message=f"Status changed to {ticket.get_status_display()}.",
                notification_type=Notification.TYPE_MAINTENANCE
            )

            messages.success(request, "Ticket updated successfully!")

        return redirect('ticket_detail', pk=ticket.id)

    return render(request, 'maintenance/ticket_detail.html', {
        'ticket': ticket,
        'staff_users': staff_users,
        'vendors': vendors,
        'status_choices': MaintenanceTicket.STATUS_CHOICES,
    })

@login_required
@guest_restricted
def ticket_create(request):
    org = request.user.organization
    properties = Property.objects.filter(organization=org)
    units = Unit.objects.filter(property__organization=org)
    tenants = User.objects.filter(organization=org, role=User.ROLE_TENANT)

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        unit_id = request.POST.get('unit')
        tenant_id = request.POST.get('tenant') or request.user.id
        category = request.POST.get('category')
        priority = request.POST.get('priority')

        unit = get_object_or_404(Unit, id=unit_id, property__organization=org)
        tenant = get_object_or_404(User, id=tenant_id, organization=org)

        ticket = MaintenanceTicket.objects.create(
            organization=org,
            title=title,
            description=description,
            property=unit.property,
            unit=unit,
            tenant=tenant,
            category=category,
            priority=priority,
            status=MaintenanceTicket.STATUS_NEW
        )

        AuditLog.objects.create(
            organization=org,
            user=request.user,
            action=f"Created Maintenance Ticket #{ticket.id}: {ticket.title}",
            entity_type="MaintenanceTicket",
            entity_id=str(ticket.id)
        )

        messages.success(request, f"Maintenance request #{ticket.id} submitted!")
        return redirect('ticket_detail', pk=ticket.id)

    return render(request, 'maintenance/ticket_form.html', {
        'properties': properties,
        'units': units,
        'tenants': tenants,
        'categories': MaintenanceTicket.CATEGORY_CHOICES,
        'priorities': MaintenanceTicket.PRIORITY_CHOICES,
    })

@login_required
def vendor_list(request):
    org = request.user.organization
    vendors = Vendor.objects.filter(organization=org)

    if request.method == 'POST':
        if request.user.is_guest:
            messages.warning(request, "🔒 Guest Access Mode: Adding vendors requires a full property manager account.")
            return redirect('guest_upgrade')

        name = request.POST.get('name')
        company = request.POST.get('company')
        category = request.POST.get('category')
        phone = request.POST.get('phone')
        email = request.POST.get('email')

        Vendor.objects.create(
            organization=org,
            name=name,
            company=company,
            category=category,
            phone=phone,
            email=email
        )
        messages.success(request, f"Vendor '{company}' added successfully!")
        return redirect('vendor_list')

    return render(request, 'maintenance/vendor_list.html', {'vendors': vendors})
