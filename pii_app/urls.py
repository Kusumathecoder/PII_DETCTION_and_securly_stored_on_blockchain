from django.urls import path
from . import views

app_name = "pii_app"

urlpatterns = [
    path("upload/", views.upload_view, name="pii_upload"),
    path("result/<int:doc_id>/", views.result_view, name="pii_result"),
    path("download/<int:doc_id>/", views.download_redacted, name="pii_download"),
]
