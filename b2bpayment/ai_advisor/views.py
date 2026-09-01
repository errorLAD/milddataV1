from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.http import JsonResponse
import datetime

from core.mixins import TenantRequiredMixin
from .services import generate_business_insights, answer_business_question
from .analytics import get_date_bounds

class AdvisorDashboardView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        period = request.GET.get('period', '30_days')
        custom_start_str = request.GET.get('start_date')
        custom_end_str = request.GET.get('end_date')

        custom_start = datetime.datetime.strptime(custom_start_str, '%Y-%m-%d').date() if custom_start_str else None
        custom_end = datetime.datetime.strptime(custom_end_str, '%Y-%m-%d').date() if custom_end_str else None

        insights = generate_business_insights(business, period, custom_start, custom_end)

        return render(request, 'ai_advisor/dashboard.html', {
            'period': period,
            'insights': insights,
            'health': insights.get('business_health', {}),
            'udhaar': insights.get('udhaar_summary', {}),
            'todays_actions': insights.get('todays_top_actions', []),
            'priority_contacts': insights.get('priority_contacts', []),
            'slow_moving': insights.get('slow_moving_products', []),
            'fast_moving': insights.get('fast_moving_products', []),
            'restock': insights.get('restock_recommendations', []),
            'profitability': insights.get('product_profitability', []),
            'customer_risks': insights.get('customer_risks', []),
            'qa_result': None
        })

class RefreshAIAnalysisView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        period = request.POST.get('period', '30_days')
        generate_business_insights(business, period, force_refresh=True)
        messages.success(request, "AI Business Advisor analysis refreshed with latest CRM database data!")
        return redirect(f"/ai-advisor/?period={period}")

class AskAIQuestionView(TenantRequiredMixin, View):
    def post(self, request):
        business = request.business
        question = request.POST.get('question', '').strip()
        period = request.POST.get('period', '30_days')

        if not question:
            messages.warning(request, "Please enter a question about your business.")
            return redirect(f"/ai-advisor/?period={period}")

        qa_res = answer_business_question(business, question)
        insights = generate_business_insights(business, period)

        return render(request, 'ai_advisor/dashboard.html', {
            'period': period,
            'insights': insights,
            'health': insights.get('business_health', {}),
            'udhaar': insights.get('udhaar_summary', {}),
            'todays_actions': insights.get('todays_top_actions', []),
            'priority_contacts': insights.get('priority_contacts', []),
            'slow_moving': insights.get('slow_moving_products', []),
            'fast_moving': insights.get('fast_moving_products', []),
            'restock': insights.get('restock_recommendations', []),
            'profitability': insights.get('product_profitability', []),
            'customer_risks': insights.get('customer_risks', []),
            'qa_result': qa_res
        })

class CustomerRiskView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        insights = generate_business_insights(business, '30_days')
        return render(request, 'ai_advisor/customer_risk.html', {
            'customer_risks': insights.get('customer_risks', [])
        })

class ProductInsightsView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        insights = generate_business_insights(business, '30_days')
        return render(request, 'ai_advisor/product_insights.html', {
            'fast_moving': insights.get('fast_moving_products', []),
            'slow_moving': insights.get('slow_moving_products', []),
            'restock': insights.get('restock_recommendations', []),
            'profitability': insights.get('product_profitability', [])
        })

class BusinessProblemsView(TenantRequiredMixin, View):
    def get(self, request):
        business = request.business
        insights = generate_business_insights(business, '30_days')
        problems = insights.get('udhaar_summary', {}).get('problems', [])
        return render(request, 'ai_advisor/business_problems.html', {
            'problems': problems
        })
