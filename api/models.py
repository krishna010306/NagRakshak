from django.db import models


class users(models.Model):
    ROLE_CHOICES = [
        ("victim", "Victim"),
        ("driver", "Ambulance Driver"),
        ("volunteer", "Volunteer"),
        ("hospital", "Hospital"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100, blank=True, default="")
    contact = models.CharField(max_length=15, blank=True, default="")
    email = models.EmailField(unique=True, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    eme_contact = models.CharField(max_length=15, blank=True, default="")

    def __str__(self):
        return self.name


class ambulance(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    contact = models.CharField(max_length=15, blank=True, default="")

    def __str__(self):
        return self.name


class volunteer(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    contact = models.CharField(max_length=15, blank=True, default="")

    def __str__(self):
        return self.name


class hospital(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")
    latitude = models.FloatField(default=0)
    longitude = models.FloatField(default=0)
    contact = models.CharField(max_length=15, blank=True, default="")
    antivenom = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class EmergencyAlert(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("hospital_routed", "Hospital Routed"),
        ("ambulance_notified", "Ambulance Notified"),
        ("ambulance_accepted", "Ambulance Accepted"),
        ("volunteer_notified", "Volunteer Notified"),
        ("completed", "Completed"),
    ]

    patient_name = models.CharField(max_length=100, blank=True)
    patient_phone = models.CharField(max_length=15, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    snake_type = models.CharField(max_length=100, blank=True)
    has_vehicle = models.BooleanField(null=True, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="pending")
    assigned_hospital = models.ForeignKey(hospital, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_driver = models.ForeignKey(ambulance, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_volunteer = models.ForeignKey(volunteer, null=True, blank=True, on_delete=models.SET_NULL)
    driver_attempt_count = models.PositiveSmallIntegerField(default=0)
    driver_notified_at = models.DateTimeField(null=True, blank=True)
    attempted_driver_ids = models.JSONField(default=list, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Emergency Alert #{self.id} ({self.status})"


# Compatibility aliases for existing imports in views/admin.
User = users
AmbulanceDriver = ambulance
Volunteer = volunteer
Hospital = hospital