from django.db import transaction
from django.utils import timezone

from .models import HistorialSim


def register_presence(sim, dispositivo, slot=None):
    if sim is None or dispositivo is None:
        return None

    now = timezone.now()
    with transaction.atomic():
        HistorialSim.objects.filter(sim=sim, hasta__isnull=True).exclude(
            dispositivo_id=dispositivo.pk,
        ).update(hasta=now)

        record = HistorialSim.objects.filter(
            sim=sim,
            dispositivo=dispositivo,
            hasta__isnull=True,
        ).order_by('-desde').first()

        if record is None:
            record = HistorialSim.objects.create(
                sim=sim,
                dispositivo=dispositivo,
                slot=slot,
                desde=now,
                ultimo_reporte=now,
            )
        else:
            record.slot = slot if slot is not None else record.slot
            record.ultimo_reporte = now
            record.save(update_fields=['slot', 'ultimo_reporte', 'updated_at'])

        return record


def close_missing(dispositivo, expected_count, reported_at=None):
    if dispositivo is None:
        return None

    reported_at = reported_at or timezone.now()
    with transaction.atomic():
        records = HistorialSim.objects.filter(
            dispositivo=dispositivo,
            hasta__isnull=True,
        ).order_by('desde')

        if expected_count is None:
            return records.count()

        if expected_count <= 0:
            records.update(hasta=reported_at)
            return 0

        for record in list(records[expected_count:]):
            record.hasta = reported_at
            record.save(update_fields=['hasta', 'updated_at'])

        return max(0, records.count() - expected_count)
