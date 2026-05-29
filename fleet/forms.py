from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
import re
from .models import Vehicle, Department, Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Örn: Ruhsat, Poliçe vb.'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }

class VehicleForm(forms.ModelForm):
    class Meta:
        model = Vehicle
        fields = [
            'plate', 'official_plate', 'brand', 'model', 'model_year',
            'department', 'kilometer', 'status', 'description'
        ]
        labels = {
            'plate': 'Plaka',
            'official_plate': 'Resmi Plaka (Varsa)',
            'brand': 'Marka',
            'model': 'Model',
            'model_year': 'Model Yılı',
            'department': 'Bağlı Olduğu Birim',
            'kilometer': 'Kilometre',
            'status': 'Durum',
            'description': 'Açıklama',
        }
        widgets = {
            'plate': forms.TextInput(attrs={'class': 'form-control'}),
            'official_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Varsa resmi plaka giriniz'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'model': forms.TextInput(attrs={'class': 'form-control'}),
            'model_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
            'kilometer': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    # Ekstra Alanlar (İlişkili modeller için)
    inspection_valid_until = forms.DateField(
        label="Muayene Geçerlilik Tarihi",
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    insurance_end_date = forms.DateField(
        label="Trafik Sigortası Bitiş Tarihi",
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    casco_end_date = forms.DateField(
        label="Kasko Bitiş Tarihi",
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    last_maintenance_date = forms.DateField(
        label="Son Bakım Tarihi",
        required=False,
        widget=forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'})
    )
    last_maintenance_km = forms.IntegerField(
        label="Son Bakım Kilometresi",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Örn: 15000'})
    )

    def clean_plate(self):
        plate = self.cleaned_data.get('plate', '').strip().upper()
        if not re.match(r'^[0-9].*[0-9]$', plate):
            raise ValidationError("Plaka bilgisi sayıyla başlamalı ve sayıyla bitmelidir. (Örn: 34 ABC 123)")
        return plate

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'}))
