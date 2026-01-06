from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from assets.models import Asset
from iot.models import Device, Alert
from cybersecurity.models import ThreatDetectionEvent

@login_required
def dashboard(request):
    context = {
        "stats": {
            "assets": Asset.objects.count(),
            "devices": Device.objects.count(),
            "alerts": Alert.objects.filter(resolved=False).count(),
            "threats": ThreatDetectionEvent.objects.count(),
        },
        "chart": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
            "data": [12, 19, 7, 14, 9]
        }
    }
    return render(request, "dashboard/dashboard.html", context)
