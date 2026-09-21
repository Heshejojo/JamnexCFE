from rest_framework import serializers

from .models import RegistroRed


class RegistroRedSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroRed
        fields = ['id', 'dispositivo', 'sim', 'tipo_conexion', 'ssid', 'rssi', 'frecuencia', 'velocidad', 'tipo_red_movil', 'operador', 'ip_local', 'ip_publica', 'fecha_hora']
