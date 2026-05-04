from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Vehicle, Department, Document, Inspection, TrafficInsurance, CascoPolicy, MaintenanceRecord
from .forms import VehicleForm, DepartmentForm, LoginForm, DocumentForm
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.db.models import Q, Max, F
import openpyxl
from django.utils import timezone
from django.template.loader import get_template
from xhtml2pdf import pisa

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Kullanıcı adı veya şifre hatalı.')
    else:
        form = LoginForm()
    return render(request, 'fleet/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    total_vehicles = Vehicle.objects.count()
    active_vehicles = Vehicle.objects.filter(status='active').count()
    service_vehicles = Vehicle.objects.filter(status='service').count()
    
    # Calculate approaching deadlines (<= 30 days or overdue)
    vehicles = Vehicle.objects.all()
    upcoming_inspections = []
    upcoming_insurances = []
    upcoming_cascos = []
    upcoming_maintenances = []

    for v in vehicles:
        ins_days = v.inspection_days_left
        if ins_days is not None and ins_days <= 30:
            upcoming_inspections.append({'vehicle': v, 'days': ins_days})
            
        insur_days = v.insurance_days_left
        if insur_days is not None and insur_days <= 30:
            upcoming_insurances.append({'vehicle': v, 'days': insur_days})
            
        casco_days = v.casco_days_left
        if casco_days is not None and casco_days <= 30:
            upcoming_cascos.append({'vehicle': v, 'days': casco_days})
            
        # Bakım hesabı: Mevcut KM - Son Bakım KM >= 9000 ise yaklaşmış say. (10.000 bakım periyodu var sayımıyla)
        latest_m = v.latest_maintenance
        if latest_m and v.kilometer:
            km_diff = v.kilometer - latest_m.kilometer
            remaining_km = 10000 - km_diff
            if remaining_km <= 1000: # 1000 km kalmışsa veya geçmişse uyar
                upcoming_maintenances.append({'vehicle': v, 'remaining_km': remaining_km})
            
    # Sort by days/km left (most urgent first)
    upcoming_inspections.sort(key=lambda x: x['days'])
    upcoming_insurances.sort(key=lambda x: x['days'])
    upcoming_cascos.sort(key=lambda x: x['days'])
    upcoming_maintenances.sort(key=lambda x: x['remaining_km'])
    
    context = {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'service_vehicles': service_vehicles,
        'upcoming_inspections': upcoming_inspections,
        'upcoming_insurances': upcoming_insurances,
        'upcoming_cascos': upcoming_cascos,
        'upcoming_maintenances': upcoming_maintenances,
        'upcoming_count': len(upcoming_inspections) + len(upcoming_insurances) + len(upcoming_cascos) + len(upcoming_maintenances)
    }
    return render(request, 'fleet/dashboard.html', context)

@login_required
def vehicle_list(request):
    query = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '')
    department_id = request.GET.get('department_id', '')
    
    vehicles = Vehicle.objects.all()
    
    if department_id:
        vehicles = vehicles.filter(department_id=department_id)
        
    if query:
        vehicles = vehicles.filter(
            Q(plate__icontains=query) |
            Q(brand__icontains=query) |
            Q(model__icontains=query) |
            Q(department__name__icontains=query)
        ).distinct()
        
    if status_filter in ['active', 'service', 'passive']:
        vehicles = vehicles.filter(status=status_filter)
        
    if sort_by == 'inspection':
        vehicles = vehicles.annotate(
            latest_inspection_date=Max('inspections__valid_until')
        ).order_by(F('latest_inspection_date').asc(nulls_last=True))
    elif sort_by == 'plate_asc':
        vehicles = vehicles.order_by('plate')
    elif sort_by == 'plate_desc':
        vehicles = vehicles.order_by('-plate')
    elif sort_by == 'km_asc':
        vehicles = vehicles.order_by('kilometer')
    elif sort_by == 'km_desc':
        vehicles = vehicles.order_by('-kilometer')
    else:
        vehicles = vehicles.order_by('-created_at')
        
    context = {
        'vehicles': vehicles,
        'search_query': query,
        'status_filter': status_filter,
        'sort_by': sort_by,
    }
    return render(request, 'fleet/vehicle_list.html', context)

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    
    if request.method == 'POST':
        if 'document_upload' in request.POST:
            doc_form = DocumentForm(request.POST, request.FILES)
            if doc_form.is_valid():
                doc = doc_form.save(commit=False)
                doc.vehicle = vehicle
                doc.save()
                messages.success(request, 'Döküman başarıyla yüklendi.')
                return redirect('vehicle_detail', pk=vehicle.pk)
        elif 'document_delete' in request.POST:
            doc_id = request.POST.get('document_id')
            doc = get_object_or_404(Document, pk=doc_id, vehicle=vehicle)
            doc.delete()
            messages.success(request, 'Döküman silindi.')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        doc_form = DocumentForm()

    return render(request, 'fleet/vehicle_detail.html', {
        'vehicle': vehicle,
        'doc_form': doc_form,
    })

@login_required
def vehicle_create(request):
    if request.method == 'POST':
        form = VehicleForm(request.POST)
        if form.is_valid():
            vehicle = form.save()
            
            # Related Records
            if form.cleaned_data.get('inspection_valid_until'):
                Inspection.objects.create(
                    vehicle=vehicle, 
                    date=timezone.now().date(),
                    valid_until=form.cleaned_data['inspection_valid_until'],
                    result='Geçti'
                )
            
            if form.cleaned_data.get('insurance_end_date'):
                TrafficInsurance.objects.create(
                    vehicle=vehicle,
                    policy_number='Bilinmiyor',
                    company='Bilinmiyor',
                    start_date=timezone.now().date(),
                    end_date=form.cleaned_data['insurance_end_date']
                )
                
            if form.cleaned_data.get('casco_end_date'):
                CascoPolicy.objects.create(
                    vehicle=vehicle,
                    policy_number='Bilinmiyor',
                    company='Bilinmiyor',
                    start_date=timezone.now().date(),
                    end_date=form.cleaned_data['casco_end_date']
                )
                
            if form.cleaned_data.get('last_maintenance_date') or form.cleaned_data.get('last_maintenance_km'):
                MaintenanceRecord.objects.create(
                    vehicle=vehicle,
                    date=form.cleaned_data.get('last_maintenance_date') or timezone.now().date(),
                    kilometer=form.cleaned_data.get('last_maintenance_km') or vehicle.kilometer,
                    title='Periyodik Bakım'
                )

            messages.success(request, 'Araç ve ilgili kayıtlar başarıyla eklendi.')
            return redirect('vehicle_list')
    else:
        form = VehicleForm()
    return render(request, 'fleet/vehicle_form.html', {'form': form, 'title': 'Araç Ekle'})

@login_required
def vehicle_update(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        form = VehicleForm(request.POST, instance=vehicle)
        if form.is_valid():
            vehicle = form.save()
            
            # Update Related Records (Simple version: Create new or update latest)
            if form.cleaned_data.get('inspection_valid_until'):
                insp = vehicle.inspections.last()
                if insp:
                    insp.valid_until = form.cleaned_data['inspection_valid_until']
                    insp.save()
                else:
                    Inspection.objects.create(vehicle=vehicle, date=timezone.now().date(), valid_until=form.cleaned_data['inspection_valid_until'], result='Geçti')
            
            if form.cleaned_data.get('insurance_end_date'):
                insur = vehicle.traffic_insurances.last()
                if insur:
                    insur.end_date = form.cleaned_data['insurance_end_date']
                    insur.save()
                else:
                    TrafficInsurance.objects.create(vehicle=vehicle, policy_number='Bilinmiyor', company='Bilinmiyor', start_date=timezone.now().date(), end_date=form.cleaned_data['insurance_end_date'])
            
            if form.cleaned_data.get('casco_end_date'):
                casco = vehicle.casco_policies.last()
                if casco:
                    casco.end_date = form.cleaned_data['casco_end_date']
                    casco.save()
                else:
                    CascoPolicy.objects.create(vehicle=vehicle, policy_number='Bilinmiyor', company='Bilinmiyor', start_date=timezone.now().date(), end_date=form.cleaned_data['casco_end_date'])
            
            if form.cleaned_data.get('last_maintenance_date') or form.cleaned_data.get('last_maintenance_km'):
                maint = vehicle.maintenance_records.last()
                if maint:
                    if form.cleaned_data.get('last_maintenance_date'): maint.date = form.cleaned_data['last_maintenance_date']
                    if form.cleaned_data.get('last_maintenance_km'): maint.kilometer = form.cleaned_data['last_maintenance_km']
                    maint.save()
                else:
                    MaintenanceRecord.objects.create(vehicle=vehicle, date=form.cleaned_data.get('last_maintenance_date') or timezone.now().date(), kilometer=form.cleaned_data.get('last_maintenance_km') or vehicle.kilometer, title='Periyodik Bakım')

            messages.success(request, 'Araç ve kayıtlar başarıyla güncellendi.')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        # Prepopulate initial data
        initial_data = {}
        last_insp = vehicle.inspections.last()
        if last_insp: initial_data['inspection_valid_until'] = last_insp.valid_until
        
        last_insur = vehicle.traffic_insurances.last()
        if last_insur: initial_data['insurance_end_date'] = last_insur.end_date
        
        last_casco = vehicle.casco_policies.last()
        if last_casco: initial_data['casco_end_date'] = last_casco.end_date
        
        last_maint = vehicle.maintenance_records.last()
        if last_maint:
            initial_data['last_maintenance_date'] = last_maint.date
            initial_data['last_maintenance_km'] = last_maint.kilometer
            
        form = VehicleForm(instance=vehicle, initial=initial_data)
        
    return render(request, 'fleet/vehicle_form.html', {'form': form, 'title': 'Araç Düzenle', 'vehicle': vehicle})

@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Araç başarıyla silindi.')
        return redirect('vehicle_list')
    return redirect('vehicle_list')

    return redirect('vehicle_list')

@login_required
def mark_notifications_read(request):
    request.session['notifications_read'] = True
    return JsonResponse({'status': 'success'})

@login_required
def department_list(request):
    departments = Department.objects.all().order_by('name')
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Birim başarıyla eklendi.')
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'fleet/department_list.html', {'departments': departments, 'form': form})

@login_required
def export_vehicles(request):
    if request.method == 'POST':
        vehicle_ids = request.POST.getlist('vehicle_ids')
        export_format = request.POST.get('format', 'excel')
        
        if vehicle_ids:
            vehicles = Vehicle.objects.filter(id__in=vehicle_ids)
        else:
            vehicles = Vehicle.objects.all()

        current_date = timezone.localtime().strftime('%d.%m.%Y')
        
        if export_format == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = f'attachment; filename="arac_listesi_{current_date}.xlsx"'
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Araçlar"
            
            visible_columns = request.POST.get('visible_columns', '')
            visible_cols_list = visible_columns.split(',') if visible_columns else []
            
            col_mapping = {
                'col-brand': ('Marka / Model', lambda v: f"{v.brand} {v.model} ({v.department.name if v.department else 'Birim Yok'})"),
                'col-km': ('Kilometre', lambda v: f"{v.kilometer} km"),
                'col-maintenance': ('Son Bakım', lambda v: f"{v.latest_maintenance.date.strftime('%d.%m.%Y')} ({v.latest_maintenance.kilometer} km)" if v.latest_maintenance else 'Kayıt Yok'),
                'col-inspection': ('Muayene', lambda v: v.latest_inspection.valid_until.strftime('%d.%m.%Y') if v.latest_inspection else 'Kayıt Yok'),
                'col-insurance': ('Trafik Sigortası', lambda v: v.latest_traffic_insurance.end_date.strftime('%d.%m.%Y') if v.latest_traffic_insurance else 'Kayıt Yok'),
                'col-casco': ('Kasko', lambda v: v.latest_casco_policy.end_date.strftime('%d.%m.%Y') if v.latest_casco_policy else 'Kayıt Yok'),
                'col-status': ('Durum', lambda v: v.get_status_display()),
                'col-year': ('Model Yılı', lambda v: v.model_year),
                'col-chassis': ('Şasi No', lambda v: v.chassis_number if v.chassis_number else '-'),
                'col-engine': ('Motor No', lambda v: v.engine_number if v.engine_number else '-'),
                'col-type': ('Araç Tipi', lambda v: v.vehicle_type if v.vehicle_type else '-'),
                'col-fuel': ('Yakıt Türü', lambda v: v.fuel_type if v.fuel_type else '-'),
                'col-transmission': ('Vites Tipi', lambda v: v.transmission_type if v.transmission_type else '-'),
                'col-color': ('Renk', lambda v: v.color if v.color else '-'),
            }
            
            if not visible_cols_list:
                visible_cols_list = ['col-brand', 'col-km', 'col-inspection', 'col-insurance', 'col-casco', 'col-status']
                
            headers = ['Plaka']
            extractors = [lambda v: v.plate]
            
            for col_key in visible_cols_list:
                if col_key in col_mapping:
                    headers.append(col_mapping[col_key][0])
                    extractors.append(col_mapping[col_key][1])
            
            ws.append(headers)
            
            for v in vehicles:
                row_data = [str(extractor(v)) for extractor in extractors]
                ws.append(row_data)
                
            wb.save(response)
            return response
            
        elif export_format == 'pdf':
            template = get_template('fleet/pdf/vehicle_list_pdf.html')
            context = {'vehicles': vehicles}
            html = template.render(context)
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="arac_listesi_{current_date}.pdf"'
            
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('PDF oluşturulurken bir hata oluştu.')
            return response

    return redirect('vehicle_list')
