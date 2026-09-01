from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
from core.mixins import TenantRequiredMixin
from .models import BusinessSettings
from .forms import (
    BusinessInfoForm, RegionalSettingsForm, PaymentSettingsForm, WhatsAppSettingsForm,
    RecoveryRulesForm, LateFeeSettingsForm, AISettingsForm
)
from whatsapp.models import WhatsAppMessageTemplate
from ai_advisor.llm_provider import test_llm_connection

class SettingsView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        settings_obj, _ = BusinessSettings.objects.get_or_create(business=business)
        templates = WhatsAppMessageTemplate.objects.filter(business=business)

        context = {
            'b_form': BusinessInfoForm(instance=business),
            'reg_form': RegionalSettingsForm(instance=settings_obj),
            'p_form': PaymentSettingsForm(instance=settings_obj),
            'w_form': WhatsAppSettingsForm(instance=settings_obj),
            'r_form': RecoveryRulesForm(instance=settings_obj),
            'l_form': LateFeeSettingsForm(instance=settings_obj),
            'ai_form': AISettingsForm(instance=settings_obj),
            'templates': templates,
            'settings': settings_obj
        }
        return render(request, 'settings_app/settings.html', context)

    def post(self, request):
        business = request.business
        settings_obj, _ = BusinessSettings.objects.get_or_create(business=business)
        action = request.POST.get('action')

        if action == 'business_info':
            b_form = BusinessInfoForm(request.POST, instance=business)
            if b_form.is_valid():
                b_form.save()
                messages.success(request, "Business information updated!")
        elif action == 'regional_settings':
            reg_form = RegionalSettingsForm(request.POST, instance=settings_obj)
            if reg_form.is_valid():
                saved_obj = reg_form.save(commit=False)
                # Auto-apply defaults if country changed or explicitly requested
                if 'country' in reg_form.changed_data or request.POST.get('apply_country_defaults') == 'true' or not saved_obj.currency_symbol:
                    saved_obj.apply_country_defaults(saved_obj.country)
                saved_obj.save()
                messages.success(request, f"Regional & Country Settings updated for {saved_obj.country} ({saved_obj.currency} {saved_obj.currency_symbol})!")
        elif action == 'payment_settings':
            p_form = PaymentSettingsForm(request.POST, request.FILES, instance=settings_obj)
            if p_form.is_valid():
                p_form.save()
                messages.success(request, "UPI and Payment details updated!")
        elif action == 'whatsapp_settings':
            w_form = WhatsAppSettingsForm(request.POST, instance=settings_obj)
            if w_form.is_valid():
                w_form.save()
                messages.success(request, "WhatsApp API credentials updated!")
        elif action == 'recovery_rules':
            r_form = RecoveryRulesForm(request.POST, instance=settings_obj)
            if r_form.is_valid():
                r_form.save()
                messages.success(request, "Automatic Recovery Rules updated!")
        elif action == 'late_fees':
            l_form = LateFeeSettingsForm(request.POST, instance=settings_obj)
            if l_form.is_valid():
                l_form.save()
                messages.success(request, "Late Fee & Interest Rules updated!")
        elif action == 'ai_settings':
            ai_form = AISettingsForm(request.POST, instance=settings_obj)
            if ai_form.is_valid():
                ai_form.save()
                messages.success(request, "AI API Provider credentials updated!")
        elif action == 'save_template':
            t_id = request.POST.get('template_id')
            title = request.POST.get('title')
            content = request.POST.get('content')
            trigger = request.POST.get('trigger_type')
            
            if t_id:
                tpl = WhatsAppMessageTemplate.objects.filter(pk=t_id, business=business).first()
                if tpl:
                    tpl.title = title
                    tpl.content = content
                    tpl.trigger_type = trigger
                    tpl.save()
            else:
                WhatsAppMessageTemplate.objects.create(
                    business=business,
                    title=title,
                    content=content,
                    trigger_type=trigger
                )
            messages.success(request, "WhatsApp Message Template saved!")

        return redirect('settings_app:index')

class TestAIConnectionView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        settings_obj, _ = BusinessSettings.objects.get_or_create(business=business)
        
        # Optionally update settings from POST if sent
        provider = request.POST.get('ai_provider')
        key = request.POST.get('ai_api_key')
        model = request.POST.get('ai_model_name')
        
        if provider:
            settings_obj.ai_provider = provider
        if key:
            settings_obj.ai_api_key = key
        if model:
            settings_obj.ai_model_name = model
        settings_obj.save()

        res = test_llm_connection(settings_obj)
        return JsonResponse(res)
