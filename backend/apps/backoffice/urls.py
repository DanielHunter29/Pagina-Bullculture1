from django.urls import path

from . import views

app_name = "backoffice"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reportes/ventas.xlsx", views.export_sales_xlsx, name="export-xlsx"),
    path("reportes/ventas.pdf", views.export_sales_pdf, name="export-pdf"),
]
