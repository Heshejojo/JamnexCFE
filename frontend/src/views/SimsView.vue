<template>
  <div class="sims-page">
    <header class="topbar">
      <div>
        <p class="back-link">Volver a la lista</p>
        <div class="sim-page-title"><div><h2>Línea de SIM</h2>
        <p class="page-caption">Consulta el estado, operador y consumo móvil de cada línea.</p>
        </div></div>
      </div>
      <div class="topbar-actions">
        <span class="sync-state" :class="{ syncing: loading, failed: loadError }">
          <i></i>{{ loadError ? 'Sin conexión' : loading ? 'Sincronizando' : `Actualizado ${lastSync}` }}
        </span>
        <span v-if="selectedSim" class="live-status active">● Activa</span>
        <button class="primary-btn" :disabled="loading" @click="loadSims">Actualizar</button>
      </div>
    </header>

    <div class="sim-layout">
      <section class="panel inventory-panel">
        <div class="panel-topline">
          <div><span class="sim-section-icon">▤</span><div><p class="eyebrow">Líneas registradas</p><h3>Listado de SIMs</h3></div></div>
          <div class="list-heading-actions"><span class="sim-count">{{ filteredSims.length }}</span><button class="devices-report-btn" type="button" @click="exportDevicesReport">⇩ Reporte dispositivos</button></div>
        </div>

        <div class="search-box">
          <input v-model="query" placeholder="Buscar número, operador, ICCID o UUID" />
        </div>

        <div v-if="filteredSims.length" class="list">
          <div v-for="sim in filteredSims" :key="sim.id" class="sim-row" :class="{ active: selectedSim && selectedSim.id === sim.id }">
            <div class="sim-info-block">
              <span class="sim-row-icon">▤</span>
              <strong>{{ sim.numero_telefonico || 'Número no disponible' }}</strong>
              <small>{{ sim.operador_nombre || 'N/A' }} · {{ sim.iccid || 'Sin ICCID' }}</small>
            </div>
            <div class="row-actions">
              <span class="status-badge" :class="sim.activo ? 'active' : 'inactive'">
                {{ sim.activo ? '● Activa' : '● Inactiva' }}
              </span>
              <button class="detail-btn" title="Ver detalles" aria-label="Ver detalles" @click="selectDetail(sim)">Ver detalles</button>
              <button class="delete-btn" title="Eliminar SIM" aria-label="Eliminar SIM" @click="deleteSim(sim)">Eliminar</button>
            </div>
          </div>
        </div>
        <div v-else class="empty-card">
          {{ loadError || 'No hay SIMs que coincidan con la búsqueda.' }}
        </div>
      </section>

      <aside class="panel detail-panel" :class="{ empty: !selectedSim }">
        <template v-if="selectedSim">
          <div class="panel-header">
            <div class="device-title-wrap">
              <span class="detail-heading-icon">⚙</span>
              <p class="eyebrow">Información técnica</p>
              <h3>{{ selectedSim.numero_telefonico || 'SIM sin número' }}</h3>
            </div>
            <div class="header-actions">
              <span class="live-status" :class="selectedSim.activo ? 'active' : 'inactive'">
                {{ selectedSim.activo ? 'Activa' : 'Inactiva' }}
              </span>
              <button class="secondary-btn" type="button" @click="startEdit">✎ Editar</button>
              <button class="secondary-btn" type="button" @click="selectedSim = null">Cerrar</button>
            </div>
          </div>

          <div class="monthly-toolbar">
            <div><span class="eyebrow">Consumo mensual</span><strong>Datos usados en {{ monthLabel }}</strong></div>
            <div class="monthly-actions"><input v-model="selectedMonth" type="month" aria-label="Mes del reporte" /><button class="export-btn" type="button" @click="exportMonthlyReport">⇩ Excel</button></div>
          </div>
          
          <div class="device-summary">
  <div class="device-badge">
    <span class="device-icon">▤</span>
    <div>
      <small>Número de teléfono</small>
      <strong>{{ selectedSim.numero_telefonico || 'No disponible' }}</strong>
    </div>
  </div>

  <div class="summary-grid">
    <div class="summary-card blue">
      <span class="summary-icon">▥</span>
      <span class="metric-kicker">Datos móviles usados hoy</span>
      <strong>{{ todayUsed(selectedSim).toFixed(2) }} MB</strong>
    </div>
    <div class="summary-card green">
      <span class="summary-icon">▥</span>
      <span class="metric-kicker">Total acumulado del mes</span>
      <strong>{{ monthlyUsed(selectedSim).toFixed(2) }} MB</strong>
    </div>
    <div class="summary-card amber">
      <span class="summary-icon">◷</span>
      <span class="metric-kicker">Límite</span>
      <strong>{{ ((totalUsed(selectedSim) / 2048) * 100).toFixed(1) }}% / 2 GB</strong>
    </div>
    <div class="summary-card violet">
      <span class="summary-icon">◎</span>
      <span class="metric-kicker">Operadora</span>
      <strong>{{ selectedSim.operador_nombre || 'Sin operador' }}</strong>
    </div>
  </div>
</div>

          <div class="detail-grid">
            <div class="detail-item"><span class="detail-icon">▤</span><span>Estado de la línea</span><strong>{{ selectedSim.activo ? 'Activo' : 'Inactivo' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▥</span><span>Tipo de SIM</span><strong>{{ simType(selectedSim) }}</strong></div>
            <div class="detail-item"><span class="detail-icon">◉</span><span>Operador</span><strong>{{ selectedSim.operador_nombre || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">⌖</span><span>País</span><strong>{{ selectedSim.pais || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">♟</span><span>MCC / MNC</span><strong>{{ selectedSim.mcc || 'N/D' }} / {{ selectedSim.mnc || 'N/D' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▣</span><span>Carrier ID</span><strong>{{ selectedSim.carrier_id ?? 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▯</span><span>Número de celular</span><strong>{{ selectedSim.numero_telefonico || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▤</span><span>ICCID</span><strong>{{ selectedSim.iccid || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">◎</span><span>ID SIM</span><strong class="uuid">{{ selectedSim.sim_uuid || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▦</span><span>Ranura</span><strong>{{ selectedSim.slot ?? 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▥</span><span>Tecnología</span><strong>{{ selectedSim.tecnologia || 'No disponible' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">⌁</span><span>Roaming</span><strong>{{ selectedSim.roaming ? 'Sí' : 'No' }}</strong></div>
            <div class="detail-item"><span class="detail-icon">▥</span><span>Tipo de red</span><strong>{{ selectedSim.tipo_red || 'No disponible' }}</strong></div>
            <div class="detail-item status-detail"><span class="detail-icon">✓</span><span>Estado</span><strong>{{ selectedSim.estado || (selectedSim.activo ? 'Activo' : 'Inactivo') }}</strong></div>
          </div>

        </template>

        <div v-else class="empty-detail">
          <h4>Selecciona una SIM</h4>
          <p>Se mostrará aquí toda la información técnica, consumo y límite de datos.</p>
        </div>
      </aside>
    </div>

    <div v-if="sims.length === 0" class="empty-state">
      <p>No hay SIMs registradas aún</p>
      <small>Las SIMs aparecerán aquí cuando se registren dispositivos</small>
    </div>

    <div v-if="editingSim" class="modal-backdrop" @click.self="editingSim = false">
      <form class="edit-modal" @submit.prevent="saveEdit">
        <div class="modal-heading">
          <div><p class="eyebrow">Editar línea</p><h3>{{ editForm.numero_telefonico || 'SIM seleccionada' }}</h3></div>
          <button type="button" class="modal-close" aria-label="Cerrar" @click="editingSim = false">×</button>
        </div>
        <label>Número de teléfono<input v-model="editForm.numero_telefonico" type="text" /></label>
        <label>ICCID<input v-model="editForm.iccid" type="text" /></label>
        <label>País<input v-model="editForm.pais" type="text" /></label>
        <label>Tecnología<input v-model="editForm.tecnologia" type="text" /></label>
        <label class="edit-check"><input v-model="editForm.activo" type="checkbox" /> SIM activa</label>
        <div class="modal-actions">
          <button type="button" class="secondary-btn" @click="editingSim = false">Cancelar</button>
          <button type="submit" class="primary-btn" :disabled="savingEdit">{{ savingEdit ? 'Guardando...' : 'Guardar cambios' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import api from '../services/api';

const sims = ref([]);
const selectedSim = ref(null);
const query = ref('');
const loading = ref(false);
const loadError = ref('');
const lastSync = ref('nunca');
const selectedMonth = ref(new Date().toISOString().slice(0, 7));
const consumptionRecords = ref([]);

const monthLabel = computed(() => {
  const [year, month] = selectedMonth.value.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString('es-MX', { month: 'long', year: 'numeric' });
});
const editingSim = ref(false);
const savingEdit = ref(false);
const editForm = reactive({ numero_telefonico: '', iccid: '', pais: '', tecnologia: '', activo: true });

const filteredSims = computed(() =>
  sims.value.filter((sim) =>
    `${sim.numero_telefonico || ''} ${sim.operador_nombre || ''} ${sim.iccid || ''} ${sim.sim_uuid || ''}`
      .toLowerCase()
      .includes(query.value.toLowerCase())
  )
);

async function loadSims() {
  loading.value = true;
  loadError.value = '';
  try {
    const [simsResponse, consumptionResponse, networksResponse] = await Promise.all([
      api.get('/sims/'),
      api.get('/consumos/'),
      api.get('/redes/'),
    ]);

    const simsList = Array.isArray(simsResponse.data) ? simsResponse.data : simsResponse.data?.results || [];
    const consumption = Array.isArray(consumptionResponse.data) ? consumptionResponse.data : consumptionResponse.data?.results || [];
    const networks = Array.isArray(networksResponse.data) ? networksResponse.data : networksResponse.data?.results || [];
    consumptionRecords.value = consumption;

    sims.value = simsList.map((sim) => {
      const lastSevenDays = Date.now() - (7 * 24 * 60 * 60 * 1000);
      const simConsumption = consumption.filter((c) => c.sim === sim.id);
      const dailyConsumption = simConsumption.filter((c) =>
        c.periodo === 'diario' && c.fecha && new Date(c.fecha).getTime() >= lastSevenDays
      );
      const sevenDayConsumption = dailyConsumption.length ? dailyConsumption : simConsumption.filter((c) =>
        c.periodo === 'semanal' && c.fecha && new Date(c.fecha).getTime() >= lastSevenDays
      );
      const consumo_datos_movil = sevenDayConsumption.reduce((sum, c) => sum + Number(c.consumo_datos_movil || 0), 0);
      const today = new Date();
      const todayKey = `${today.getFullYear()}-${today.getMonth()}-${today.getDate()}`;
      const todayRecord = dailyConsumption.find((c) => {
        const date = new Date(c.fecha);
        return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}` === todayKey;
      });
      const consumo_datos_movil_hoy = Number(todayRecord?.consumo_datos_movil || 0);
      const consumo_wifi = 0;
      return {
        ...sim,
        consumo_datos_movil,
        consumo_datos_movil_hoy,
        consumo_wifi,
        operador_nombre: sim.operador_nombre || sim.operador?.nombre || (typeof sim.operador === 'string' ? sim.operador : 'N/A'),
        tipo_red: networks
          .filter((network) => network.sim === sim.id)
          .sort((a, b) => new Date(b.fecha_hora || 0) - new Date(a.fecha_hora || 0))[0]?.tipo_conexion || sim.tecnologia || null,
      };
    });

    if (!selectedSim.value && sims.value.length) {
      selectedSim.value = sims.value[0];
    }
    lastSync.value = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit', hour12: true });
  } catch (error) {
    console.error('Error cargando SIMs:', error);
    sims.value = [];
    loadError.value = error.response?.status === 401
      ? 'Tu sesión no está autenticada.'
      : 'No fue posible cargar las SIMs.';
  } finally {
    loading.value = false;
  }
}

function totalUsed(sim) {
  return Number(sim?.consumo_datos_movil || 0);
}

function monthlyUsed(sim) {
  return consumptionRecords.value
    .filter((item) => item.sim === sim?.id && item.fecha?.slice(0, 7) === selectedMonth.value)
    .reduce((sum, item) => sum + Number(item.consumo_datos_movil || 0), 0);
}

function todayUsed(sim) {
  return Number(sim?.consumo_datos_movil_hoy || 0);
}

function simType(sim) {
  return sim?.esim ? 'eSIM' : 'SIM física';
}

async function exportMonthlyReport() {
  if (!selectedSim.value) return;
  const [year, month] = selectedMonth.value.split('-');
  try {
    const response = await api.get(`/reportes/sims/${selectedSim.value.id}/exportar/`, {
      params: { anio: year, mes: month, formato: 'xlsx' },
      responseType: 'blob',
    });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `sim-${selectedSim.value.id}-${selectedMonth.value}.xlsx`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exportando reporte mensual:', error);
    window.alert('No fue posible generar el reporte Excel.');
  }
}

async function exportDevicesReport() {
  const [year, month] = selectedMonth.value.split('-');
  try {
    const response = await api.get('/reportes/dispositivos/exportar/', {
      params: { anio: year, mes: month, formato: 'xlsx' },
      responseType: 'blob',
    });
    const url = URL.createObjectURL(response.data);
    const link = document.createElement('a');
    link.href = url;
    link.download = `dispositivos-${selectedMonth.value}.xlsx`;
    link.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Error exportando dispositivos:', error);
    window.alert('No fue posible generar el reporte de dispositivos.');
  }
}

function startEdit() {
  if (!selectedSim.value) return;
  Object.assign(editForm, {
    numero_telefonico: selectedSim.value.numero_telefonico || '',
    iccid: selectedSim.value.iccid || '',
    pais: selectedSim.value.pais || '',
    tecnologia: selectedSim.value.tecnologia || '',
    activo: selectedSim.value.activo !== false,
  });
  editingSim.value = true;
}

async function saveEdit() {
  if (!selectedSim.value) return;
  savingEdit.value = true;
  try {
    await api.put(`/sims/${selectedSim.value.id}/`, editForm);
    const selectedId = selectedSim.value.id;
    editingSim.value = false;
    await loadSims();
    selectedSim.value = sims.value.find((sim) => sim.id === selectedId) || null;
  } catch (error) {
    console.error('Error actualizando la SIM:', error);
    window.alert('No fue posible guardar los cambios de la SIM.');
  } finally {
    savingEdit.value = false;
  }
}

function formatDate(dateString) {
  if (!dateString) return 'Sin fecha';
  const date = new Date(dateString);
  return date.toLocaleString('es-ES');
}

async function deleteSim(sim) {
  const nombre = sim.numero_telefonico || sim.iccid || 'esta SIM';
  const confirmar = window.confirm(`¿Seguro que deseas eliminar ${nombre}?\n\nEsta acción no se puede deshacer.`);

  if (!confirmar) return;

  try {
    await api.delete(`/sims/${sim.id}/`);
    if (selectedSim.value?.id === sim.id) {
      selectedSim.value = null;
    }
    await loadSims();
  } catch (error) {
    console.error('Error al eliminar la SIM:', error);
  }
}

function selectDetail(sim) {
  selectedSim.value = sim;
}

let refreshTimer = null;

onMounted(() => {
  loadSims();
  refreshTimer = setInterval(loadSims, 30000);
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<style scoped>
.sims-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 6px 2px 18px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 8px 4px;
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #64748b;
  font-size: 0.75rem;
  font-weight: 800;
}

.topbar h2 {
  margin: 6px 0 0;
  font-size: 2.05rem;
  font-weight: 800;
  color: #0f172a;
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sync-state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #15803d;
  font-size: 0.78rem;
  font-weight: 700;
  white-space: nowrap;
  padding: 8px 10px;
  border: 1px solid #DCE3EE;
  border-radius: 7px;
  background: #F4F6FA;
}

.sync-state i {
  width: 8px;
  height: 8px;
  display: inline-block;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
}

.sync-state.syncing i { background: #f59e0b; }
.sync-state.failed { color: #dc2626; }
.sync-state.failed i { background: #ef4444; }

.primary-btn {
  border: 0;
  background: linear-gradient(135deg, #1E9B48, #34C98F);
  color: white;
  border-radius: 12px;
  padding: 11px 17px;
  font-size: 0.92rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 10px 18px rgba(37, 99, 235, 0.16);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.primary-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 22px rgba(30, 155, 72, 0.22);
  filter: brightness(1.02);
}

.secondary-btn {
  border: 1px solid #dfe7f2;
  background: white;
  color: #475569;
  border-radius: 10px;
  padding: 10px 15px;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.secondary-btn:hover {
  transform: translateY(-1px);
  border-color: #bfd0e7;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.06);
}

.delete-btn {
  border: 0;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-radius: 10px;
  padding: 10px 13px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, filter 0.18s ease;
}

.delete-btn:hover {
  transform: translateY(-1px);
  filter: brightness(1.02);
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(180px, 1fr));
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.94), rgba(248, 250, 252, 0.98));
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 8px 16px rgba(15, 23, 42, 0.03);
}

.card-green {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 100%);
}

.card-violet {
  background: linear-gradient(135deg, #f5f3ff 0%, #ffffff 100%);
}

.card-amber {
  background: linear-gradient(135deg, #fff7ed 0%, #ffffff 100%);
}

.card-blue {
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 100%);
}

.stat-icon {
  width: 46px;
  height: 46px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 1.2rem;
  font-weight: 800;
}

.stat-icon.green {
  background: linear-gradient(135deg, #34d399, #10b981);
}

.stat-icon.violet {
  background: linear-gradient(135deg, #a78bfa, #7c3aed);
}

.stat-icon.amber {
  background: linear-gradient(135deg, #fbbf24, #f97316);
}

.stat-icon.blue {
  background: linear-gradient(135deg, #34C98F, #1E9B48);
}

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-body span {
  color: #475569;
  font-size: 0.82rem;
  font-weight: 600;
}

.stat-body strong {
  font-size: 1.5rem;
  line-height: 1;
  color: #0f172a;
}

.neutral-text {
  color: #64748b;
}

.sim-layout {
  display: grid;
  grid-template-columns: minmax(330px, 1fr) minmax(420px, 1.45fr);
  gap: 20px;
  align-items: start;
}

.panel {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(148, 163, 184, 0.14);
  border-radius: 18px;
  padding: 18px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.03);
}

.inventory-panel {
  min-height: 600px;
}

.panel-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.panel h3 {
  margin: 0;
  font-size: 1.12rem;
  color: #0f172a;
}

.search-box {
  margin-bottom: 14px;
}

.search-box input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 11px;
  border: 1px solid #d8e2ef;
  font-size: 0.9rem;
  background: #f8fafc;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sim-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  min-height: 92px;
  padding: 12px 14px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8fafc, #eef7ff);
  border: 1px solid rgba(148, 163, 184, 0.12);
  transition: all 0.2s ease;
}

.sim-row:hover,
.sim-row.active {
  background: linear-gradient(135deg, #eef8ff, #ebf5ff);
  border-color: rgba(37, 99, 235, 0.2);
  transform: translateY(-1px);
}

.sim-info-block {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 4px;
}

.sim-info-block strong {
  display: block;
  color: #0f172a;
  font-size: 1rem;
  font-weight: 800;
  line-height: 1.3;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sim-info-block small {
  display: block;
  color: #64748b;
  font-size: 0.82rem;
  line-height: 1.4;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.status-badge {
  padding: 6px 10px;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 700;
  white-space: nowrap;
}

.status-badge.active {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  color: #166534;
}

.status-badge.inactive {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  color: #991b1b;
}

.detail-btn {
  border: 0;
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
  border-radius: 8px;
  padding: 9px 12px;
  font-weight: 700;
  cursor: pointer;
  font-size: 0.84rem;
}

.empty-card {
  border: 2px dashed #d8e2ef;
  background: #f8fafc;
  border-radius: 12px;
  padding: 34px 18px;
  text-align: center;
  color: #64748b;
  font-size: 0.92rem;
}

.detail-panel {
  background: linear-gradient(135deg, #f8fbff 0%, #f5f3ff 100%);
  min-height: 600px;
}

.detail-panel.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc, #f4f7fb);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(37, 99, 235, 0.12);
}

.device-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.panel-header h3 {
  margin: 0;
  font-size: 1.38rem;
  color: #0f172a;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.live-status {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 7px 11px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.live-status.active {
  background: linear-gradient(135deg, #dcfce7, #bbf7d0);
  color: #166534;
}

.live-status.inactive {
  background: linear-gradient(135deg, #fee2e2, #fecaca);
  color: #991b1b;
}

.device-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 22px;
}

.device-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  width: fit-content;
  min-width: 180px;
  max-width: 100%;
  padding: 10px 14px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(148, 163, 184, 0.14);
}

.sim-badge-compact {
  flex: 0 0 170px;
  min-width: 170px;
}

.sim-badge-wide {
  flex: 1 1 0;
  min-width: 240px;
}

.device-icon {
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  background: linear-gradient(135deg, #dbeafe, #e0e7ff);
  font-size: 1.2rem;
  flex-shrink: 0;
}

.device-icon.secondary {
  background: linear-gradient(135deg, #dcfce7, #d9f99d);
}

.device-badge small {
  display: block;
  color: #64748b;
  font-size: 0.7rem;
  margin-bottom: 2px;
}

.device-badge strong {
  color: #0f172a;
  font-size: 1rem;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.summary-card {
  padding: 14px 16px;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.summary-card.blue {
  background: linear-gradient(135deg, rgba(191, 219, 254, 0.35), rgba(255, 255, 255, 0.75));
}

.summary-card.green {
  background: linear-gradient(135deg, rgba(220, 252, 231, 0.4), rgba(255, 255, 255, 0.72));
}

.summary-card.amber {
  background: linear-gradient(135deg, rgba(254, 243, 199, 0.4), rgba(255, 255, 255, 0.75));
}

.summary-card.violet {
  background: linear-gradient(135deg, rgba(233, 213, 255, 0.35), rgba(255, 255, 255, 0.72));
}

.metric-kicker {
  color: #475569;
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-weight: 800;
}

.summary-card strong {
  color: #0f172a;
  font-size: 0.96rem;
  line-height: 1.45;
  word-break: break-word;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px 11px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.detail-item span {
  color: #64748b;
  font-size: 0.73rem;
  font-weight: 700;
}

.detail-item strong {
  color: #0f172a;
  font-weight: 700;
  word-break: break-word;
}

.limit-section {
  margin-top: 18px;
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(239,246,255,0.9));
  border: 1px solid rgba(148, 163, 184, 0.12);
}

.limit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.limit-label {
  font-size: 0.76rem;
  font-weight: 700;
  color: #1e40af;
}

.limit-text {
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f172a;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(201, 217, 237, 0.5);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: all 0.3s ease;
}

.limit-remaining {
  display: block;
  font-size: 0.74rem;
  color: #64748b;
  text-align: right;
}

.empty-state {
  grid-column: 1 / -1;
  padding: 52px 18px;
  text-align: center;
  border-radius: 18px;
  background: linear-gradient(135deg, #f8fafc, #eef6ff);
  border: 2px dashed #bfdbfe;
}

.empty-state p {
  margin: 0 0 8px;
  font-size: 1.1rem;
  font-weight: 700;
  color: #0f172a;
}

.empty-state small {
  color: #475569;
}

.empty-detail {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 260px;
  gap: 10px;
  color: #64748b;
  text-align: center;
}

.empty-detail-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  background: rgba(148, 163, 184, 0.08);
  display: grid;
  place-items: center;
  font-size: 1.4rem;
}

.empty-detail h4 {
  margin: 0;
  color: #0f172a;
}

.empty-detail p {
  margin: 0;
  max-width: 270px;
  line-height: 1.5;
}

.uuid {
  font-family: 'Monaco', 'Courier New', monospace;
  font-size: 0.75rem;
}

.active-text {
  color: #059669;
  font-weight: 700;
}

.inactive-text {
  color: #dc2626;
  font-weight: 700;
}

@media (max-width: 1100px) {
  .sim-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .topbar,
  .panel-header,
  .header-actions,
  .sim-row,
  .limit-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .stats-grid,
  .summary-grid,
  .detail-grid {
    grid-template-columns: 1fr;
  }

  .row-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}

.sims-page { gap: 18px; padding: 24px; border: 1px solid #DCE3EE; border-radius: 12px; background: linear-gradient(180deg, #F4F6FA, #EDF0F7); }
.topbar { padding: 0 0 16px; border-bottom: 1px solid #DCE3EE; }
.topbar h2 { color: #121A2B; font-size: 2rem; }
.eyebrow { color: #1E9B48; }
.primary-btn { background: #1E9B48; border-radius: 7px; box-shadow: 0 7px 14px rgba(0, 127, 95, 0.18); }
.primary-btn:hover { background: #167A39; }
.panel { padding: 20px; border-color: #DCE3EE; border-radius: 10px; box-shadow: 0 6px 18px rgba(0, 67, 49, 0.05); }
.inventory-panel { background: #fff; }
.detail-panel { background: linear-gradient(145deg, #E6F6EC, #F4F6FA); }
.search-box input { border-color: #DCE3EE; background: #F4F6FA; border-radius: 7px; }
.sim-row { border-color: #DCE3EE; border-radius: 8px; background: #F4F6FA; }
.sim-row:hover, .sim-row.active { border-color: #3A6FB0; background: #E9EEFA; transform: none; }
.detail-btn { background: #E6F6EC; color: #167A39; border-radius: 7px; }
.panel-header { border-color: #DCE3EE; }
.panel-header h3 { color: #121A2B; }
.device-badge, .summary-card, .detail-item, .limit-section { border-color: #DCE3EE; border-radius: 8px; }
.device-icon { background: #dff3e9; }
.summary-card.blue { background: #E9EEFA; }
.summary-card.violet { background: #fff1ef; }
.summary-card strong, .detail-item strong { color: #121A2B; }
.limit-section { background: #fff; }
.limit-label { color: #1E9B48; }
.progress-bar { background: #dcece4; }
.progress-fill { background: #1E9B48 !important; }

@media (max-width: 640px) {
  .sims-page { padding: 16px 12px; }
  .topbar h2 { font-size: 1.55rem; }
}

.back-link { margin: 0 0 10px; color: #1E9B48; font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.08em; display: inline-flex; align-items: center; gap: 5px; cursor: pointer; }
.sim-title-icon, .sim-section-icon { display: grid; place-items: center; flex: 0 0 auto; width: 42px; height: 42px; border-radius: 10px; color: #1E9B48; background: #E6F6EC; font-size: 1.35rem; }
.sim-page-title .page-caption { margin: 5px 0 0; }
.sim-page-title h2 { margin: 0; }
.sim-section-icon { width: 36px; height: 36px; font-size: 1.15rem; }
.panel-topline > div:first-child { display: flex; align-items: center; gap: 12px; }
.sim-count { display: grid; place-items: center; min-width: 24px; height: 24px; padding: 0 7px; border-radius: 999px; color: #1E9B48; background: #E6F6EC; font-size: 0.76rem; font-weight: 800; }
.list-heading-actions { display: flex; align-items: center; gap: 8px; margin-left: auto; }
.devices-report-btn { border: 1px solid #C7D3E8; padding: 7px 9px; border-radius: 6px; background: #E6F6EC; color: #167A39; font-size: 0.7rem; font-weight: 800; cursor: pointer; }
.devices-report-btn:hover { background: #d8f1e4; }
.sim-row { position: relative; padding-left: 54px; border-left: 3px solid transparent; }
.sim-row.active { border-left-color: #1E9B48; }
.sim-row-icon { position: absolute; left: 14px; top: 50%; transform: translateY(-50%); width: 30px; height: 30px; display: grid; place-items: center; border-radius: 9px; color: #1E9B48; background: #E6F6EC; font-size: 1rem; }
.sim-info-block strong { color: #121A2B; }
.sim-info-block small { color: #5B6B82; }
.sim-row { padding: 14px; border-left-width: 3px; border-radius: 6px; background: #F4F6FA; }
.sim-row-icon { display: none; }
.sim-row .row-actions { gap: 8px; }
.sim-row .detail-btn { width: 30px; padding: 8px 0; font-size: 0; background: #E6F6EC; color: #167A39; border-radius: 6px; }
.sim-row .detail-btn::after { content: '›'; font-size: 1.2rem; line-height: 1; }
.sim-row .delete-btn { width: 30px; padding: 8px 0; font-size: 0; border-radius: 6px; background: #fff0ee; color: #b42318; }
.sim-row .delete-btn::after { content: '×'; font-size: 1.15rem; line-height: 1; }
.sim-row .status-badge { border-radius: 4px; background: #E6F6EC; color: #167A39; }
.detail-heading-icon { position: absolute; left: 0; top: 0; width: 38px; height: 38px; display: grid; place-items: center; border-radius: 10px; color: #1E9B48; background: #E6F6EC; font-size: 1.15rem; }
.device-title-wrap { position: relative; padding-left: 50px; }
.device-title-wrap .eyebrow { padding-top: 2px; }
.device-title-wrap h3 { font-size: 1.15rem; }
.operator-badge { margin-left: auto; display: flex; flex-direction: column; gap: 3px; padding: 8px 12px; border-radius: 8px; color: #1E9B48; background: #E6F6EC; }
.operator-badge small { color: #5B6B82; font-size: 0.66rem; }
.operator-badge strong { font-size: 0.8rem; }
.operator-badge-mobile { display: none; }
.summary-card { position: relative; min-height: 72px; justify-content: center; padding: 12px 14px 12px 58px; }
.summary-icon { position: absolute; left: 13px; top: 50%; transform: translateY(-50%); width: 35px; height: 35px; display: grid; place-items: center; border-radius: 10px; color: #1E9B48; background: rgba(255,255,255,0.72); font-size: 1.1rem; }
.summary-card.blue, .summary-card.green { background: #E6F6EC; }
.summary-card.amber { background: #fff8e7; }
.summary-card.violet { background: #fff0ef; }
.summary-card .metric-kicker { color: #5B6B82; text-transform: none; letter-spacing: 0; }
.detail-item { position: relative; min-height: 70px; justify-content: center; padding: 12px 12px 12px 58px; background: #f8fbfa; }
.detail-icon { position: absolute; left: 12px; top: 50%; transform: translateY(-50%); width: 34px; height: 34px; display: grid; place-items: center; border-radius: 9px; color: #5B6B82; background: #edf5f4; font-size: 1rem; font-weight: 700; }
.detail-item span:not(.detail-icon) { color: #5B6B82; font-size: 0.7rem; }
.detail-item strong { font-size: 0.82rem; }
.detail-item:first-child { background: #E6F6EC; border-color: #CBD8EC; }
.detail-item:first-child .detail-icon { color: #1E9B48; background: #E6F6EC; }
.status-detail { background: #E6F6EC; border-color: #CBD8EC; }
.status-detail .detail-icon { color: #1E9B48; background: #E6F6EC; }
.status-detail span:not(.detail-icon), .status-detail strong { color: #1E9B48; }
.live-status { border-radius: 7px; background: #E6F6EC; color: #1E9B48; }
.monthly-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 14px; margin: 0 0 18px; padding: 12px 14px; border: 1px solid #DCE3EE; border-radius: 8px; background: #EDF0F7; }
.monthly-toolbar strong { display: block; margin-top: 4px; color: #121A2B; font-size: 0.9rem; text-transform: capitalize; }
.monthly-actions { display: flex; align-items: center; gap: 8px; }
.monthly-actions input { padding: 8px 9px; border: 1px solid #DCE3EE; border-radius: 6px; background: #fff; color: #121A2B; }
.export-btn { border: 0; padding: 9px 12px; border-radius: 6px; background: #1E9B48; color: #fff; font-weight: 800; cursor: pointer; }
.export-btn:hover { background: #167A39; }
.modal-backdrop { position: fixed; inset: 0; z-index: 20; display: grid; place-items: center; padding: 20px; background: rgba(7, 38, 29, 0.34); }
.edit-modal { width: min(100%, 480px); display: grid; gap: 14px; padding: 24px; border: 1px solid #DCE3EE; border-radius: 12px; background: #fff; box-shadow: 0 22px 60px rgba(0, 67, 49, 0.22); }
.modal-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid #DCE3EE; }
.modal-heading h3 { margin: 0; color: #121A2B; }
.modal-close { border: 0; background: transparent; color: #5B6B82; font-size: 1.5rem; line-height: 1; cursor: pointer; }
.edit-modal label { display: grid; gap: 6px; color: #5B6B82; font-size: 0.76rem; font-weight: 700; }
.edit-modal input[type="text"] { width: 100%; padding: 10px 11px; border: 1px solid #DCE3EE; border-radius: 7px; background: #F4F6FA; color: #121A2B; }
.edit-modal input[type="text"]:focus { outline: 0; border-color: #008f68; box-shadow: 0 0 0 0.18rem rgba(0,143,104,0.12); }
.edit-check { display: flex !important; grid-template-columns: auto 1fr; align-items: center; gap: 8px !important; color: #121A2B !important; }
.edit-check input { width: auto; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 4px; }

@media (max-width: 640px) {
  .operator-badge { display: none; }
  .operator-badge-mobile { display: inline-flex; margin: 0; width: 100%; }
  .sim-page-title { align-items: flex-start; }
  .monthly-toolbar, .monthly-actions { align-items: stretch; flex-direction: column; }
  .monthly-actions input, .export-btn { width: 100%; }
}

/* Inventario de líneas */
.sims-page {
  position: relative;
  gap: 16px;
  padding: 28px;
  background: #F0F2F8;
  border: 1px solid #DCE3EE;
  border-radius: 8px;
}
.sims-page::before { position: absolute; top: 0; left: 28px; width: 64px; height: 4px; content: ''; background: #e1261c; }
.topbar { padding: 0 0 16px; border-bottom: 1px solid #DCE3EE; }
.topbar > div { min-width: 0; }
.topbar h2 { color: #121A2B; font-size: 2.15rem; letter-spacing: -0.02em; }
.page-caption { margin: 7px 0 0; color: #5B6B82; font-size: 0.88rem; }
.eyebrow { color: #1E9B48; }
.primary-btn { background: #1E9B48; border-radius: 6px; box-shadow: none; }
.primary-btn:hover { background: #167A39; }
.sim-layout { grid-template-columns: minmax(280px, 0.78fr) minmax(420px, 1.22fr); gap: 12px; }
.panel { padding: 22px; border: 1px solid #DCE3EE; border-radius: 8px; box-shadow: 0 5px 15px rgba(0, 67, 49, 0.045); }
.inventory-panel { min-height: 620px; background: #fff; }
.panel-topline > div { display: flex; align-items: center; gap: 12px; }
.panel-index { color: #e1261c; font-size: 0.72rem; font-weight: 900; }
.panel-topline { border-bottom: 1px solid #DCE3EE; padding-bottom: 14px; }
.search-box input { padding: 12px; background: #F4F6FA; border: 1px solid #DCE3EE; border-radius: 6px; }
.sim-row { padding: 14px; background: #F4F6FA; border: 1px solid #DCE3EE; border-left: 3px solid transparent; border-radius: 6px; }
.sim-row:hover, .sim-row.active { background: #E9EEFA; border-color: #9AACC9; border-left-color: #1E9B48; transform: none; }
.status-badge { border-radius: 4px; }
.status-badge.active { background: #E6F6EC; color: #167A39; }
.status-badge.inactive { background: #fff0ee; color: #b42318; }
.detail-btn { padding: 9px 12px; background: #E6F6EC; color: #167A39; border-radius: 6px; }
.detail-panel { min-height: 620px; background: #fff; border-top: 4px solid #1E9B48; }
.detail-panel.empty { background: #F8F9FC; border-top-color: #b8d5c7; }
.panel-header { margin-bottom: 20px; padding-bottom: 16px; border-color: #DCE3EE; }
.panel-header h3 { color: #121A2B; }
.live-status { border-radius: 4px; }
.live-status.active { background: #E6F6EC; color: #167A39; }
.live-status.inactive { background: #fff0ee; color: #b42318; }
.device-badge, .summary-card, .detail-item, .limit-section { border-radius: 6px; border-color: #DCE3EE; }
.device-badge { background: #F4F6FA; }
.device-icon { background: #E6F6EC; }
.summary-card { background: #F4F6FA; }
.summary-card.blue { background: #E9EEFA; }
.summary-card.amber { background: #fff8e8; }
.summary-card.violet { background: #fff0ee; }
.summary-card strong, .detail-item strong { color: #121A2B; }
.limit-section { background: #fff; }
.limit-label { color: #1E9B48; }
.progress-bar { background: #dcece4; }
.progress-fill { background: #1E9B48 !important; }

@media (max-width: 640px) {
  .sims-page { padding: 18px 12px; }
  .sims-page::before { left: 12px; }
  .topbar h2 { font-size: 1.7rem; }
}

.device-badge { width: 100%; padding: 13px 14px; background: #F4F6FA; }
.device-icon { color: #1E9B48; background: #e0f4e9; font-size: 1.25rem; }
</style>