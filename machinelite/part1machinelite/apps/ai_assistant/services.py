from django.db.models import Sum, Avg, Count, F, Q
from apps.machines.models import Machine
from apps.fuel.models import FuelLog
from apps.maintenance.models import MaintenanceLog
from apps.finance.models import RevenueLog, ExpenseLog
from apps.documents.models import MachineDocument
from datetime import date, timedelta

class AIAssistantEngine:
    def __init__(self, organization):
        self.org = organization

    def ask(self, query):
        q = query.lower().strip()

        if "profitable" in q or "profit" in q or "best machine" in q or "top machine" in q:
            return self.get_most_profitable_analysis()
        elif "idle" in q or "unused" in q or "available" in q:
            return self.get_idle_machines_analysis()
        elif "maintenance" in q or "service" in q or "upcoming" in q or "breakdown" in q:
            return self.get_maintenance_analysis()
        elif "fuel" in q or "abnormal" in q or "diesel" in q or "consumption" in q:
            return self.get_fuel_efficiency_analysis()
        elif "cost" in q or "monthly" in q or "expense" in q or "spending" in q:
            return self.get_monthly_cost_analysis()
        elif "repair" in q or "replace" in q or "sell" in q or "old" in q:
            return self.get_repair_vs_replace_recommendation()
        elif "document" in q or "expiry" in q or "permit" in q or "insurance" in q:
            return self.get_document_expiry_analysis()
        else:
            return self.get_general_summary()

    def get_most_profitable_analysis(self):
        machines = Machine.objects.filter(organization=self.org)
        machine_stats = []
        for m in machines:
            rev = RevenueLog.objects.filter(organization=self.org, machine=m).aggregate(s=Sum('amount'))['s'] or 0
            fuel_exp = FuelLog.objects.filter(organization=self.org, machine=m).aggregate(s=Sum('total_cost'))['s'] or 0
            maint_exp = MaintenanceLog.objects.filter(organization=self.org, machine=m).aggregate(s=Sum('cost'))['s'] or 0
            other_exp = ExpenseLog.objects.filter(organization=self.org, machine=m).exclude(category='fuel').exclude(category='maintenance').aggregate(s=Sum('amount'))['s'] or 0
            
            total_exp = float(fuel_exp) + float(maint_exp) + float(other_exp)
            net_profit = float(rev) - total_exp
            machine_stats.append({
                'machine': m,
                'revenue': float(rev),
                'expenses': total_exp,
                'net_profit': net_profit,
                'margin': (net_profit / float(rev) * 100) if rev > 0 else 0
            })

        machine_stats.sort(key=lambda x: x['net_profit'], reverse=True)
        if not machine_stats:
            return {"answer": "No fleet machines registered yet."}

        top = machine_stats[0]
        curr = self.org.currency_symbol
        
        details = [f"• **{m['machine'].name}**: Net Profit {curr}{m['net_profit']:,.2f} (Rev: {curr}{m['revenue']:,.2f}, Exp: {curr}{m['expenses']:,.2f})" for m in machine_stats[:3]]
        
        answer = (
            f"🏆 **Top Profitable Equipment**: **{top['machine'].name}** ({top['machine'].reg_number})\n\n"
            f"It generated a total net profit of **{curr}{top['net_profit']:,.2f}** with a profit margin of **{top['margin']:.1f}%**.\n\n"
            f"**Top Fleet Earners Ranking**:\n" + "\n".join(details)
        )
        return {"answer": answer, "data": machine_stats[:5]}

    def get_idle_machines_analysis(self):
        idle_machines = Machine.objects.filter(organization=self.org, status='idle')
        curr = self.org.currency_symbol
        count = idle_machines.count()
        if count == 0:
            return {"answer": "✅ Excellent! None of your heavy machines are currently sitting idle. All active equipment is deployed or earning rental income."}

        details = [f"• **{m.name}** ({m.get_category_display()}) - Current Meter: {m.current_meter} {m.unit_label} - Rental Rate: {curr}{m.daily_rate}/day" for m in idle_machines]
        answer = (
            f"⚠️ You currently have **{count} idle equipment unit(s)** sitting in yard without active project allocation:\n\n"
            + "\n".join(details) + "\n\n"
            f"💡 *Recommendation*: Allocate these units to upcoming construction jobs or list them on rental contracts to avoid revenue leakage."
        )
        return {"answer": answer}

    def get_maintenance_analysis(self):
        machines = Machine.objects.filter(organization=self.org)
        due_list = []
        for m in machines:
            last_maint = MaintenanceLog.objects.filter(organization=self.org, machine=m).order_by('-date').first()
            if last_maint and last_maint.next_service_meter:
                remaining = last_maint.next_service_meter - m.current_meter
                if remaining <= 50:
                    due_list.append((m, remaining, last_maint.next_service_meter))

        breakdowns = Machine.objects.filter(organization=self.org, status='breakdown')
        curr = self.org.currency_symbol

        answer_parts = []
        if breakdowns.exists():
            b_names = ", ".join([b.name for b in breakdowns])
            answer_parts.append(f"🔴 **CRITICAL DOWNTIME**: Machines currently under breakdown: **{b_names}**.")

        if due_list:
            due_details = [f"• **{m.name}**: Current {m.current_meter} {m.unit_label} (Service due at {target} {m.unit_label} → **{rem:.1f} {m.unit_label} remaining**)" for m, rem, target in due_list]
            answer_parts.append("🛠️ **Upcoming Scheduled Maintenance**:\n" + "\n".join(due_details))
        else:
            answer_parts.append("✅ All equipment service schedules are up to date.")

        return {"answer": "\n\n".join(answer_parts)}

    def get_fuel_efficiency_analysis(self):
        abnormal_logs = FuelLog.objects.filter(organization=self.org, is_abnormal_flag=True)
        curr = self.org.currency_symbol

        if not abnormal_logs.exists():
            avg_eff = FuelLog.objects.filter(organization=self.org).aggregate(a=Avg('efficiency_rate'))['a'] or 0
            return {"answer": f"⛽ **Fuel Monitoring Clean**: No abnormal fuel consumption spikes or diesel theft indicators flagged across your fleet. Average fleet efficiency is **{avg_eff:.2f} L/Hr**."}

        details = [f"• **{f.machine.name}** on {f.date}: **{f.efficiency_rate} L/Hr** ({f.fuel_liters}L filled for {f.hours_run_since_last} operating hours)" for f in abnormal_logs[:5]]
        answer = (
            f"🚨 **Abnormal Fuel Consumption Alert**: Detected **{abnormal_logs.count()} refuel entries** exceeding baseline efficiency thresholds:\n\n"
            + "\n".join(details) + "\n\n"
            f"💡 *Action*: Inspect fuel tank seals, check engine injector timing, or audit driver logbook for potential fuel siphoning."
        )
        return {"answer": answer}

    def get_monthly_cost_analysis(self):
        fuel_tot = FuelLog.objects.filter(organization=self.org).aggregate(s=Sum('total_cost'))['s'] or 0
        maint_tot = MaintenanceLog.objects.filter(organization=self.org).aggregate(s=Sum('cost'))['s'] or 0
        exp_tot = ExpenseLog.objects.filter(organization=self.org).aggregate(s=Sum('amount'))['s'] or 0
        rev_tot = RevenueLog.objects.filter(organization=self.org).aggregate(s=Sum('amount'))['s'] or 0

        curr = self.org.currency_symbol
        total_costs = float(fuel_tot) + float(maint_tot) + float(exp_tot)
        net_profit = float(rev_tot) - total_costs

        answer = (
            f"📊 **Fleet Financial Summary**:\n\n"
            f"• **Total Revenue**: **{curr}{float(rev_tot):,.2f}**\n"
            f"• **Fuel Expenses**: {curr}{float(fuel_tot):,.2f}\n"
            f"• **Maintenance & Repairs**: {curr}{float(maint_tot):,.2f}\n"
            f"• **Other Operating Costs**: {curr}{float(exp_tot):,.2f}\n"
            f"───────────────────────\n"
            f"• **Total Fleet Costs**: **{curr}{total_costs:,.2f}**\n"
            f"• **Net Operating Profit**: **{curr}{net_profit:,.2f}**"
        )
        return {"answer": answer}

    def get_repair_vs_replace_recommendation(self):
        machines = Machine.objects.filter(organization=self.org)
        recs = []
        curr = self.org.currency_symbol
        for m in machines:
            cum_maint = MaintenanceLog.objects.filter(organization=self.org, machine=m).aggregate(s=Sum('cost'))['s'] or 0
            ratio = (float(cum_maint) / float(m.estimated_value) * 100) if m.estimated_value > 0 else 0
            if ratio >= 25.0:
                recs.append((m, float(cum_maint), float(m.estimated_value), ratio))

        if not recs:
            return {"answer": "✅ All equipment assets are financially healthy. Cumulative maintenance costs across all machines remain well below asset replacement thresholds."}

        details = []
        for m, maint, val, r in recs:
            action = "🔴 **RECOMMEND REPLACEMENT / AUCTION**" if r > 40 else "⚠️ **HIGH REPAIR EXPENSE - MONITOR**"
            details.append(f"• **{m.name}** ({m.make_model}): Cumulative Repairs: {curr}{maint:,.2f} vs Valuation: {curr}{val:,.2f} (**{r:.1f}% repair-to-value ratio**) → {action}")

        answer = (
            f"🔄 **Repair vs Replace Lifecycle Audit**:\n\n"
            + "\n".join(details) + "\n\n"
            f"💡 *Enterprise Rule*: When cumulative maintenance exceeds 35-40% of current asset resale value, replacing with a newer low-breakdown unit yields higher overall fleet ROI."
        )
        return {"answer": answer}

    def get_document_expiry_analysis(self):
        expired = MachineDocument.objects.filter(organization=self.org, expiry_date__lt=date.today())
        expiring_soon = MachineDocument.objects.filter(organization=self.org, expiry_date__gte=date.today(), expiry_date__lte=date.today() + timedelta(days=30))

        parts = []
        if expired.exists():
            e_list = [f"• **{d.title}** ({d.doc_number}) for {d.machine.name if d.machine else 'Operator'} - Expired {d.expiry_date}" for d in expired]
            parts.append("🚨 **EXPIRED COMPLIANCE DOCUMENTS (Immediate Penalty Risk)**:\n" + "\n".join(e_list))

        if expiring_soon.exists():
            s_list = [f"• **{d.title}** for {d.machine.name if d.machine else 'Operator'} - Expiring on {d.expiry_date} ({d.days_remaining} days left)" for d in expiring_soon]
            parts.append("⚠️ **Expiring Within 30 Days**:\n" + "\n".join(s_list))

        if not parts:
            return {"answer": "✅ All machine RCs, insurance policies, permits, PUCs, and operator licenses are valid and compliant."}

        return {"answer": "\n\n".join(parts)}

    def get_general_summary(self):
        m_count = Machine.objects.filter(organization=self.org).count()
        working = Machine.objects.filter(organization=self.org, status='working').count()
        idle = Machine.objects.filter(organization=self.org, status='idle').count()
        curr = self.org.currency_symbol
        rev = RevenueLog.objects.filter(organization=self.org).aggregate(s=Sum('amount'))['s'] or 0

        answer = (
            f"🤖 **Machine OS Intelligence Assistant Ready**\n\n"
            f"I have direct access to your fleet live data ({m_count} equipment units, {working} working, {idle} idle, Total Revenue: {curr}{float(rev):,.2f}).\n\n"
            f"You can ask me questions like:\n"
            f"• *Which machine is most profitable?*\n"
            f"• *Which machines are sitting idle?*\n"
            f"• *What maintenance is due soon?*\n"
            f"• *Any abnormal fuel consumption flags?*\n"
            f"• *Monthly cost and expense breakdown?*\n"
            f"• *Repair-vs-replace recommendations?*\n"
            f"• *Document & permit expiry status?*"
        )
        return {"answer": answer}
