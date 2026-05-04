from .models import Vehicle

def fleet_notifications(request):
    notifications = []
    if request.user.is_authenticated:
        vehicles = Vehicle.objects.all()
        for v in vehicles:
            if v.inspection_days_left is not None and v.inspection_days_left < 0:
                notifications.append({'plate': v.plate, 'issue': 'Muayene', 'days': abs(v.inspection_days_left)})
            if v.insurance_days_left is not None and v.insurance_days_left < 0:
                notifications.append({'plate': v.plate, 'issue': 'Trafik Sigortası', 'days': abs(v.insurance_days_left)})
            if v.casco_days_left is not None and v.casco_days_left < 0:
                notifications.append({'plate': v.plate, 'issue': 'Kasko', 'days': abs(v.casco_days_left)})
    
    notifications_read = request.session.get('notifications_read', False)
    
    return {
        'fleet_notifications': notifications,
        'notifications_read': notifications_read,
        'notifications_count': len(notifications)
    }
