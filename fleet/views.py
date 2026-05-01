from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Vehicle, Department, Document
from .forms import VehicleForm, DepartmentForm, LoginForm, DocumentForm
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
import openpyxl
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
            
    # Sort by days left (most urgent first)
    upcoming_inspections.sort(key=lambda x: x['days'])
    upcoming_insurances.sort(key=lambda x: x['days'])
    upcoming_cascos.sort(key=lambda x: x['days'])
    
    context = {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'service_vehicles': service_vehicles,
        'upcoming_inspections': upcoming_inspections,
        'upcoming_insurances': upcoming_insurances,
        'upcoming_cascos': upcoming_cascos,
    }
    return render(request, 'fleet/dashboard.html', context)

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.all().order_by('-created_at')
    return render(request, 'fleet/vehicle_list.html', {'vehicles': vehicles})

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
            form.save()
            messages.success(request, 'Araç başarıyla eklendi.')
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
            form.save()
            messages.success(request, 'Araç başarıyla güncellendi.')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleForm(instance=vehicle)
    return render(request, 'fleet/vehicle_form.html', {'form': form, 'title': 'Araç Düzenle', 'vehicle': vehicle})

@login_required
def vehicle_delete(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Araç başarıyla silindi.')
        return redirect('vehicle_list')
    return redirect('vehicle_list')

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

        if export_format == 'excel':
            response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            response['Content-Disposition'] = 'attachment; filename="arac_listesi.xlsx"'
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Araçlar"
            
            headers = ['Plaka', 'Marka / Model', 'Birim', 'Kilometre', 'Muayene', 'Trafik Sigortası', 'Kasko', 'Durum']
            ws.append(headers)
            
            for v in vehicles:
                ins = v.latest_inspection.valid_until.strftime('%d.%m.%Y') if v.latest_inspection else 'Yok'
                traf = v.latest_traffic_insurance.end_date.strftime('%d.%m.%Y') if v.latest_traffic_insurance else 'Yok'
                casco = v.latest_casco_policy.end_date.strftime('%d.%m.%Y') if v.latest_casco_policy else 'Yok'
                dept = v.department.name if v.department else 'Birim Yok'
                
                ws.append([
                    v.plate, f"{v.brand} {v.model}", dept, v.kilometer, 
                    ins, traf, casco, v.get_status_display()
                ])
                
            wb.save(response)
            return response
            
        elif export_format == 'pdf':
            template = get_template('fleet/pdf/vehicle_list_pdf.html')
            context = {'vehicles': vehicles}
            html = template.render(context)
            
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="arac_listesi.pdf"'
            
            pisa_status = pisa.CreatePDF(html, dest=response)
            if pisa_status.err:
                return HttpResponse('PDF oluşturulurken bir hata oluştu.')
            return response

    return redirect('vehicle_list')
