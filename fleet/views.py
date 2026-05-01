from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from .models import Vehicle, Department
from .forms import VehicleForm, DepartmentForm, LoginForm
from django.contrib import messages

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
    
    context = {
        'total_vehicles': total_vehicles,
        'active_vehicles': active_vehicles,
        'service_vehicles': service_vehicles,
    }
    return render(request, 'fleet/dashboard.html', context)

@login_required
def vehicle_list(request):
    vehicles = Vehicle.objects.all().order_by('-created_at')
    return render(request, 'fleet/vehicle_list.html', {'vehicles': vehicles})

@login_required
def vehicle_detail(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    return render(request, 'fleet/vehicle_detail.html', {'vehicle': vehicle})

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
