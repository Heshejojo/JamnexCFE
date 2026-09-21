from django.urls import path

from .views import AsignacionSimDetailAPIView, AsignacionSimListCreateAPIView, SimDetailAPIView, SimListCreateAPIView

urlpatterns = [
    path('asignaciones-sim/', AsignacionSimListCreateAPIView.as_view(), name='asignaciones-sim-list'),
    path('asignaciones-sim/<int:pk>/', AsignacionSimDetailAPIView.as_view(), name='asignaciones-sim-detail'),
    path('sims/', SimListCreateAPIView.as_view(), name='sims-list'),
    path('sims/<int:pk>/', SimDetailAPIView.as_view(), name='sims-detail'),
]
