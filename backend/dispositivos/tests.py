from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from consumos.models import Consumo
from dispositivos.models import Dispositivo
from dispositivos.serializers import DispositivoSerializer
from redes.models import RegistroRed
from redes.serializers import RegistroRedSerializer


class DeviceActivityTimeoutTest(TestCase):
    def test_device_becomes_inactive_after_eighteen_hours_without_contact(self):
        device = Dispositivo.objects.create(
            device_uuid='activity-timeout-test',
            ultimo_contacto=timezone.now() - timedelta(hours=17, minutes=59),
        )
        self.assertTrue(device.esta_activo)

        device.ultimo_contacto = timezone.now() - timedelta(hours=18, minutes=1)
        device.save(update_fields=['ultimo_contacto'])

        self.assertFalse(device.esta_activo)
        serialized = DispositivoSerializer(device).data
        self.assertTrue(serialized['activo'])
        self.assertFalse(serialized['en_linea'])

    def test_device_without_contact_is_inactive(self):
        device = Dispositivo.objects.create(device_uuid='never-contacted-test')
        self.assertFalse(device.esta_activo)


class DeviceConsumptionMobileOnlyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        registration = self.client.post(
            '/api/device/register/',
            {'device_uuid': 'mobile-consumption-test'},
            format='json',
        )
        self.assertEqual(registration.status_code, 201)
        self.device = Dispositivo.objects.get(pk=registration.data['device_id'])
        self.device_headers = {
            'HTTP_AUTHORIZATION': f"Device {registration.data['token']}",
        }

    def test_wifi_and_submitted_total_do_not_change_mobile_consumption(self):
        response = self.client.post(
            '/api/device/consumption/',
            {
                'consumo_datos_movil': 12.5,
                'consumo_wifi': 900,
                'consumo_total': 1000,
                'periodo': 'diario',
            },
            format='json',
            **self.device_headers,
        )

        self.assertEqual(response.status_code, 201)
        consumption = Consumo.objects.get(dispositivo=self.device)
        self.assertEqual(consumption.consumo_datos_movil, 12.5)
        self.assertEqual(consumption.consumo_wifi, 0)
        self.assertEqual(consumption.consumo_total, 12.5)
        self.assertEqual(response.data['consumo_total'], 12.5)

        self.client.post(
            '/api/device/consumption/',
            {
                'consumo_datos_movil': 20,
                'consumo_wifi': 700,
                'consumo_total': 900,
                'periodo': 'diario',
            },
            format='json',
            **self.device_headers,
        )
        consumption.refresh_from_db()
        self.assertEqual(consumption.consumo_datos_movil, 20)
        self.assertEqual(consumption.consumo_wifi, 0)
        self.assertEqual(consumption.consumo_total, 20)

    def test_wifi_network_record_stores_only_connection_status(self):
        response = self.client.post(
            '/api/device/network/',
            {
                'tipo_conexion': 'WIFI',
                'ssid': 'private-network-name',
                'rssi': -30,
                'frecuencia': 5200,
                'velocidad': 800,
            },
            format='json',
            **self.device_headers,
        )

        self.assertEqual(response.status_code, 201)
        network = RegistroRed.objects.get(dispositivo=self.device)
        self.assertEqual(network.tipo_conexion, 'WIFI')
        self.assertIsNone(network.ssid)
        self.assertIsNone(network.rssi)
        self.assertIsNone(network.frecuencia)
        self.assertIsNone(network.velocidad)
        network_data = RegistroRedSerializer(network).data
        self.assertEqual(set(network_data), {'id', 'dispositivo', 'sim', 'tipo_conexion', 'fecha_hora'})
