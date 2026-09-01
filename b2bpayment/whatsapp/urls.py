from django.urls import path
from .views import (
    WhatsAppInboxView, SendMessageView, ToggleHumanTakeoverView,
    SendPaymentLinkView, WhatsAppWebhookView, WhatsAppSandboxView,
    CampaignListView, CampaignCreateView
)

app_name = 'whatsapp'

urlpatterns = [
    path('', WhatsAppInboxView.as_view(), name='inbox'),
    path('send/<int:conv_id>/', SendMessageView.as_view(), name='send'),
    path('toggle-takeover/<int:conv_id>/', ToggleHumanTakeoverView.as_view(), name='toggle_takeover'),
    path('send-link/<int:conv_id>/', SendPaymentLinkView.as_view(), name='send_link'),
    path('webhook/', WhatsAppWebhookView.as_view(), name='webhook'),
    path('sandbox/', WhatsAppSandboxView.as_view(), name='sandbox'),
    path('campaigns/', CampaignListView.as_view(), name='campaign_list'),
    path('campaigns/add/', CampaignCreateView.as_view(), name='campaign_create'),
]
