<template>
  <div class="dashboard-page">
    <header class="topbar">
      <div class="welcome-heading">
        <p class="eyebrow">Panel de control</p>
        <h2>Bienvenido a Jamnex<span aria-hidden="true"></span></h2>
        <p>Sistema de Monitoreo y Administracion de Terminales Android</p>
      </div>
      <div class="topbar-actions">
        <span class="online-state"><i></i>En línea</span>
        <span class="date-state"><i>◷</i>{{ todayLabel }}</span>
        <span class="sync-state" :class="{ syncing: loading, failed: syncError }">
          <i></i>{{ syncError ? 'Sin conexión' : loading ? 'Sincronizando' : `Actualizado ${lastSync}` }}
        </span>
        <button class="primary-btn" :disabled="loading" @click="loadDashboard">Actualizar</button>
      </div>
    </header>

    <section class="stats-grid">
      <div class="stat-card stat-devices"><div class="stat-icon">▣</div><div class="stat-body"><span>Dispositivos</span><strong>{{ metrics.devices }}</strong><small>Total de dispositivos registrados</small></div></div>
      <div class="stat-card stat-sims"><div class="stat-icon">▤</div><div class="stat-body"><span>SIMs</span><strong>{{ metrics.sims }}</strong><small>Total de SIMs activas</small></div></div>
      <div class="stat-card stat-online"><div class="stat-icon">▥</div><div class="stat-body"><span>En línea</span><strong>{{ metrics.connected }}</strong><small>Dispositivos conectados</small></div></div>
      <div class="stat-card stat-data"><div class="stat-icon">▤</div><div class="stat-body"><span>Datos móviles usados</span><strong>{{ formatMb(metrics.mobile) }}</strong><small>Consumo total del periodo</small></div></div>
    </section>

    <section class="command-grid">
      <div class="command-hero">
        <div class="hero-heading"><div><span class="hero-kicker">▥ &nbsp; Red móvil</span><h3>Consumo acumulado</h3></div><span class="hero-period">◷ &nbsp; Este mes</span></div>
        <strong class="hero-value">{{ formatMb(metrics.mobile) }}</strong>
        <p>{{ metrics.sims }} SIM{{ metrics.sims === 1 ? '' : 's' }} activa{{ metrics.sims === 1 ? '' : 's' }}</p>
        <div class="hero-chart" aria-hidden="true"><span v-for="day in 7" :key="day" :style="{ height: `${metrics.mobile ? 20 + (day * 5) : 5}px` }"></span></div>
        <div class="hero-footer"><span>Últimos 7 días</span><span class="hero-note">✓ Sin consumo crítico</span></div>
      </div>

      <div class="attention-panel">
        <div class="attention-heading"><div><span class="hero-kicker">♧ &nbsp; Atención</span><h3>SIM con mayor consumo</h3></div><router-link to="/sims">Ver todas →</router-link></div>
        <div class="attention-main"><div class="attention-icon">▥</div><div><strong>{{ topSim.label }}</strong><p>{{ topSim.value ? 'Línea con mayor consumo en el periodo.' : 'No se ha registrado consumo en el periodo.' }}</p><b>+{{ formatMb(topSim.value) }}</b><small>{{ formatMb(topSim.value) }}</small></div></div>
        <div class="attention-footer">ⓘ &nbsp; El consumo de datos móviles se actualizará en tiempo real según la actividad de los dispositivos.</div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue';
import api from '../services/api';

const loading = ref(false);
const lastSync = ref('nunca');
const syncError = ref(false);
const topSim = ref({ label: 'Sin datos', value: 0 });
const todayLabel = new Date().toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
const metrics = reactive({ devices: 0, sims: 0, connected: 0, stale: 0, mobile: 0, wifi: 0, consumption: 0 });

function asList(data) {
  return Array.isArray(data) ? data : data?.results || data?.value || [];
}

async function loadDashboard() {
  loading.value = true;
  syncError.value = false;
  try {
    const [devicesResponse, simsResponse, consumptionResponse] = await Promise.all([
      api.get('/dispositivos/'),
      api.get('/sims/'),
      api.get('/consumos/'),
    ]);
    
    const devices = asList(devicesResponse.data);
    const sims = asList(simsResponse.data);
    const consumption = asList(consumptionResponse.data);
    
    metrics.devices = devices.length;
    metrics.sims = sims.length;
    metrics.connected = devices.filter((item) => item.activo).length;
    metrics.mobile = consumption.reduce((sum, item) => sum + Number(item.consumo_datos_movil || 0), 0);
    metrics.wifi = consumption.reduce((sum, item) => sum + Number(item.consumo_wifi || 0), 0);
    metrics.consumption = metrics.mobile;
    const consumptionBySim = consumption.reduce((result, item) => {
      const key = item.sim || item.dispositivo || 'Sin asignar';
      result[key] = (result[key] || 0) + Number(item.consumo_datos_movil || 0);
      return result;
    }, {});
    const [topSimId, topSimValue] = Object.entries(consumptionBySim).sort((a, b) => b[1] - a[1])[0] || ['Sin datos', 0];
    const sim = sims.find((item) => String(item.id) === String(topSimId));
    topSim.value = { label: sim?.numero_telefonico || sim?.operador_nombre || (topSimId === 'Sin asignar' ? 'Sin SIM asignada' : `SIM ${topSimId}`), value: topSimValue };
    lastSync.value = new Date().toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
  } catch (error) {
    console.error(error);
    syncError.value = true;
  } finally {
    loading.value = false;
  }
}

function formatMb(value) {
  const amount = Number(value || 0);
  return amount >= 1024 ? `${(amount / 1024).toFixed(1)} GB` : `${amount.toFixed(1)} MB`;
}

let refreshTimer = null;

onMounted(() => {
  loadDashboard();
  refreshTimer = setInterval(loadDashboard, 30000);
});

onBeforeUnmount(() => {
  if (refreshTimer) clearInterval(refreshTimer);
});
</script>

<style scoped>
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(180deg, #F4F6FA 0%, #EDF0F7 100%);
  border-radius: 24px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.topbar-caption {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 0.88rem;
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
}

.sync-state i,
.device-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12);
}

.sync-state.syncing i { background: #f59e0b; }
.sync-state.failed { color: #dc2626; }
.sync-state.failed i { background: #ef4444; }

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #1E9B48;
  font-size: 0.85rem;
  font-weight: 800;
}

.topbar h2 {
  margin: 4px 0 0;
  font-size: 1.8rem;
  font-weight: 800;
  color: #0f172a;
}

.primary-btn {
  border: 0;
  background: linear-gradient(135deg, #1E9B48, #00a878);
  color: white;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 8px 16px rgba(0, 127, 95, 0.22);
}

.primary-btn:disabled {
  cursor: wait;
  opacity: 0.65;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: white;
  border-radius: 14px;
  border: 1px solid rgba(148, 163, 184, 0.15);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}

.card-blue { background: linear-gradient(135deg, #effaf5, #ffffff); }
.card-green { background: linear-gradient(135deg, #ecfdf5, #ffffff); }
.card-violet { background: linear-gradient(135deg, #fff4f2, #ffffff); }
.card-green-light { background: linear-gradient(135deg, #dcfce7, #ffffff); }

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 1.3rem;
  flex-shrink: 0;
}

.stat-icon.blue { background: linear-gradient(135deg, #00a878, #1E9B48); }
.stat-icon.green { background: linear-gradient(135deg, #34d399, #10b981); }
.stat-icon.violet { background: linear-gradient(135deg, #ef4444, #c81e1e); }

.stat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.stat-body span {
  color: #64748b;
  font-size: 0.8rem;
  font-weight: 600;
}

.stat-body strong {
  font-size: 1.6rem;
  line-height: 1;
  color: #0f172a;
  font-weight: 800;
}

.content-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}

.signal-strip {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  overflow: hidden;
  background: #dbe4ee;
  border: 1px solid #dbe4ee;
  border-radius: 14px;
}

.signal-strip > div {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 18px;
  background: rgba(255, 255, 255, 0.92);
}

.strip-label,
.panel-meta {
  color: #64748b;
  font-size: 0.76rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.signal-strip strong {
  color: #0f172a;
  font-size: 1.35rem;
}

.signal-strip strong.warning { color: #d97706; }
.signal-strip small { color: #94a3b8; }

.panel {
  background: white;
  border: 1px solid rgba(148, 163, 184, 0.15);
  border-radius: 14px;
  padding: 18px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.04);
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  padding-bottom: 12px;
}

.panel-meta {
  margin-left: auto;
  text-transform: none;
  letter-spacing: 0;
  font-weight: 600;
}

.panel-subtitle {
  margin: 5px 0 0;
  color: #94a3b8;
  font-size: 0.8rem;
}

.panel-link {
  margin-left: auto;
  color: #1E9B48;
  font-size: 0.82rem;
  font-weight: 700;
  text-decoration: none;
}

.device-list {
  display: grid;
  gap: 2px;
}

.device-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 4px;
  border-bottom: 1px solid #eef2f7;
}

.device-row:last-child { border-bottom: 0; }
.device-dot { flex: 0 0 auto; background: #94a3b8; box-shadow: 0 0 0 4px rgba(148, 163, 184, 0.12); }
.device-dot.online { background: #22c55e; box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.12); }

.device-name {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 3px;
}

.device-name strong {
  overflow: hidden;
  color: #1e293b;
  font-size: 0.9rem;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.device-name small { color: #94a3b8; font-size: 0.76rem; }
.device-status { color: #64748b; font-size: 0.76rem; font-weight: 700; }
.device-status.online { color: #15803d; }

.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #0f172a;
}

.bar-chart {
  height: 160px;
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 8px 0;
}

.bar-column {
  flex: 1;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  align-items: center;
  gap: 6px;
}

.bar {
  width: 100%;
  max-width: 36px;
  min-height: 6px;
  border-radius: 6px 6px 2px 2px;
  background: linear-gradient(180deg, #34d399, #10b981);
  transition: all 0.3s ease;
}

.bar:hover {
  opacity: 0.8;
  transform: scaleY(1.05);
}

.bar-column small {
  color: #64748b;
  font-size: 0.7rem;
  font-weight: 600;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: linear-gradient(135deg, #f8fafc, #f0f9ff);
  border-radius: 10px;
  border: 1px solid rgba(37, 99, 235, 0.1);
}

.status-label {
  color: #475569;
  font-weight: 600;
  font-size: 0.9rem;
}

.status-value {
  color: #34C98F;
  font-weight: 700;
  font-size: 1.1rem;
}

.status-value.alert {
  color: #ef4444;
}

.empty-list {
  padding: 20px;
  text-align: center;
  color: #94a3b8;
  background: rgba(248, 250, 252, 0.6);
  border-radius: 10px;
  border: 1px dashed #cbd5e1;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .signal-strip {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .topbar h2 {
    font-size: 1.4rem;
  }

  .topbar,
  .topbar-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .topbar-actions { width: 100%; }
  .primary-btn { width: 100%; }

  .bar-chart {
    height: 140px;
  }
}

.welcome-heading h2 { margin: 4px 0 2px; font-size: 1.75rem; color: #102a22; }
.welcome-heading > p:last-child { margin: 0; color: #5B6B82; font-size: 0.78rem; }
.online-state, .date-state { display: inline-flex; align-items: center; gap: 6px; color: #526a61; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
.online-state { padding: 7px 9px; border: 1px solid #DCE3EE; border-radius: 7px; background: #F4F6FA; color: #15803d; }
.online-state i, .date-state i { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; font-style: normal; }
.date-state i { width: auto; height: auto; background: none; color: #64748b; font-size: 1rem; }
.stats-grid { gap: 12px; }
.stat-card { min-height: 102px; padding: 14px; border-radius: 8px; box-shadow: 0 5px 14px rgba(15, 23, 42, 0.04); }
.stat-card b { margin-left: auto; color: #6c8790; font-size: 1.4rem; font-weight: 400; }
.stat-card .stat-icon { width: 40px; height: 40px; border-radius: 10px; color: #1E9B48; background: #d6f7e6; font-size: 1.3rem; }
.stat-sims .stat-icon { color: #1478bd; background: #dceeff; }
.stat-online .stat-icon { color: #7045d9; background: #ebe2ff; }
.stat-data .stat-icon { color: #078b90; background: #d8f7f5; }
.stat-body { gap: 4px; }
.stat-body span { color: #26423a; font-size: 0.72rem; }
.stat-body strong { font-size: 1.35rem; }
.stat-body small { color: #5B6B82; font-size: 0.65rem; }
.command-grid { grid-template-columns: 1.35fr 1fr; gap: 12px; }
.command-hero { min-height: 250px; padding: 20px 22px; border-radius: 9px; background: linear-gradient(125deg, #167A39, #008c68); }
.hero-heading h3 { margin: 8px 0 0; font-size: 1rem; }
.hero-period { padding: 7px 10px; border: 1px solid rgba(255,255,255,0.22); border-radius: 6px; color: #e4fff4; font-size: 0.7rem; }
.hero-value { margin: 22px 0 2px; font-size: 2.7rem; letter-spacing: -0.03em; }
.hero-chart { height: 55px; display: flex; align-items: flex-end; gap: 2px; margin-top: 14px; border-bottom: 1px solid rgba(255,255,255,0.2); background: repeating-linear-gradient(90deg, transparent 0, transparent calc(14.28% - 1px), rgba(255,255,255,0.08) calc(14.28% - 1px), rgba(255,255,255,0.08) 14.28%); }
.hero-chart span { flex: 1; max-width: 7px; margin: 0 auto; border-radius: 5px 5px 0 0; background: #72e0ba; box-shadow: 0 0 0 3px rgba(114,224,186,0.12); }
.hero-footer { margin-top: 12px; padding-top: 0; border-top: 0; }
.hero-note { padding: 7px 10px; border-radius: 8px; background: rgba(84, 218, 155, 0.25); color: #e4fff4; }
.attention-panel { min-height: 250px; padding: 20px; border: 1px solid #e1ece7; border-radius: 9px; background: #fff; box-shadow: 0 5px 14px rgba(15, 23, 42, 0.04); }
.attention-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
.attention-heading h3 { margin: 8px 0 0; color: #173b30; font-size: 0.95rem; }
.attention-heading a { color: #1E9B48; font-size: 0.68rem; font-weight: 800; text-decoration: none; }
.attention-main { display: flex; align-items: center; gap: 14px; margin: 23px 0; }
.attention-icon { width: 46px; height: 46px; display: grid; place-items: center; border-radius: 50%; background: #e4f8ee; color: #1E9B48; font-size: 1.4rem; }
.attention-main strong { display: block; color: #26423a; font-size: 0.88rem; }
.attention-main p { margin: 4px 0 6px; color: #8a9a94; font-size: 0.68rem; }
.attention-main b { display: block; color: #1E9B48; font-size: 1.25rem; }
.attention-main small { color: #8a9a94; font-size: 0.66rem; }
.attention-footer { padding-top: 14px; border-top: 1px solid #edf2ef; color: #5B6B82; font-size: 0.68rem; line-height: 1.45; }

@media (max-width: 760px) {
  .welcome-heading h2 { font-size: 1.45rem; }
  .topbar-actions { width: 100%; flex-wrap: wrap; }
  .command-grid { grid-template-columns: 1fr; }
  .online-state, .date-state { display: none; }
}

.dashboard-page {
  position: relative;
  gap: 18px;
  padding: 30px;
  border: 1px solid #DCE3EE;
  border-radius: 12px;
}

.dashboard-page::before {
  position: absolute;
  top: 0;
  left: 30px;
  width: 72px;
  height: 4px;
  content: '';
  background: #e1261c;
}

.topbar { padding-bottom: 8px; }
.topbar h2 { font-size: 2.1rem; letter-spacing: -0.02em; }
.topbar-caption { color: #5B6B82; }
.sync-state { padding: 8px 10px; border: 1px solid #DCE3EE; border-radius: 7px; background: #F4F6FA; }
.primary-btn { border-radius: 7px; }

.command-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(270px, 0.8fr);
  gap: 16px;
}

.command-hero {
  min-height: 218px;
  padding: 24px 26px;
  color: #fff;
  background: linear-gradient(125deg, #167A39, #008c68);
  border-radius: 10px;
  box-shadow: 0 12px 22px rgba(0, 88, 63, 0.16);
}

.hero-heading,
.hero-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.hero-kicker { color: #c4efde; font-size: 0.78rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.hero-live { color: #e4fff4; font-size: 0.68rem; font-weight: 800; }
.hero-live i { display: inline-block; width: 7px; height: 7px; margin-right: 5px; border-radius: 50%; background: #a7f3d0; }
.hero-value { display: block; margin: 34px 0 4px; font-size: 4.2rem; font-weight: 800; letter-spacing: -0.05em; }
.command-hero p { margin: 0; color: #d7f3e9; }
.hero-footer { margin-top: 30px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.2); color: #b7e4d4; font-size: 0.78rem; }

.quick-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1px;
  overflow: hidden;
  background: #DCE3EE;
  border: 1px solid #DCE3EE;
  border-radius: 10px;
}

.quick-metric { display: flex; min-height: 108px; flex-direction: column; justify-content: center; padding: 16px 18px; background: #fff; }
.quick-metric span { color: #5B6B82; font-size: 0.74rem; font-weight: 800; text-transform: uppercase; }
.quick-metric strong { margin-top: 7px; color: #121A2B; font-size: 1.7rem; }
.quick-metric small { color: #94a79f; }
.green-text { color: #008c68 !important; }
.warning { color: #c2410c !important; }

.content-grid { grid-template-columns: minmax(0, 1.35fr) minmax(240px, 0.65fr); }
.panel { padding: 20px; border: 1px solid #DCE3EE; border-radius: 10px; box-shadow: 0 6px 18px rgba(0, 67, 49, 0.05); }
.panel-header { margin-bottom: 14px; padding-bottom: 14px; border-color: #e1eee8; }
.panel-header > div { display: flex; align-items: center; gap: 9px; }
.section-number { color: #e1261c; font-size: 0.7rem; font-weight: 900; }
.panel-meta { color: #81948c; }
.bar { background: linear-gradient(180deg, #00a878, #167A39); border-radius: 3px 3px 1px 1px; }
.status-item { padding: 14px; background: #f6fbf8; border-color: #DCE3EE; border-radius: 7px; }
.status-value { color: #1E9B48; }
.devices-panel { margin-top: 0; }

.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.overview-panel {
  min-height: 164px;
  padding: 22px 24px;
  border: 1px solid #DCE3EE;
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 6px 18px rgba(0, 67, 49, 0.05);
}

.connection-panel { background: linear-gradient(135deg, #fff, #effaf5); }
.usage-panel { background: linear-gradient(135deg, #167A39, #008c68); color: #fff; }
.overview-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.overview-kicker { color: #5B6B82; font-size: 0.7rem; font-weight: 800; letter-spacing: 0.08em; text-transform: uppercase; }
.usage-panel .overview-kicker { color: #b7e4d4; }
.overview-heading h3 { margin: 6px 0 0; color: #121A2B; font-size: 1.08rem; }
.usage-panel .overview-heading h3 { color: #fff; }
.overview-heading > strong { color: #1E9B48; font-size: 2rem; line-height: 1; }
.usage-dot { width: 10px; height: 10px; margin-top: 5px; border-radius: 50%; background: #a7f3d0; box-shadow: 0 0 0 5px rgba(167, 243, 208, 0.18); }
.connection-track { height: 10px; margin-top: 28px; overflow: hidden; border-radius: 5px; background: #d9ebe2; }
.connection-track span { display: block; height: 100%; border-radius: inherit; background: #1E9B48; transition: width 0.3s ease; }
.overview-footer { display: flex; justify-content: space-between; gap: 12px; margin-top: 12px; color: #5B6B82; font-size: 0.78rem; }
.usage-panel .overview-footer { color: #d7f3e9; }
.usage-value { display: block; margin-top: 22px; color: #fff; font-size: 2.25rem; }
.top-sim-panel { background: #fff; }
.top-sim-value { display: block; overflow: hidden; margin-top: 28px; color: #121A2B; font-size: 1.75rem; text-overflow: ellipsis; white-space: nowrap; }
.top-sim-panel .overview-footer a { color: #1E9B48; font-weight: 800; text-decoration: none; }

@media (max-width: 900px) {
  .command-grid { grid-template-columns: 1fr; }
  .overview-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .dashboard-page { padding: 18px 14px; }
  .dashboard-page::before { left: 14px; }
  .topbar h2 { font-size: 1.65rem; }
  .command-hero { padding: 20px; }
  .hero-value { margin-top: 28px; font-size: 2.6rem; }
  .quick-metrics { grid-template-columns: repeat(3, 1fr); }
  .quick-metric { min-height: 92px; padding: 12px 9px; }
  .quick-metric strong { font-size: 1.35rem; }
  .quick-metric span, .quick-metric small { font-size: 0.65rem; }
}
</style>