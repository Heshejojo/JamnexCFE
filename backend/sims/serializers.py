from rest_framework import serializers

from operadores.models import Operador
from .models import AsignacionSim, Sim, SimTransferConflict


class SimSerializer(serializers.ModelSerializer):
    operador = serializers.PrimaryKeyRelatedField(
        queryset=Operador.objects.all(),
        required=False,
        allow_null=True,
    )
    operador_nombre = serializers.CharField(source='operador.nombre', read_only=True, allow_null=True)
    detectada = serializers.SerializerMethodField()
    ultimo_reporte = serializers.SerializerMethodField()
    dispositivos_count = serializers.SerializerMethodField()

    def get_detectada(self, obj):
        return obj.historial.filter(hasta__isnull=True).exists()

    def get_ultimo_reporte(self, obj):
        record = obj.historial.order_by('-ultimo_reporte', '-desde').first()
        return record.ultimo_reporte.isoformat() if record and record.ultimo_reporte else None

    def get_dispositivos_count(self, obj):
        return obj.historial.values('dispositivo_id').distinct().count()

    class Meta:
        model = Sim
        fields = [
            'id', 'dispositivo', 'sim_uuid', 'iccid', 'numero_telefonico', 'operador', 'operador_nombre', 'pais', 'mcc', 'mnc',
            'slot', 'carrier_id', 'esim', 'tecnologia', 'roaming', 'estado', 'sim_datos',
            'fecha_alta', 'activo', 'detectada', 'ultimo_reporte', 'dispositivos_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class SimEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sim
        fields = ['iccid', 'numero_telefonico']


class SimTransferConflictSerializer(serializers.ModelSerializer):
    sim_id = serializers.IntegerField(read_only=True)
    iccid = serializers.CharField(source='sim.iccid', read_only=True, allow_null=True)
    numero_telefonico = serializers.CharField(source='sim.numero_telefonico', read_only=True, allow_null=True)
    source_device_name = serializers.SerializerMethodField()
    target_device_name = serializers.SerializerMethodField()

    class Meta:
        model = SimTransferConflict
        fields = [
            'id', 'sim_id', 'iccid', 'numero_telefonico',
            'source_device', 'source_device_name',
            'target_device', 'target_device_name', 'created_at',
        ]

    @staticmethod
    def _device_name(device):
        if device is None:
            return 'Dispositivo eliminado'
        return ' '.join(filter(None, [device.fabricante, device.modelo])) or device.device_uuid or str(device.pk)

    def get_source_device_name(self, conflict):
        return self._device_name(conflict.source_device)

    def get_target_device_name(self, conflict):
        return self._device_name(conflict.target_device)


class AsignacionSimSerializer(serializers.ModelSerializer):
    class Meta:
        model = AsignacionSim
        fields = ['id', 'sim', 'dispositivo', 'trabajador', 'slot', 'fecha_asignacion', 'fecha_finalizacion', 'activo']
