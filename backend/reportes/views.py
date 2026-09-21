from datetime import date
from io import BytesIO

from django.http import HttpResponse
from django.utils import timezone
from openpyxl import Workbook
from rest_framework.views import APIView

from usuarios.permissions import RolePermission
from auditoria.services import record_action
from consumos.models import Consumo
from dispositivos.models import Dispositivo
from sims.models import Sim


class SimMonthlyExportView(APIView):
    permission_classes = [RolePermission]

    def get(self, request, pk):
        month = int(request.query_params.get('mes', timezone.now().month))
        year = int(request.query_params.get('anio', timezone.now().year))
        if month < 1 or month > 12:
            return HttpResponse('El mes debe estar entre 1 y 12.', status=400)

        sim = Sim.objects.select_related('dispositivo', 'operador').filter(pk=pk).first()
        if not sim:
            return HttpResponse('SIM no encontrada.', status=404)

        start = date(year, month, 1)
        end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        consumos = Consumo.objects.filter(sim=sim, fecha__date__gte=start, fecha__date__lt=end).order_by('fecha')
        workbook = Workbook()
        summary = workbook.active
        summary.title = 'Resumen SIM'
        summary.append(['REPORTE MENSUAL DE SIM'])
        summary.append(['Mes', f'{year}-{month:02d}'])
        summary.append([])
        summary.append(['Fecha', 'Serial dispositivo', 'Datos móviles usados (MB)', 'Operador', 'ICCID', 'Número telefónico'])
        summary_rows = [
            [f'{year}-{month:02d}', sim.dispositivo.serial if sim.dispositivo else '',
             sum(item.consumo_datos_movil for item in consumos),
             sim.operador.nombre if sim.operador else '', sim.iccid or '', sim.numero_telefonico or ''],
        ]
        for row in summary_rows:
            summary.append(row)

        for sheet in workbook.worksheets:
            sheet.freeze_panes = 'A5'
            sheet.column_dimensions['A'].width = 28
            for cell in sheet[1]:
                cell.font = cell.font.copy(bold=True, color='FFFFFF')
                cell.fill = cell.fill.copy(fill_type='solid', fgColor='007F5F')
            for column in ('B', 'C', 'D', 'E', 'F'):
                sheet.column_dimensions[column].width = 24

        output = BytesIO()
        workbook.save(output)
        record_action(request, 'EXPORTAR', 'consumos', sim.pk, f'Reporte mensual SIM {year}-{month:02d}')
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="sim-{sim.pk}-{year}-{month:02d}.xlsx"'
        return response


class DevicesMonthlyExportView(APIView):
    permission_classes = [RolePermission]

    def get(self, request):
        month = int(request.query_params.get('mes', timezone.now().month))
        year = int(request.query_params.get('anio', timezone.now().year))
        if month < 1 or month > 12:
            return HttpResponse('El mes debe estar entre 1 y 12.', status=400)

        start = date(year, month, 1)
        end = date(year + (month == 12), 1 if month == 12 else month + 1, 1)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Dispositivos'
        sheet.append(['Fecha', 'Serial', 'Modelo', 'Fabricante', 'Estado', 'Datos móviles usados (MB)', 'ICCID', 'IMEI'])
        for device in Dispositivo.objects.all().order_by('id'):
            consumos = Consumo.objects.filter(dispositivo=device, fecha__date__gte=start, fecha__date__lt=end)
            sim = device.sims.order_by('id').first()
            sheet.append([
                f'{year}-{month:02d}', device.serial or '', device.modelo or '', device.fabricante or '',
                'Activo' if device.activo else 'Inactivo',
                sum(item.consumo_datos_movil for item in consumos),
                sim.iccid if sim else '', device.imei_1 or '',
            ])
        sheet.freeze_panes = 'A2'
        for column in ('A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'):
            sheet.column_dimensions[column].width = 25
        for cell in sheet[1]:
            cell.font = cell.font.copy(bold=True, color='FFFFFF')
            cell.fill = cell.fill.copy(fill_type='solid', fgColor='007F5F')
        output = BytesIO()
        workbook.save(output)
        record_action(request, 'EXPORTAR', 'dispositivos', '', f'Reporte mensual dispositivos {year}-{month:02d}')
        response = HttpResponse(output.getvalue(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="dispositivos-{year}-{month:02d}.xlsx"'
        return response
