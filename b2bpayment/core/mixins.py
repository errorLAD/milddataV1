from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

class TenantRequiredMixin(LoginRequiredMixin):
    """
    Mixin for class-based views that ensures user is logged in and belongs to a business.
    Automatically scopes get_queryset() to request.business.
    """
    def dispatch(self, request, *args, **kwargs):
        is_guest = getattr(request, 'is_guest', False)
        if not request.user.is_authenticated and not is_guest:
            return self.handle_no_permission()
        if not getattr(request, 'business', None):
            messages.warning(request, "Please complete your business setup or log in again.")
            return redirect('accounts:login')
        if not request.business.is_active and not (request.user.is_superuser or request.user.is_staff or is_guest):
            from django.shortcuts import render
            return render(request, 'blocked.html')
        return super(LoginRequiredMixin, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs, 'for_business') and self.request.business:
            return qs.for_business(self.request.business)
        elif self.request.business and hasattr(qs.model, 'business'):
            return qs.filter(business=self.request.business)
        return qs

    def form_valid(self, form):
        if hasattr(form.instance, 'business') and self.request.business:
            form.instance.business = self.request.business
        return super().form_valid(form)
