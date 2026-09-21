from django.db import models

from dispositivos.models import Dispositivo
from operadores.models import Operador
from trabajadores.models import Trabajador


class Sim(models.Model):
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.SET_NULL, null=True, blank=True, related_name='sims')
    sim_uuid = models.CharField(max_length=255, unique=True, null=True, blank=True)
    iccid = models.CharField(max_length=255, null=True, blank=True)
    numero_telefonico = models.CharField(max_length=50, null=True, blank=True)
    operador = models.ForeignKey(Operador, on_delete=models.PROTECT, related_name='sims', null=True, blank=True)
    pais = models.CharField(max_length=100, blank=True)
    mcc = models.CharField(max_length=10, blank=True)
    mnc = models.CharField(max_length=10, blank=True)
    slot = models.IntegerField(null=True, blank=True)
    carrier_id = models.IntegerField(null=True, blank=True)
    esim = models.BooleanField(default=False)
    tecnologia = models.CharField(max_length=30, blank=True)
    roaming = models.BooleanField(default=False)
    estado = models.CharField(max_length=50, default='activo')
    sim_datos = models.BooleanField(default=False)
    fecha_alta = models.DateField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sim_uuid or self.iccid or f'SIM {self.pk}'


class AsignacionSim(models.Model):
    sim = models.ForeignKey(Sim, on_delete=models.CASCADE, related_name='asignaciones')
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='sims_asignadas')
    trabajador = models.ForeignKey(Trabajador, on_delete=models.CASCADE, related_name='sims_asignadas')
    slot = models.IntegerField(null=True, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_finalizacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.sim} -> {self.dispositivo}'
