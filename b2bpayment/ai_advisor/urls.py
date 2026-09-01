from django.urls import path
from .views import (
    AdvisorDashboardView, RefreshAIAnalysisView, AskAIQuestionView,
    CustomerRiskView, ProductInsightsView, BusinessProblemsView
)

app_name = 'ai_advisor'

urlpatterns = [
    path('', AdvisorDashboardView.as_view(), name='dashboard'),
    path('refresh/', RefreshAIAnalysisView.as_view(), name='refresh'),
    path('ask/', AskAIQuestionView.as_view(), name='ask'),
    path('ask-question/', AskAIQuestionView.as_view(), name='ask_question'),
    path('customer-risk/', CustomerRiskView.as_view(), name='customer_risk'),
    path('product-insights/', ProductInsightsView.as_view(), name='product_insights'),
    path('problems/', BusinessProblemsView.as_view(), name='problems'),
]
