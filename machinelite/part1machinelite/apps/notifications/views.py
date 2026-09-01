from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification

def notification_list(request):
    tenant = request.tenant
    if not tenant:
        return redirect('login')

    notifications = Notification.objects.filter(organization=tenant)
    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'notifications/list.html', context)

def mark_read(request, pk):
    tenant = request.tenant
    if not tenant:
        return JsonResponse({'error': 'No tenant'}, status=400)
    
    notification = get_object_or_404(Notification, pk=pk, organization=tenant)
    notification.is_read = True
    notification.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('notification_list')

def mark_all_read(request):
    tenant = request.tenant
    if tenant:
        Notification.objects.filter(organization=tenant, is_read=False).update(is_read=True)
    return redirect('notification_list')
