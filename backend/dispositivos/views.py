import hashlib
import secrets

from django.utils import timezone
from rest_framework import authentication, generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from consumos.models import Consumo
from bateria.models import RegistroBateria
from ram.models import RegistroRam
from almacenamiento.models import RegistroAlmacenamiento
from redes.models import RegistroRed
from sims.models import Sim
from operadores.models import Operador

from .models import CredencialDispositivo, Dispositivo
from .serializers import DeviceConsumptionSerializer, DeviceNetworkSerializer, DeviceRegisterSerializer, DeviceSimSerializer, DeviceStatusSerializer, DispositivoEditSerializer, DispositivoSerializer
from usuarios.permissions import RolePermission
from auditoria.services import record_action


class DeviceAuthentication(authentication.BaseAuthentication):
    keyword = 'Device'

    def authenticate(self, request):
        header = request.headers.get('Authorization', '')
        if not header.startswith(f'{self.keyword} '):
            return None

        raw_token = header[len(self.keyword) + 1:].strip()
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        credential = CredencialDispositivo.objects.select_related('dispositivo').filter(
            token_hash=token_hash, revocado=False, dispositivo__activo=True
        ).first()
        if not credential:
            return None

        credential.ultimo_uso = timezone.now()
        credential.save(update_fields=['ultimo_uso'])
        return credential.dispositivo, credential


class DeviceRegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = DeviceRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device_defaults = {
            key: value
            for key, value in data.items()
            if key not in {'device_uuid', 'serial', 'imei_1'}
        }
        device, created = Dispositivo.objects.get_or_create(
            device_uuid=data['device_uuid'],
            defaults={
                **device_defaults,
                'serial': data.get('serial'),
                'imei_1': data.get('imei_1'),
            },
        )
        if not created:
            for field, value in device_defaults.items():
                setattr(device, field, value)
            device.save(update_fields=[*device_defaults, 'updated_at'])
        raw_token = secrets.token_urlsafe(32)
        CredencialDispositivo.objects.update_or_create(
            dispositivo=device,
            defaults={'token_hash': hashlib.sha256(raw_token.encode()).hexdigest(), 'revocado': False},
        )
        return Response({'device_id': device.id, 'device_uuid': device.device_uuid, 'token': raw_token}, status=status.HTTP_201_CREATED)


class DeviceStatusView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        device = request.user
        if data.get('activo') is not None:
            device.activo = data['activo']
        device.ultimo_contacto = timezone.now()
        device.save(update_fields=['activo', 'ultimo_contacto', 'updated_at'])
        if data.get('battery_percent') is not None:
            state = (data.get('battery_status') or 'DESCONOCIDO').upper()
            state = {'COMPLETA': 'CARGADA', 'DESCONOCIDA': 'DESCONOCIDO'}.get(state, state)
            if state not in {'CARGANDO', 'DESCARGANDO', 'CARGADA', 'DESCONOCIDO'}:
                state = 'DESCONOCIDO'
            RegistroBateria.objects.create(
                dispositivo=device,
                porcentaje=data['battery_percent'],
                estado=state,
                temperatura=data.get('battery_temperature'),
            )
        if data.get('ram_total') is not None:
            RegistroRam.objects.create(
                dispositivo=device,
                ram_total=data['ram_total'],
                ram_usada=data.get('ram_usada') or 0,
                ram_disponible=data.get('ram_disponible') or 0,
            )
        if data.get('almacenamiento_total') is not None:
            RegistroAlmacenamiento.objects.create(
                dispositivo=device,
                almacenamiento_total=data['almacenamiento_total'],
                usado=data.get('almacenamiento_usado') or 0,
                disponible=data.get('almacenamiento_disponible') or 0,
            )
        return Response({'device_id': device.id, 'received_at': timezone.now()})


class DeviceNetworkView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceNetworkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        sim = Sim.objects.filter(dispositivo=request.user).order_by('-updated_at').first()
        record = RegistroRed.objects.create(
            dispositivo=request.user,
            sim=sim,
            tipo_conexion=data['tipo_conexion'],
        )
        return Response({'id': record.id, 'received_at': timezone.now()}, status=status.HTTP_201_CREATED)


class DeviceSimView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceSimSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        operador_nombre = data.pop('operador_nombre', None)
        operador = None
        if operador_nombre:
            operador, _ = Operador.objects.get_or_create(
                nombre=operador_nombre,
                defaults={'pais': data.get('pais', ''), 'activo': True},
            )
        sim_defaults = {
            'dispositivo': request.user,
            'slot': data.get('slot'),
            'mcc': data.get('mcc', ''),
            'mnc': data.get('mnc', ''),
            'operador': operador,
            'pais': data.get('pais', ''),
            'carrier_id': data.get('carrier_id'),
            'esim': data.get('esim', False),
            'tecnologia': data.get('tecnologia', ''),
            'roaming': data.get('roaming', False),
            'activo': True,
        }
        sim, created = Sim.objects.get_or_create(
            sim_uuid=data['sim_uuid'],
            defaults={
                **sim_defaults,
                'iccid': data.get('iccid'),
                'numero_telefonico': data.get('numero_telefonico'),
            },
        )
        if not created:
            for field, value in sim_defaults.items():
                setattr(sim, field, value)
            sim.save(update_fields=[*sim_defaults, 'updated_at'])
        Consumo.objects.filter(dispositivo=request.user, sim__isnull=True).update(sim=sim)
        return Response({'id': sim.id, 'available': True}, status=status.HTTP_201_CREATED)


class DeviceConsumptionView(APIView):
    authentication_classes = [DeviceAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = DeviceConsumptionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        mobile_data = data['consumo_datos_movil']
        total = mobile_data
        fecha = data.get('fecha', timezone.now())
        sim_id = data.get('sim')
        sim = Sim.objects.filter(pk=sim_id).first() if sim_id else None
        if sim is None:
            sim = Sim.objects.filter(dispositivo=request.user).order_by('-updated_at').first()
        consumo = Consumo.objects.filter(
            dispositivo=request.user,
            periodo=data['periodo'],
            fecha__date=fecha.date(),
        ).first()
        if consumo:
            consumo.sim = sim
            consumo.consumo_datos_movil = data['consumo_datos_movil']
            consumo.consumo_total = total
            consumo.fecha = fecha
            consumo.save(update_fields=[
                'sim', 'consumo_datos_movil', 'consumo_total', 'fecha',
            ])
        else:
            consumo = Consumo.objects.create(
                dispositivo=request.user,
                sim=sim,
                consumo_datos_movil=data['consumo_datos_movil'],
                consumo_total=total,
                periodo=data['periodo'],
                fecha=fecha,
                fuente='ANDROID',
            )
        return Response({'id': consumo.id, 'consumo_total': consumo.consumo_total}, status=status.HTTP_201_CREATED)


class DeviceRevokeView(APIView):
    permission_classes = [RolePermission]

    def post(self, request, pk):
        device = Dispositivo.objects.get(pk=pk)
        credential = getattr(device, 'credencial', None)
        if credential:
            credential.revocado = True
            credential.save(update_fields=['revocado'])
        device.activo = False
        device.save(update_fields=['activo', 'updated_at'])
        record_action(request, 'REVOCAR', 'dispositivos', device.pk, 'Credencial de dispositivo revocada')
        return Response({'device_id': device.pk, 'revocado': True})


class DispositivoListCreateAPIView(generics.ListCreateAPIView):
    queryset = Dispositivo.objects.all()
    serializer_class = DispositivoSerializer
    permission_classes = [RolePermission]


class DispositivoDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Dispositivo.objects.all()
    serializer_class = DispositivoSerializer
    permission_classes = [RolePermission]

    def get_serializer_class(self):
        if self.request.method in {'PUT', 'PATCH'}:
            return DispositivoEditSerializer
        return DispositivoSerializer

    def perform_update(self, serializer):
        device = serializer.save()
        record_action(self.request, 'MODIFICAR', 'dispositivos', device.pk, 'Dispositivo modificado')

    def perform_destroy(self, instance):
        record_action(self.request, 'ELIMINAR', 'dispositivos', instance.pk, 'Dispositivo eliminado')
        instance.delete()
