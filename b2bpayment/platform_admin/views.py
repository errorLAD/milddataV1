from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone

from accounts.models import Business, UserProfile
from customers.models import Customer
from products.models import Product
from sales.models import Sale, SaleItem
from udhaar.models import Udhaar
from payments.models import Payment
from whatsapp.models import WhatsAppConversation, WhatsAppMessage, WhatsAppMessageTemplate
from sales_agent.models import DraftOrder, SalesBlastHistory, SalesAgentSettings

class SuperuserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not (request.user.is_superuser or request.user.is_staff):
            raise PermissionDenied("Platform Admin privileges required.")
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(SuperuserRequiredMixin, View):
    def get(self, request):
        total_businesses = Business.objects.count()
        active_businesses = Business.objects.filter(is_active=True).count()
        blocked_businesses = Business.objects.filter(is_active=False).count()

        total_products = Product.objects.count()
        total_customers = Customer.objects.count()
        total_transactions = Payment.objects.count()
        
        total_revenue = Sale.objects.aggregate(s=Sum('total_amount'))['s'] or 0
        total_udhaar = Udhaar.objects.exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0
        total_orders = DraftOrder.objects.count() + Sale.objects.count()

        total_whatsapp_sent = WhatsAppMessage.objects.count()
        total_ai_replies = WhatsAppMessage.objects.filter(sender='system').count()
        total_ai_conversations = WhatsAppConversation.objects.count()

        # AI Sales & Recovery Metrics
        ai_sales_convs = WhatsAppConversation.objects.filter(conversation_type='sales').count()
        ai_recovery_convs = WhatsAppConversation.objects.filter(conversation_type='recovery').count()

        ai_leads_generated = WhatsAppConversation.objects.filter(conversation_type='sales').values('customer').distinct().count()
        ai_customers_contacted = WhatsAppConversation.objects.values('customer').distinct().count()

        ai_sales_approved = DraftOrder.objects.filter(status='Approved')
        ai_sales_count = ai_sales_approved.count()
        ai_sales_revenue = ai_sales_approved.aggregate(s=Sum('total_amount'))['s'] or 0

        # Udhaar Recovered through AI
        ai_recovery_msgs_count = WhatsAppMessage.objects.filter(conversation__conversation_type='recovery', sender='system').count()
        ai_recovered_payments = Payment.objects.filter(
            Q(notes__icontains='AI') | Q(customer__whatsapp_conversations__conversation_type='recovery')
        ).distinct()
        ai_recovered_amount = ai_recovered_payments.aggregate(s=Sum('amount'))['s'] or 0

        conversion_rate = round((ai_sales_count / ai_sales_convs * 100), 1) if ai_sales_convs > 0 else 0
        recovery_rate = round((float(ai_recovered_amount) / float(total_udhaar) * 100), 1) if total_udhaar > 0 else 0

        recent_businesses = Business.objects.order_by('-created_at')[:5]

        return render(request, 'platform_admin/dashboard.html', {
            'total_businesses': total_businesses,
            'active_businesses': active_businesses,
            'blocked_businesses': blocked_businesses,
            'total_products': total_products,
            'total_customers': total_customers,
            'total_transactions': total_transactions,
            'total_revenue': total_revenue,
            'total_udhaar': total_udhaar,
            'total_orders': total_orders,
            'total_whatsapp_sent': total_whatsapp_sent,
            'total_ai_replies': total_ai_replies,
            'total_ai_conversations': total_ai_conversations,
            'ai_sales_convs': ai_sales_convs,
            'ai_recovery_convs': ai_recovery_convs,
            'ai_leads_generated': ai_leads_generated,
            'ai_customers_contacted': ai_customers_contacted,
            'ai_sales_count': ai_sales_count,
            'ai_sales_revenue': ai_sales_revenue,
            'ai_recovery_msgs_count': ai_recovery_msgs_count,
            'ai_recovered_amount': ai_recovered_amount,
            'conversion_rate': conversion_rate,
            'recovery_rate': recovery_rate,
            'recent_businesses': recent_businesses,
        })

class BusinessListView(SuperuserRequiredMixin, View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        status_filter = request.GET.get('status', 'all')
        sort_by = request.GET.get('sort', 'date_desc')

        businesses = Business.objects.all()

        if query:
            businesses = businesses.filter(
                Q(name__icontains=query) |
                Q(owner_name__icontains=query) |
                Q(phone__icontains=query) |
                Q(email__icontains=query)
            )

        if status_filter == 'active':
            businesses = businesses.filter(is_active=True)
        elif status_filter == 'blocked':
            businesses = businesses.filter(is_active=False)

        # Build list of business dicts with real computed DB metrics
        business_data = []
        for b in businesses:
            rev = Sale.objects.filter(business=b).aggregate(s=Sum('total_amount'))['s'] or 0
            sales_cnt = Sale.objects.filter(business=b).count()
            udh_amt = Udhaar.objects.filter(business=b).exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0
            prod_cnt = Product.objects.filter(business=b).count()
            cust_cnt = Customer.objects.filter(business=b).count()
            tx_cnt = Payment.objects.filter(business=b).count()
            orders_cnt = DraftOrder.objects.filter(business=b).count() + sales_cnt
            wa_sent = WhatsAppMessage.objects.filter(conversation__business=b).count()
            ai_replies = WhatsAppMessage.objects.filter(conversation__business=b, sender='system').count()

            business_data.append({
                'obj': b,
                'revenue': rev,
                'sales_count': sales_cnt,
                'udhaar_amount': udh_amt,
                'products_count': prod_cnt,
                'customers_count': cust_cnt,
                'transactions_count': tx_cnt,
                'orders_count': orders_cnt,
                'whatsapp_sent': wa_sent,
                'ai_replies': ai_replies,
            })

        # Sorting
        if sort_by == 'date_asc':
            business_data.sort(key=lambda x: x['obj'].created_at)
        elif sort_by == 'revenue_desc':
            business_data.sort(key=lambda x: x['revenue'], reverse=True)
        elif sort_by == 'udhaar_desc':
            business_data.sort(key=lambda x: x['udhaar_amount'], reverse=True)
        elif sort_by == 'sales_desc':
            business_data.sort(key=lambda x: x['sales_count'], reverse=True)
        elif sort_by == 'name_asc':
            business_data.sort(key=lambda x: x['obj'].name.lower())
        else:
            # Default: date_desc
            business_data.sort(key=lambda x: x['obj'].created_at, reverse=True)

        return render(request, 'platform_admin/business_list.html', {
            'business_data': business_data,
            'query': query,
            'status_filter': status_filter,
            'sort_by': sort_by,
        })

class BusinessDetailView(SuperuserRequiredMixin, View):
    def get(self, request, pk):
        business = get_object_or_404(Business, pk=pk)

        revenue = Sale.objects.filter(business=business).aggregate(s=Sum('total_amount'))['s'] or 0
        sales_count = Sale.objects.filter(business=business).count()
        udhaar_amount = Udhaar.objects.filter(business=business).exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 0
        
        products_count = Product.objects.filter(business=business).count()
        customers_count = Customer.objects.filter(business=business).count()
        transactions_count = Payment.objects.filter(business=business).count()
        draft_orders_count = DraftOrder.objects.filter(business=business).count()

        wa_conversations = WhatsAppConversation.objects.filter(business=business)
        wa_messages_count = WhatsAppMessage.objects.filter(conversation__business=business).count()
        ai_replies_count = WhatsAppMessage.objects.filter(conversation__business=business, sender='system').count()

        ai_sales_approved = DraftOrder.objects.filter(business=business, status='Approved')
        ai_sales_count = ai_sales_approved.count()
        ai_sales_revenue = ai_sales_approved.aggregate(s=Sum('total_amount'))['s'] or 0

        # Detailed Lists
        recent_sales = Sale.objects.filter(business=business).order_by('-sale_date')[:10]
        recent_udhaars = Udhaar.objects.filter(business=business).order_by('-created_at')[:10]
        recent_drafts = DraftOrder.objects.filter(business=business).order_by('-created_at')[:10]
        top_products = Product.objects.filter(business=business).order_by('-stock_quantity')[:10]
        recent_payments = Payment.objects.filter(business=business).order_by('-created_at')[:10]

        return render(request, 'platform_admin/business_detail.html', {
            'business': business,
            'revenue': revenue,
            'sales_count': sales_count,
            'udhaar_amount': udhaar_amount,
            'products_count': products_count,
            'customers_count': customers_count,
            'transactions_count': transactions_count,
            'draft_orders_count': draft_orders_count,
            'wa_conversations_count': wa_conversations.count(),
            'wa_messages_count': wa_messages_count,
            'ai_replies_count': ai_replies_count,
            'ai_sales_count': ai_sales_count,
            'ai_sales_revenue': ai_sales_revenue,
            'recent_sales': recent_sales,
            'recent_udhaars': recent_udhaars,
            'recent_drafts': recent_drafts,
            'top_products': top_products,
            'recent_payments': recent_payments,
        })

class BlockBusinessView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        business.is_active = False
        business.save()
        messages.warning(request, f"Business '{business.name}' has been BLOCKED / SUSPENDED.")
        return redirect('platform_admin:business_list')

class UnblockBusinessView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        business.is_active = True
        business.save()
        messages.success(request, f"Business '{business.name}' has been RESTORED to Active status.")
        return redirect('platform_admin:business_list')

class DeleteBusinessView(SuperuserRequiredMixin, View):
    def post(self, request, pk):
        business = get_object_or_404(Business, pk=pk)
        b_name = business.name
        business.delete()
        messages.success(request, f"Business '{b_name}' has been deleted permanently.")
        return redirect('platform_admin:business_list')

class AIMetricsView(SuperuserRequiredMixin, View):
    def get(self, request):
        total_ai_conversations = WhatsAppConversation.objects.count()
        sales_conversations = WhatsAppConversation.objects.filter(conversation_type='sales').count()
        recovery_conversations = WhatsAppConversation.objects.filter(conversation_type='recovery').count()

        customers_contacted = WhatsAppConversation.objects.values('customer').distinct().count()
        total_messages_sent = WhatsAppMessage.objects.count()
        total_ai_replies = WhatsAppMessage.objects.filter(sender='system').count()

        leads_generated = WhatsAppConversation.objects.filter(conversation_type='sales').values('customer').distinct().count()

        ai_sales_approved = DraftOrder.objects.filter(status='Approved')
        ai_sales_count = ai_sales_approved.count()
        ai_sales_revenue = ai_sales_approved.aggregate(s=Sum('total_amount'))['s'] or 0

        recovery_messages_sent = WhatsAppMessage.objects.filter(conversation__conversation_type='recovery', sender='system').count()
        ai_recovered_payments = Payment.objects.filter(
            Q(notes__icontains='AI') | Q(customer__whatsapp_conversations__conversation_type='recovery')
        ).distinct()
        ai_recovered_amount = ai_recovered_payments.aggregate(s=Sum('amount'))['s'] or 0

        followups_sent = WhatsAppMessage.objects.filter(sender='system', message_text__icontains='reminder').count() + Udhaar.objects.filter(last_reminder_sent__isnull=False).count()

        conversion_rate = round((ai_sales_count / sales_conversations * 100), 1) if sales_conversations > 0 else 0
        total_udhaar = Udhaar.objects.exclude(status='Paid').aggregate(s=Sum('remaining_amount'))['s'] or 1
        recovery_rate = round((float(ai_recovered_amount) / float(total_udhaar) * 100), 1) if total_udhaar > 0 else 0

        # Breakdown per Business
        business_ai_stats = []
        for b in Business.objects.all():
            b_convs = WhatsAppConversation.objects.filter(business=b).count()
            b_replies = WhatsAppMessage.objects.filter(conversation__business=b, sender='system').count()
            b_drafts = DraftOrder.objects.filter(business=b, status='Approved')
            b_sales_cnt = b_drafts.count()
            b_sales_val = b_drafts.aggregate(s=Sum('total_amount'))['s'] or 0

            business_ai_stats.append({
                'business': b,
                'conversations': b_convs,
                'ai_replies': b_replies,
                'sales_count': b_sales_cnt,
                'sales_value': b_sales_val,
            })

        return render(request, 'platform_admin/ai_metrics.html', {
            'total_ai_conversations': total_ai_conversations,
            'sales_conversations': sales_conversations,
            'recovery_conversations': recovery_conversations,
            'customers_contacted': customers_contacted,
            'total_messages_sent': total_messages_sent,
            'total_ai_replies': total_ai_replies,
            'leads_generated': leads_generated,
            'ai_sales_count': ai_sales_count,
            'ai_sales_revenue': ai_sales_revenue,
            'recovery_messages_sent': recovery_messages_sent,
            'ai_recovered_amount': ai_recovered_amount,
            'followups_sent': followups_sent,
            'conversion_rate': conversion_rate,
            'recovery_rate': recovery_rate,
            'business_ai_stats': business_ai_stats,
        })
