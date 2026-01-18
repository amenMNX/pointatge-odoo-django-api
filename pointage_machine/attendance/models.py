from django.db import models
from django.utils.timezone import now

class Employee(models.Model):
    pin = models.CharField(
        max_length=10,
        unique=True,
        db_index=True
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.pin} - {self.name}"


class Pointage(models.Model):
    # Employee reference
    employee = models.ForeignKey("Employee", on_delete=models.CASCADE)
    
    # Timestamp of IN/OUT
    check_time = models.DateTimeField()
    
    # State IN or OUT
    state = models.CharField(max_length=3, choices=[("IN", "IN"), ("OUT", "OUT")])
    
    # Optional notes and anomaly flag
    anomaly = models.BooleanField(default=False)
    note = models.TextField(blank=True)
    
    # --- Step 2 additions ---
    # Track origin of pointage (WEB, MACHINE, API)
    source = models.CharField(
        max_length=20,
        default="WEB",
        help_text="Origin of pointage: WEB, API, MACHINE"
    )
    
    # Flag to indicate if this record has been synced to Odoo
    synced_to_odoo = models.BooleanField(
        default=False,
        help_text="True if pointage has been sent to Odoo"
    )
    
    # Optional external unique ID for Odoo integration
    external_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional unique external ID for integration"
    )

    # Order by timestamp
    class Meta:
        ordering = ["check_time"]

    def __str__(self):
        return f"{self.employee.pin} - {self.state} at {self.check_time}"



class Leave(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date_from = models.DateField()
    date_to = models.DateField()
    note = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.employee.pin} leave {self.date_from} → {self.date_to}"
