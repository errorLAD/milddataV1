import json
import datetime
from django.utils import timezone
from .models import AIBusinessInsightCache, AIAdvisorQueryLog
from .analytics import (
    get_date_bounds, build_structured_analytics_payload,
    get_business_health_summary, get_udhaar_recovery_insights,
    get_todays_priority_contacts, get_sales_velocity_and_slow_inventory,
    get_restock_recommendations
)
from .llm_provider import call_llm_api

def generate_business_insights(business, period_code='30_days', custom_start=None, custom_end=None, force_refresh=False):
    """
    Retrieves cached business insights or computes structured analytics payload.
    """
    cache_entry = AIBusinessInsightCache.objects.filter(business=business, date_range_code=period_code).first()

    if cache_entry and not force_refresh:
        age_seconds = (timezone.now() - cache_entry.last_analyzed_at).total_seconds()
        if age_seconds < 3600 and cache_entry.insight_json:
            return cache_entry.insight_json

    start_date, end_date = get_date_bounds(period_code, custom_start, custom_end)
    payload = build_structured_analytics_payload(business, start_date, end_date)

    # Optional LLM Enhancement if configured
    try:
        from settings_app.models import BusinessSettings
        b_settings = BusinessSettings.objects.filter(business=business).first()
        if b_settings and b_settings.is_ai_enabled and b_settings.ai_api_key:
            system_prompt = (
                "You are an expert AI Business Advisor for an Indian Kirana/SMB store. "
                "Analyze the provided structured CRM database context. "
                "Provide a concise, 2-sentence executive summary of business health, highlight key risks, and recommend 2 immediate actions. "
                "Never invent numbers or facts not present in the data."
            )
            user_prompt = f"BUSINESS CRM ANALYTICS CONTEXT:\n{json.dumps(payload, indent=2)}"
            llm_summary = call_llm_api(b_settings, system_prompt, user_prompt)
            if llm_summary and len(llm_summary.strip()) > 10:
                payload['business_health']['summary'] = f"[AI Generated ({b_settings.get_ai_provider_display()})]: {llm_summary.strip()}"
    except Exception:
        # Fall back gracefully to standard ORM computed summary
        pass

    # Save to cache
    if not cache_entry:
        cache_entry = AIBusinessInsightCache(
            business=business,
            date_range_code=period_code
        )
    
    cache_entry.health_status = payload['business_health']['status']
    cache_entry.health_summary = payload['business_health']['summary']
    cache_entry.insight_json = payload
    cache_entry.save()

    return payload

def answer_business_question(business, question_text):
    """
    Answers B2B Collections questions using real DB analytics context + optional LLM integration.
    Tailored for payment collections, accounts receivable recovery, and customer payment behavior.
    """
    text = question_text.lower().strip()
    today = timezone.now().date()
    start_date = today - datetime.timedelta(days=30)

    payload = build_structured_analytics_payload(business, start_date, today)

    # Try LLM API first if configured
    llm_answer = None
    try:
        from settings_app.models import BusinessSettings
        b_settings = BusinessSettings.objects.filter(business=business).first()
        if b_settings and b_settings.is_ai_enabled and b_settings.ai_api_key:
            system_prompt = (
                "You are an expert AI B2B Collections & Accounts Receivable Assistant for KarobarPlus. "
                "Your primary goal is to help the business owner collect pending B2B payments faster. "
                "Use ONLY the provided CRM database analytics payload to answer the owner's question. "
                "Format your answer clearly with: "
                "Recommendation: ... | Key Data: ... | Action: ... "
                "Never invent numbers, customers, sales, or payments."
            )
            user_prompt = f"STORE ANALYTICS DATA:\n{json.dumps(payload, indent=2)}\n\nCOLLECTIONS QUERY:\n{question_text}"
            llm_reply = call_llm_api(b_settings, system_prompt, user_prompt)
            if llm_reply and len(llm_reply.strip()) > 15:
                llm_answer = f"🤖 [AI Collections Assistant ({b_settings.get_ai_provider_display()})]:\n{llm_reply.strip()}"
    except Exception:
        pass

    if llm_answer:
        resp = llm_answer
        link_url = "/collections/"
        link_text = "Open Collections Workspace"
    else:
        # High-accuracy rule-based B2B collections parser
        from udhaar.models import Udhaar
        from customers.models import Customer
        from payments.models import Payment

        active_udhaars = Udhaar.objects.filter(business=business).exclude(status='Paid')
        overdue_udhaars = active_udhaars.filter(due_date__lt=today)

        if any(k in text for k in ['who', 'contact', 'call', 'today', 'follow up', 'priority']):
            priorities = overdue_udhaars.order_by('due_date', '-remaining_amount')[:5]
            count = overdue_udhaars.count()
            total_amt = sum(float(u.remaining_amount) for u in overdue_udhaars)
            if priorities.exists():
                top = priorities.first()
                p_list = ", ".join([f"**{u.customer.name}** (₹{u.remaining_amount:,.0f} — {u.days_overdue}d overdue)" for u in priorities[:3]])
                resp = (
                    f"You should follow up with **{count} customers** today.\n\n"
                    f"💰 **Total outstanding from these customers:** ₹{total_amt:,.0f}\n\n"
                    f"🎯 **Highest priority:** {top.customer.name} — ₹{top.remaining_amount:,.0f} overdue for {top.days_overdue} days"
                    f"{' with ' + str(top.customer.promises_broken_count) + ' missed promises' if top.customer.promises_broken_count else ''}.\n\n"
                    f"Top accounts to contact: {p_list}."
                )
            else:
                resp = "✅ All priority customer accounts are currently up to date! No urgent collection contacts required today."
            link_url = "/collections/?tab=due_today"
            link_text = "View Today's Priority Follow-ups"

        elif any(k in text for k in ['missed', 'broken', 'promise']):
            missed_qs = active_udhaars.filter(promise_broken=True)
            cnt = missed_qs.count()
            if cnt > 0:
                m_names = ", ".join([f"**{u.customer.name}** (₹{u.remaining_amount:,.0f})" for u in missed_qs[:3]])
                resp = (
                    f"⚠️ There are **{cnt} customer(s)** with missed payment promises.\n\n"
                    f"Accounts requiring immediate follow-up: {m_names}.\n\n"
                    f"Action: Call or send a firm WhatsApp reminder to reschedule or collect payment immediately."
                )
            else:
                resp = "✅ No missed payment promises recorded! All customer promises are in good standing."
            link_url = "/collections/?tab=missed"
            link_text = "View Missed Promises"

        elif any(k in text for k in ['week', 'potential', 'forecast', 'expected']):
            next_7 = today + datetime.timedelta(days=7)
            due_week = active_udhaars.filter(due_date__lte=next_7)
            week_amt = sum(float(u.remaining_amount) for u in due_week)
            resp = (
                f"📊 **Collection Forecast for this Week:**\n\n"
                f"Potential collections maturing this week: **₹{week_amt:,.0f}** across {due_week.count()} invoices.\n\n"
                f"Action: Send pre-due reminders 3 days before maturity to maximize on-time recovery."
            )
            link_url = "/collections/?tab=upcoming"
            link_text = "View Upcoming Maturities"

        elif any(k in text for k in ['highest', 'largest', 'most overdue', 'biggest']):
            top_overdue = overdue_udhaars.order_by('-remaining_amount')[:5]
            if top_overdue.exists():
                lines = [f"• **{u.customer.name}**: ₹{u.remaining_amount:,.0f} ({u.days_overdue} days overdue)" for u in top_overdue]
                resp = (
                    f"🚨 **Highest Overdue Accounts:**\n\n" + "\n".join(lines) +
                    f"\n\nAction: Initiate escalation or offer structured payment plans for balances exceeding ₹50,000."
                )
            else:
                resp = "No overdue accounts found."
            link_url = "/collections/?tab=overdue"
            link_text = "View Overdue List"

        elif any(k in text for k in ['draft', 'template', 'reminder', 'message']):
            resp = (
                f"📝 **Recommended WhatsApp Collection Templates:**\n\n"
                f"1. **Friendly:** *'Hello {{customer_name}}, your payment of {{amount}} is pending. Please let us know your expected payment date. Thank you!'*\n\n"
                f"2. **Professional:** *'Payment reminder: {{amount}} against invoice #{{invoice_number}} is currently overdue. Kindly arrange payment at the earliest.'*\n\n"
                f"3. **Hindi/Hinglish:** *'Namaste {{customer_name}} ji, ₹{{amount}} ka payment pending hai. Kripya payment ki expected date bata dein.'*"
            )
            link_url = "/collections/reminder-rules/"
            link_text = "Configure Reminder Templates"

        elif any(k in text for k in ['late', 'frequent', 'behavior', 'delay', 'risk']):
            high_risk = Customer.objects.filter(business=business, promises_broken_count__gt=0).order_by('-promises_broken_count')[:5]
            if high_risk.exists():
                r_names = ", ".join([f"**{c.name}** ({c.promises_broken_count} missed promises)" for c in high_risk])
                resp = (
                    f"⚠️ **Customers Frequently Delaying Payments:**\n\n{r_names}.\n\n"
                    f"Recommendation: Reduce credit limit for these accounts and enforce partial upfront advance payments."
                )
            else:
                resp = "No chronic late payers detected. Most customers are paying on time."
            link_url = "/customers/"
            link_text = "View Customers"

        else:
            u_sum = payload['udhaar_summary']
            resp = (
                f"📊 **B2B Collections Summary:**\n\n"
                f"• Total Outstanding: **₹{u_sum['total_outstanding']:,.0f}**\n"
                f"• Total Overdue: **₹{u_sum['total_overdue']:,.0f}**\n"
                f"• Broken Promises: **{u_sum['broken_promises_cnt']}**\n\n"
                f"Recommendation: Focus on accounts overdue past 15 days first to protect operating cash flow."
            )
            link_url = "/collections/"
            link_text = "Open Collections Workspace"

    # Log query
    AIAdvisorQueryLog.objects.create(
        business=business,
        question=question_text,
        answer=resp
    )

    return {
        'question': question_text,
        'answer': resp,
        'link_url': link_url,
        'link_text': link_text
    }

