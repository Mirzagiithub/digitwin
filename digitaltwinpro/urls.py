from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("dashboard.urls")),
    # API / App routes
    path('api/core/', include('core.urls')),
    path('api/assets/', include('assets.urls')),
    path('api/simulation/', include('simulation.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/cybersecurity/', include('cybersecurity.urls')),
    path('api/iot/', include('iot.urls')),
]

# Media files (development only)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
