from datetime import date, timedelta
from django.db.models import Sum

class HealthScoreCalculator:
    """
    Calculates dynamic Machine Health Score (0-100) based on telemetry, maintenance, breakdown,
    fuel efficiency, machine age, repair costs, and compliance.
    """
    def __init__(self, machine, organization):
        self.machine = machine
        self.org = organization

    def calculate(self):
        from apps.maintenance.models import MaintenanceLog
        from apps.fuel.models import FuelLog
        from apps.documents.models import MachineDocument

        score = 100
        reasons = []
        recommendations = []
        risk_indicators = []

        # 1. Breakdown History & Downtime (Past 90 Days)
        breakdowns = MaintenanceLog.objects.filter(
            organization=self.org,
            machine=self.machine,
            is_breakdown=True
        )
        b_count = breakdowns.count()
        if b_count > 0:
            deduction = min(30, b_count * 15)
            score -= deduction
            reasons.append(f"Recorded {b_count} breakdown event(s) in history (-{deduction} pts).")
            risk_indicators.append("High Breakdown Risk")
            recommendations.append("Perform a comprehensive engine & hydraulic inspection.")

        total_downtime = breakdowns.aggregate(s=Sum('downtime_hours'))['s'] or 0
        if total_downtime > 20:
            score -= 10
            reasons.append(f"High cumulative downtime: {total_downtime} hours (-10 pts).")

        # 2. Maintenance Service Interval Status
        last_maint = MaintenanceLog.objects.filter(
            organization=self.org,
            machine=self.machine
        ).order_by('-date').first()

        if last_maint and last_maint.next_service_meter:
            overdue = self.machine.current_meter - last_maint.next_service_meter
            if overdue > 0:
                score -= 20
                reasons.append(f"Overdue for scheduled preventive service by {overdue:.1f} {self.machine.unit_label} (-20 pts).")
                risk_indicators.append("Overdue Service")
                recommendations.append("Schedule 250 HR preventive oil & filter service immediately.")
            elif (last_maint.next_service_meter - self.machine.current_meter) <= 50:
                score -= 5
                reasons.append(f"Approaching service interval ({last_maint.next_service_meter - self.machine.current_meter:.1f} {self.machine.unit_label} left) (-5 pts).")

        # 3. Abnormal Fuel Consumption Flag
        abnormal_fuel = FuelLog.objects.filter(
            organization=self.org,
            machine=self.machine,
            is_abnormal_flag=True
        ).exists()
        if abnormal_fuel:
            score -= 10
            reasons.append("Flagged for abnormal fuel consumption rate (-10 pts).")
            risk_indicators.append("Fuel Inefficiency Spike")
            recommendations.append("Inspect fuel injectors and check fuel tank seals.")

        # 4. Repair Cost to Asset Value Ratio
        cum_maint_cost = float(MaintenanceLog.objects.filter(
            organization=self.org,
            machine=self.machine
        ).aggregate(s=Sum('cost'))['s'] or 0)

        asset_val = float(self.machine.estimated_value) if self.machine.estimated_value > 0 else 3000000.0
        repair_ratio = (cum_maint_cost / asset_val) * 100

        if repair_ratio >= 35.0:
            score -= 20
            reasons.append(f"High repair-to-value ratio: {repair_ratio:.1f}% of asset value spent on repairs (-20 pts).")
            risk_indicators.append("High Maintenance Cost Asset")
            recommendations.append("Evaluate repair-vs-replace ROI; consider asset replacement.")
        elif repair_ratio >= 20.0:
            score -= 10
            reasons.append(f"Moderate repair-to-value ratio: {repair_ratio:.1f}% (-10 pts).")

        # 5. Document Compliance Expiry
        today = date.today()
        expired_doc = MachineDocument.objects.filter(
            organization=self.org,
            machine=self.machine,
            expiry_date__lt=today
        ).exists()
        if expired_doc:
            score -= 10
            reasons.append("One or more compliance documents (RC/Insurance/Permit) expired (-10 pts).")
            risk_indicators.append("Expired Compliance Document")
            recommendations.append("Renew expired compliance documents to prevent fine penalties.")

        # Final Clamp
        final_score = max(0, min(100, score))

        # Status Classification
        if final_score >= 85:
            status = 'excellent'
            status_label = 'Excellent'
            badge_class = 'kp-badge-success'
        elif final_score >= 70:
            status = 'good'
            status_label = 'Good'
            badge_class = 'kp-badge-brand'
        elif final_score >= 50:
            status = 'warning'
            status_label = 'Warning'
            badge_class = 'kp-badge-warning'
        else:
            status = 'critical'
            status_label = 'Critical'
            badge_class = 'kp-badge-danger'

        return {
            'score': final_score,
            'status': status,
            'status_label': status_label,
            'badge_class': badge_class,
            'reasons': reasons if reasons else ["Equipment operating in optimal mechanical condition."],
            'recommendations': recommendations if recommendations else ["Maintain current preventive service schedule."],
            'risk_indicators': risk_indicators,
            'repair_ratio': round(repair_ratio, 1),
            'total_downtime': total_downtime,
            'breakdown_count': b_count,
        }
