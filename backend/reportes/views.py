from calendar import monthrange
from collections import defaultdict
from openpyxl.styles import Font, PatternFill
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
        consumos = Consumo.objects.filter(
            sim=sim, periodo='diario', fecha__date__gte=start, fecha__date__lt=end
        ).order_by('fecha')

        # MB por día (si hay varias filas el mismo día, se suman)
        por_dia = defaultdict(float)
        for item in consumos:
            por_dia[timezone.localtime(item.fecha).date()] += item.consumo_datos_movil
        total_mes = sum(por_dia.values())

        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(fill_type='solid', fgColor='007F5F')

        workbook = Workbook()

        # Hoja 1: resumen del mes
        summary = workbook.active
        summary.title = 'Resumen SIM'
        summary.append(['Mes', 'Serial dispositivo', 'Datos móviles usados (MB)', 'Operador', 'ICCID', 'Número telefónico'])
        summary.append([
            f'{year}-{month:02d}',
            sim.dispositivo.serial if sim.dispositivo else '',
            round(total_mes, 2),
            sim.operador.nombre if sim.operador else '',
            sim.iccid or '',
            sim.numero_telefonico or '',
        ])

        # Hoja 2: consumo día por día
        daily = workbook.create_sheet('Consumo diario')
        daily.append(['Fecha', 'Datos móviles usados (MB)', 'Acumulado del mes (MB)'])
        acumulado = 0
        for day in range(1, monthrange(year, month)[1] + 1):
            current = date(year, month, day)
            usado = por_dia.get(current)
            if usado is not None:
                acumulado += usado
            daily.append([
                current,
                round(usado, 2) if usado is not None else None,
                round(acumulado, 2),
            ])
            daily.cell(row=daily.max_row, column=1).number_format = 'yyyy-mm-dd'
        daily.append(['TOTAL DEL MES', round(total_mes, 2), ''])
        for cell in daily[daily.max_row]:
            cell.font = Font(bold=True)

        for sheet in workbook.worksheets:
            sheet.freeze_panes = 'A2'
            for cell in sheet[1]:
                cell.font = header_font
                cell.fill = header_fill
            for column in ('A', 'B', 'C', 'D', 'E', 'F'):
                sheet.column_dimensions[column].width = 26

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
            consumos = Consumo.objects.filter(dispositivo=device, periodo='diario', fecha__date__gte=start, fecha__date__lt=end)
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
