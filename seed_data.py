import os
import django
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from fleet.models import Department, Vehicle, Inspection, TrafficInsurance, CascoPolicy

def run():
    print("Seeding test data...")

    # Create Departments
    dept1, _ = Department.objects.get_or_create(name="İnsan Kaynakları", description="İK Birimi")
    dept2, _ = Department.objects.get_or_create(name="Satış Departmanı", description="Saha Satış")
    dept3, _ = Department.objects.get_or_create(name="Bilgi İşlem", description="IT Departmanı")

    today = timezone.now().date()

    # Clear old test vehicles if they exist
    Vehicle.objects.all().delete()

    # Vehicle 1: Muayene geçmiş, Sigorta/Kasko yaklaşıyor (< 30 gün)
    v1 = Vehicle.objects.create(
        plate="34 ABC 01", brand="Renault", model="Megane", model_year=2020, 
        department=dept1, kilometer=120000, status="active"
    )
    Inspection.objects.create(
        vehicle=v1, date=today - timedelta(days=385), valid_until=today - timedelta(days=20), result="Geçti"
    )
    TrafficInsurance.objects.create(
        vehicle=v1, policy_number="TRF-001", company="A Sigorta", 
        start_date=today - timedelta(days=350), end_date=today + timedelta(days=15)
    )
    CascoPolicy.objects.create(
        vehicle=v1, policy_number="KSK-001", company="A Sigorta", 
        start_date=today - timedelta(days=350), end_date=today + timedelta(days=15)
    )

    # Vehicle 2: Muayene yaklaşıyor, Sigorta/Kasko uzun (> 30 gün)
    v2 = Vehicle.objects.create(
        plate="06 XYZ 99", brand="Fiat", model="Egea", model_year=2021, 
        department=dept2, kilometer=85000, status="active"
    )
    Inspection.objects.create(
        vehicle=v2, date=today - timedelta(days=340), valid_until=today + timedelta(days=25), result="Geçti"
    )
    TrafficInsurance.objects.create(
        vehicle=v2, policy_number="TRF-002", company="B Sigorta", 
        start_date=today - timedelta(days=100), end_date=today + timedelta(days=265)
    )
    CascoPolicy.objects.create(
        vehicle=v2, policy_number="KSK-002", company="B Sigorta", 
        start_date=today - timedelta(days=100), end_date=today + timedelta(days=265)
    )

    # Vehicle 3: Muayene uzun, Sigorta/Kasko geçmiş
    v3 = Vehicle.objects.create(
        plate="35 QWE 55", brand="Ford", model="Focus", model_year=2019, 
        department=dept3, kilometer=150000, status="active"
    )
    Inspection.objects.create(
        vehicle=v3, date=today - timedelta(days=100), valid_until=today + timedelta(days=265), result="Geçti"
    )
    TrafficInsurance.objects.create(
        vehicle=v3, policy_number="TRF-003", company="C Sigorta", 
        start_date=today - timedelta(days=400), end_date=today - timedelta(days=35)
    )
    CascoPolicy.objects.create(
        vehicle=v3, policy_number="KSK-003", company="C Sigorta", 
        start_date=today - timedelta(days=400), end_date=today - timedelta(days=35)
    )

    print("Test verileri başarıyla eklendi!")

if __name__ == '__main__':
    run()
