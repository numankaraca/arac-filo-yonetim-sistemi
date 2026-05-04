from django.contrib import admin
from .models import Vehicle, Department, User, Document, Inspection, TrafficInsurance, CascoPolicy, MaintenanceRecord

admin.site.site_header = "İstanbul İl Göç İdaresi Araç Yönetimi"
admin.site.site_title = "İl Göç İdaresi Admin"
admin.site.index_title = "Araç Yönetim Sistemine Hoş Geldiniz"

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate', 'brand', 'model', 'department', 'status')
    search_fields = ('plate', 'brand', 'model')

admin.site.register(Department)
admin.site.register(User)
admin.site.register(Document)
admin.site.register(Inspection)
admin.site.register(TrafficInsurance)
admin.site.register(CascoPolicy)
admin.site.register(MaintenanceRecord)
