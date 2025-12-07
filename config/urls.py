from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # Root should go to authentication landing page
    path('', include("authentication.urls")),

    # PII app
    path('pii/', include('pii_app.urls')),

    # Blockchain
    path('ledger/', include('blockchain_app.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
