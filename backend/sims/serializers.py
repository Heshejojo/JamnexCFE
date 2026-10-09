from rest_framework import serializers

from operadores.models import Operador
from .models import AsignacionSim, Sim


class SimSerializer(serializers.ModelSerializer):
    operador = serializers.PrimaryKeyRelatedField(
        queryset=Operador.objects.all(),
        required=False,
        allow_null=True,
    )
    operador_nombre = serializers.CharField(source='operador.nombre', read_only=True, allow_null=True)

    class Meta:
        model = Sim
        fields = [
            'id', 'dispositivo', 'sim_uuid', 'iccid', 'numero_telefonico', 'operador', 'operador_nombre', 'pais', 'mcc', 'mnc',
            'slot', 'carrier_id', 'esim', 'tecnologia', 'roaming', 'estado', 'sim_datos',
            'fecha_alta', 'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SimEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sim
        fields = ['iccid', 'numero_telefonico']


class AsignacionSimSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionSim
        fields = ['id', 'sim', 'dispositivo', 'trabajador', 'slot', 'fecha_asignacion', 'fecha_finalizacion', 'activo']
