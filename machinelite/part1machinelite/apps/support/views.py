from django.shortcuts import render, redirect
from django.contrib import messages

def support_index(request):
    """Render Help Center & FAQs."""
    return render(request, 'support/index.html')

def submit_ticket(request):
    if request.method == 'POST':
        messages.success(request, "Ticket submitted! Our technical support team will contact you within 2 business hours.")
        return redirect('support_index')
    return redirect('support_index')
