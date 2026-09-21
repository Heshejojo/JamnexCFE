from django.urls import path

from .views import DevicesMonthlyExportView, SimMonthlyExportView

urlpatterns = [
    path('reportes/sims/<int:pk>/exportar/', SimMonthlyExportView.as_view(), name='sim-monthly-export'),
    path('reportes/dispositivos/exportar/', DevicesMonthlyExportView.as_view(), name='devices-monthly-export'),
]
