from django.db import models
from apps.tenants.models import Organization
from apps.machines.models import Machine

class FuelLog(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='fuel_logs')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='fuel_logs')
    date = models.DateField()
    fuel_liters = models.FloatField(help_text="Volume of fuel filled in Liters")
    cost_per_liter = models.DecimalField(max_digits=10, decimal_places=2, default=94.50)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2)
    meter_reading = models.FloatField(help_text="Meter reading at fill-up time")
    hours_run_since_last = models.FloatField(default=0.0, help_text="Operating units run since previous refueling")
    efficiency_rate = models.FloatField(default=0.0, help_text="Liters per HR or Liters per 100 KM")
    fuel_vendor = models.CharField(max_length=150, blank=True, null=True, help_text="Station or site tanker")
    is_abnormal_flag = models.BooleanField(default=False, help_text="True if efficiency is suspicious/abnormal")
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-created_at']

    def save(self, *args, **kwargs):
        if not self.total_cost:
            self.total_cost = float(self.fuel_liters) * float(self.cost_per_liter)
        
        # Calculate efficiency rate (Liters per HR)
        if self.hours_run_since_last > 0:
            self.efficiency_rate = round(self.fuel_liters / self.hours_run_since_last, 2)
            # Threshold for abnormal consumption (e.g., > 14 L/hr for general JCBs or > 25 L/hr for Excavator)
            if self.efficiency_rate > 15.0:
                self.is_abnormal_flag = True
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.machine.name} - {self.fuel_liters}L on {self.date}"
