from rest_framework import generics, permissions

from .models import AsignacionSim, Sim
from .serializers import AsignacionSimSerializer, SimSerializer
from usuarios.permissions import RolePermission


class SimListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sim.objects.select_related('operador').all()
    serializer_class = SimSerializer
    permission_classes = [RolePermission]


class SimDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sim.objects.select_related('operador').all()
    serializer_class = SimSerializer
    permission_classes = [RolePermission]


class AsignacionSimListCreateAPIView(generics.ListCreateAPIView):
    queryset = AsignacionSim.objects.select_related('sim', 'dispositivo', 'trabajador').all()
    serializer_class = AsignacionSimSerializer
    permission_classes = [RolePermission]


class AsignacionSimDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AsignacionSim.objects.all()
    serializer_class = AsignacionSimSerializer
    permission_classes = [RolePermission]
