from django.shortcuts import redirect
from django.views import View
from core.mixins import TenantRequiredMixin
from .models import Notification

class MarkAllReadView(TenantRequiredMixin, View):
    def get(self, request):
        Notification.objects.filter(business=request.business, is_read=False).update(is_read=True)
        return redirect(request.META.get('HTTP_REFERER', 'dashboard:index'))
