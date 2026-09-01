from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from apps.suppliers.views import (
    dashboard_view, suppliers_list_view, add_supplier_wizard_view,
    supplier_invitation_sent_view, supplier_detail_view
)
from apps.documents.views import documents_list_view, document_detail_view
from apps.approvals.views import approvals_list_view, approval_detail_view
from apps.compliance.views import compliance_center_view
from apps.portal.views import supplier_portal_view, portal_upload_document_view
from apps.core.views import (
    login_view, register_view, guest_login_view, logout_view,
    templates_list_view, notifications_list_view, activity_log_view,
    global_search_view, reports_view, settings_view
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Authentication & Guest Access Routes
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('guest-login/', guest_login_view, name='guest_login'),
    path('logout/', logout_view, name='logout'),

    # Dashboard / Overview
    path('', dashboard_view, name='dashboard'),

    # Suppliers
    path('suppliers/', suppliers_list_view, name='suppliers_list'),
    path('suppliers/add/', add_supplier_wizard_view, name='add_supplier'),
    path('suppliers/invited/<uuid:supplier_id>/', supplier_invitation_sent_view, name='supplier_invitation_sent'),
    path('suppliers/<uuid:supplier_id>/', supplier_detail_view, name='supplier_detail'),

    # Documents
    path('documents/', documents_list_view, name='documents_list'),
    path('documents/<uuid:doc_id>/', document_detail_view, name='document_detail'),

    # Approvals Workflow
    path('approvals/', approvals_list_view, name='approvals_list'),
    path('approvals/<uuid:approval_id>/', approval_detail_view, name='approval_detail'),

    # Compliance Center
    path('compliance/', compliance_center_view, name='compliance_center'),

    # Configuration & System
    path('templates/', templates_list_view, name='templates_list'),
    path('notifications/', notifications_list_view, name='notifications_list'),
    path('activity/', activity_log_view, name='activity_log'),
    path('search/', global_search_view, name='global_search'),
    path('reports/', reports_view, name='reports'),
    path('settings/', settings_view, name='settings'),

    # Supplier Portal (Isolated View)
    path('portal/<str:token>/', supplier_portal_view, name='portal_view'),
    path('portal/<str:token>/upload/<uuid:doc_id>/', portal_upload_document_view, name='portal_upload_doc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
