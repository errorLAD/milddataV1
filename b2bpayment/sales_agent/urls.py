from django.urls import path
from .views import (
    DashboardView, ApproveDraftOrderView, RejectDraftOrderView,
    ImportBlastView, ConfirmImportView, SendBlastView,
    BlastHistoryListView, SalesAgentSettingsView,
    TemplateListView, TemplateSaveView, TemplateToggleActiveView, TemplateDeleteView
)

app_name = 'sales_agent'

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('draft-order/<int:pk>/approve/', ApproveDraftOrderView.as_view(), name='approve_draft'),
    path('draft-order/<int:pk>/reject/', RejectDraftOrderView.as_view(), name='reject_draft'),
    path('import-blast/', ImportBlastView.as_view(), name='import_blast'),
    path('import-blast/confirm/', ConfirmImportView.as_view(), name='confirm_import'),
    path('send-blast/', SendBlastView.as_view(), name='send_blast'),
    path('blast-history/', BlastHistoryListView.as_view(), name='blast_history'),
    path('settings/', SalesAgentSettingsView.as_view(), name='settings'),
    path('templates/', TemplateListView.as_view(), name='templates_list'),
    path('templates/save/', TemplateSaveView.as_view(), name='template_save'),
    path('templates/<int:pk>/toggle/', TemplateToggleActiveView.as_view(), name='template_toggle'),
    path('templates/<int:pk>/delete/', TemplateDeleteView.as_view(), name='template_delete'),
]
