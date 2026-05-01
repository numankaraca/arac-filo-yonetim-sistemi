from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)

class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

class Role(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class User(AbstractUser, BaseModel):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Override groups and user_permissions to avoid clash
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='fleet_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='fleet_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

class Department(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Personnel(BaseModel):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    identity_number = models.CharField(max_length=11, unique=True, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='personnel')
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Vehicle(BaseModel):
    STATUS_CHOICES = [
        ('active', 'Aktif'),
        ('service', 'Serviste'),
        ('passive', 'Pasif'),
    ]
    
    plate = models.CharField(max_length=20, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    model_year = models.IntegerField()
    vehicle_type = models.CharField(max_length=50, blank=True, null=True)
    fuel_type = models.CharField(max_length=30, blank=True, null=True)
    transmission_type = models.CharField(max_length=30, blank=True, null=True)
    chassis_number = models.CharField(max_length=100, blank=True, null=True)
    engine_number = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='vehicles')
    kilometer = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.plate} - {self.brand} {self.model}"

    @property
    def latest_inspection(self):
        return self.inspections.order_by('-valid_until').first()

    @property
    def latest_traffic_insurance(self):
        return self.traffic_insurances.order_by('-end_date').first()

    @property
    def latest_casco_policy(self):
        return self.casco_policies.order_by('-end_date').first()

    def _days_left(self, date_val):
        if not date_val:
            return None
        return (date_val - timezone.now().date()).days

    @property
    def inspection_days_left(self):
        inspection = self.latest_inspection
        return self._days_left(inspection.valid_until) if inspection else None

    @property
    def insurance_days_left(self):
        insurance = self.latest_traffic_insurance
        return self._days_left(insurance.end_date) if insurance else None

    @property
    def casco_days_left(self):
        casco = self.latest_casco_policy
        return self._days_left(casco.end_date) if casco else None

class VehicleAssignment(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignments')
    personnel = models.ForeignKey(Personnel, on_delete=models.CASCADE, related_name='assignments')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_kilometer = models.IntegerField()
    end_kilometer = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

class KilometerLog(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='kilometer_logs')
    personnel = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    kilometer = models.IntegerField()
    description = models.TextField(blank=True, null=True)

class MaintenanceRecord(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='maintenance_records')
    date = models.DateField()
    kilometer = models.IntegerField()
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    service_name = models.CharField(max_length=100, blank=True, null=True)

class Inspection(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections')
    date = models.DateField()
    valid_until = models.DateField()
    result = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    notes = models.TextField(blank=True, null=True)

class TrafficInsurance(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='traffic_insurances')
    policy_number = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

class CascoPolicy(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='casco_policies')
    policy_number = models.CharField(max_length=100)
    company = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

class FuelRecord(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='fuel_records')
    personnel = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    liter = models.DecimalField(max_digits=6, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    kilometer = models.IntegerField()
    station = models.CharField(max_length=100, blank=True, null=True)

class DamageRecord(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='damage_records')
    date = models.DateField()
    description = models.TextField()
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    repaired = models.BooleanField(default=False)

class TrafficFine(BaseModel):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='traffic_fines')
    personnel = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)
    is_paid = models.BooleanField(default=False)

class Document(BaseModel):
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to='documents/')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')
    personnel = models.ForeignKey(Personnel, on_delete=models.SET_NULL, null=True, blank=True, related_name='documents')

class Notification(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

class ActivityLog(BaseModel):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=150)
    model_name = models.CharField(max_length=50, blank=True, null=True)
    object_id = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
