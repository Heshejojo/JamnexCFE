<template>
  <div v-if="auth.token" class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <div class="brand-logo-frame">
          <img class="brand-logo" src="/images/Logo1.jpg" alt="Comisión Federal de Electricidad" />
        </div>
        <div class="brand-copy">
          <small>Plataforma de control</small>
          <div class="brand-title">Agente CFE</div>
        </div>
      </div>

      <div class="nav-label">Módulos principales</div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-item" exact-active-class="active">
          <span aria-hidden="true">⌂</span>Dashboard
        </router-link>
        <router-link to="/dispositivos" class="nav-item" exact-active-class="active">
          <span aria-hidden="true">▣</span>Dispositivos
        </router-link>
        <router-link to="/sims" class="nav-item" exact-active-class="active">
          <span aria-hidden="true">▤</span>SIMs
        </router-link>
        <router-link to="/usuarios" class="nav-item" exact-active-class="active">
          <span aria-hidden="true">♙</span>Usuarios
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-pill">
          <div class="avatar">{{ initials }}</div>
          <div>
            <strong>{{ userName }}</strong>
            <small>{{ roleName }}</small>
          </div>
        </div>
        <button class="logout-btn" @click="logoutSession">Cerrar sesión</button>
      </div>
    </aside>

    <main class="main-panel">
      <router-view />
    </main>
  </div>

  <div v-else class="auth-wrapper">
    <router-view />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';

const auth = useAuthStore();
const router = useRouter();

const userName = computed(() => auth.user?.first_name || auth.user?.username || 'Administrador');
const roleName = computed(() => auth.user?.rol?.nombre || 'Superadmin');
const initials = computed(() => {
  const base = userName.value || 'A';
  return base
    .split(' ')
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('');
});

onMounted(async () => {
  if (auth.token) {
    await auth.fetchCurrentUser();
  }
});

function logoutSession() {
  auth.logout();
  router.push('/login');
}
</script>

<style scoped>
:global(body) {
  margin: 0;
  background: #F0F2F8;
  font-family: 'Poppins', 'Segoe UI', sans-serif;
  color: #1f2937;
}

* {
  box-sizing: border-box;
}

.app-shell {
  display: flex;
  min-height: 100vh;
  background: #F0F2F8;
}

.sidebar {
  width: 220px;
  background: linear-gradient(180deg, #16233A 0%, #0A121C 100%);
  color: white;
  padding: 20px 14px;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.brand-block {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 6px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.12);
}

.brand-logo {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
  object-position: center;
}

.brand-logo-frame {
  width: 56px;
  height: 56px;
  display: grid;
  flex-shrink: 0;
  place-items: center;
  overflow: hidden;
  border-radius: 10px;
  background: #fff;
  padding: 5px;
  box-shadow: 0 5px 14px rgba(0, 0, 0, 0.16);
}

.brand-logo-frame .brand-logo {
  border-radius: 4px;
}

.brand-title {
  margin-top: 4px;
  font-size: 1rem;
  font-weight: 700;
}

.brand-copy {
  min-width: 0;
}

.brand-block small {
  color: rgba(255,255,255,0.7);
  font-size: 0.66rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.nav-label {
  margin: 4px 8px 0;
  color: #8fcab7;
  font-size: 0.64rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.nav-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  text-decoration: none;
  color: rgba(255,255,255,0.8);
  min-height: 44px;
  padding: 11px 10px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 9px;
  font-weight: 600;
  transition: 0.2s ease;
}

.nav-item span {
  width: 22px;
  color: #b7e4d4;
  font-size: 1.15rem;
  text-align: center;
}

.nav-item:hover,
.nav-item.active {
  background: linear-gradient(135deg, rgba(0, 145, 105, 0.52), rgba(255,255,255,0.08));
  color: #fff;
  box-shadow: inset 0 0 0 1px rgba(148, 163, 184, 0.12);
}

.nav-item.active::after {
  width: 4px;
  height: 22px;
  margin-left: auto;
  content: '';
  border-radius: 2px;
  background: #e1261c;
}

.sidebar-footer {
  margin-top: auto;
  border-top: 1px solid rgba(255,255,255,0.12);
  padding-top: 18px;
}

.user-pill {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
  padding: 10px 12px;
  background: rgba(255,255,255,0.04);
  border-radius: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ef4444, #f59e0b);
  display: grid;
  place-items: center;
  font-size: 0.78rem;
  font-weight: 700;
}

.user-pill strong,
.user-pill small {
  display: block;
}

.user-pill small {
  color: rgba(255,255,255,0.7);
}

.logout-btn {
  width: 100%;
  border: 0;
  background: rgba(0, 127, 95, 0.18);
  color: white;
  border-radius: 10px;
  padding: 10px 12px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.2s ease;
}

.logout-btn:hover {
  background: rgba(0, 127, 95, 0.3);
}

.main-panel {
  flex: 1;
  padding: 24px;
  min-width: 0;
  overflow-x: hidden;
}

.auth-wrapper {
  min-height: 100vh;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #e9f5ef 0%, #f8fafc 52%, #fff1f1 100%);
}

@media (max-width: 760px) {
  .app-shell {
    display: block;
  }

  .sidebar {
    width: 100%;
    padding: 14px;
    gap: 12px;
  }

  .brand-block {
    padding: 4px 6px 12px;
  }

  .brand-logo-frame { width: 48px; height: 48px; }
  .brand-logo { width: 100%; height: 100%; }

  .nav-menu {
    display: flex;
    flex-direction: row;
    gap: 8px;
    overflow-x: auto;
    padding: 2px 0 5px;
    scrollbar-width: thin;
  }

  .nav-item {
    min-width: 118px;
    justify-content: flex-start;
    padding: 10px 12px;
    font-size: 0.72rem;
    white-space: nowrap;
  }

  .nav-item span { display: inline-block; }
  .sidebar-footer { display: none; }
  .main-panel { padding: 10px; }
}
</style>