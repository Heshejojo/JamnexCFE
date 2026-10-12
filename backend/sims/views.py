from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AsignacionSim, Sim, SimTransferConflict
from .serializers import (
    AsignacionSimSerializer,
    SimEditSerializer,
    SimSerializer,
    SimTransferConflictSerializer,
)
from usuarios.permissions import RolePermission


class SimListCreateAPIView(generics.ListCreateAPIView):
    queryset = Sim.objects.select_related('operador').all()
    serializer_class = SimSerializer
    permission_classes = [RolePermission]


class SimDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sim.objects.select_related('operador').all()
    serializer_class = SimSerializer
    permission_classes = [RolePermission]

    def get_serializer_class(self):
        if self.request.method in {'PUT', 'PATCH'}:
            return SimEditSerializer
        return SimSerializer


class SimTransferConflictListAPIView(generics.ListAPIView):
    serializer_class = SimTransferConflictSerializer
    permission_classes = [RolePermission]

    def get_queryset(self):
        return SimTransferConflict.objects.filter(
            status=SimTransferConflict.Status.PENDING,
        ).select_related('sim', 'source_device', 'target_device').order_by('-created_at')


class SimTransferConflictActionAPIView(APIView):
    permission_classes = [RolePermission]

    def post(self, request, pk, action):
        if action not in {'transfer', 'dismiss'}:
            return Response({'detail': 'Acción no válida.'}, status=400)
        with transaction.atomic():
            conflict = get_object_or_404(
                SimTransferConflict.objects.select_for_update().select_related('sim'),
                pk=pk,
            )
            if conflict.status != SimTransferConflict.Status.PENDING:
                return Response(
                    {'detail': 'Esta solicitud ya fue atendida.'},
                    status=409,
                )

            if action == 'transfer':
                sim = Sim.objects.select_for_update().get(pk=conflict.sim_id)
                if not conflict.target_device_id:
                    return Response(
                        {'detail': 'El dispositivo que solicitó la SIM ya no existe.'},
                        status=409,
                    )
                if sim.dispositivo_id != conflict.source_device_id:
                    conflict.status = SimTransferConflict.Status.STALE
                    conflict.resolved_at = timezone.now()
                    conflict.save(update_fields=['status', 'resolved_at'])
                    return Response(
                        {'detail': 'La SIM ya cambió de dispositivo. Actualiza la lista.'},
                        status=409,
                    )

                sim.dispositivo_id = conflict.target_device_id
                sim.activo = True
                sim.save(update_fields=['dispositivo', 'activo', 'updated_at'])
                conflict.status = SimTransferConflict.Status.TRANSFERRED
            elif action == 'dismiss':
                conflict.status = SimTransferConflict.Status.DISMISSED
            conflict.resolved_at = timezone.now()
            conflict.save(update_fields=['status', 'resolved_at'])

        return Response({'id': conflict.id, 'status': conflict.status})


class AsignacionSimListCreateAPIView(generics.ListCreateAPIView):
    queryset = AsignacionSim.objects.select_related('sim', 'dispositivo', 'trabajador').all()
    serializer_class = AsignacionSimSerializer
    permission_classes = [RolePermission]


class AsignacionSimDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = AsignacionSim.objects.all()
    serializer_class = AsignacionSimSerializer
    permission_classes = [RolePermission]
