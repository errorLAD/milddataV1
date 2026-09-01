import time
import uuid

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render

from .forms import LoginForm, SignUpForm


def _clear_guest_session(request):
    request.session.pop("is_guest", None)
    request.session.pop("guest_id", None)
    request.session.pop("guest_created_at", None)


class UserLoginView(LoginView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        _clear_guest_session(self.request)
        messages.success(self.request, "Successfully logged in!")
        return super().form_valid(form)


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("products:catalog")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            _clear_guest_session(request)
            login(request, user)
            messages.success(request, "Account created successfully!")
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url or "products:catalog")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


def guest_login(request):
    """Initialize temporary guest session."""
    if request.user.is_authenticated:
        return redirect("products:catalog")

    guest_uid = f"guest_{uuid.uuid4().hex[:10]}"
    request.session["is_guest"] = True
    request.session["guest_id"] = guest_uid
    request.session["guest_created_at"] = time.time()
    
    next_url = request.GET.get("next")
    return redirect(next_url or "products:saas_directory")


def logout_view(request):
    _clear_guest_session(request)
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("home")
