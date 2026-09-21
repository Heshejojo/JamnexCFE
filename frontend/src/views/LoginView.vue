<template>
  <div class="login-shell">
    <div class="login-panel">
      <section class="login-aside">
        <div class="logo-frame">
          <img class="brand-logo" src="/images/Logo1.jpg" alt="Comisión Federal de Electricidad" />
        </div>
        <div class="aside-copy">
          <span class="aside-kicker">Sistema interno</span>
          <h1>JAMNEX</h1>
          <p>Monitorea dispositivos y líneas móviles desde un solo lugar.</p>
        </div>
        <div class="aside-line"></div>
        <small class="aside-footer">Comisión Federal de Electricidad</small>
      </section>

      <section class="login-content">
        <div class="welcome-copy">
          <span class="form-kicker">Acceso</span>
          <h2>Bienvenido</h2>
          <p>Ingresa para continuar al panel de control.</p>
        </div>

        <form class="login-form" @submit.prevent="submitLogin">
          <div class="mb-3">
            <label class="form-label" for="login-identifier">Usuario</label>
            <input id="login-identifier" v-model="identifier" type="text" class="form-control" placeholder="Ingresa tu correo electrónico" autocomplete="username" autofocus required />
          </div>

          <div class="mb-3">
            <div class="password-label-row">
              <label class="form-label" for="login-password">Contraseña</label>
              <button type="button" class="password-toggle" @click="showPassword = !showPassword">
                {{ showPassword ? 'Ocultar' : 'Mostrar' }}
              </button>
            </div>
            <input id="login-password" v-model="password" :type="showPassword ? 'text' : 'password'" class="form-control" placeholder="Escribe tu contraseña" autocomplete="current-password" required />
          </div>

          <div v-if="errorMessage" class="alert alert-danger py-2 mb-3">{{ errorMessage }}</div>

          <button type="submit" class="btn btn-primary w-100" :disabled="loading">
            <span>{{ loading ? 'Validando acceso...' : 'Iniciar sesión' }}</span>
          </button>
        </form>

      </section>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import { useAuthStore } from '../stores/auth';

const identifier = ref('');
const password = ref('');
const showPassword = ref(false);
const errorMessage = ref('');
const loading = ref(false);
const router = useRouter();
const auth = useAuthStore();

async function submitLogin() {
  loading.value = true;
  errorMessage.value = '';

  try {
    const response = await api.post('/auth/login/', {
      identifier: identifier.value.trim(),
      password: password.value,
    });

    auth.setAuth(response.data);
    router.push('/');
  } catch (error) {
    errorMessage.value = 'Credenciales inválidas o servicio no disponible.';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-shell {
  width: 100%;
  margin: 0 auto;
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 28px 18px;
  background: linear-gradient(135deg, #e8f5ef 0%, #f8fafc 55%, #fff3f0 100%);
}

.login-panel {
  width: min(100%, 860px);
  display: grid;
  grid-template-columns: 0.86fr 1.14fr;
  overflow: hidden;
  background: #fff;
  border: 1px solid rgba(0, 127, 95, 0.16);
  box-shadow: 0 24px 60px rgba(0, 67, 49, 0.16);
  border-radius: 18px;
}

.login-aside {
  display: flex;
  min-height: 520px;
  flex-direction: column;
  justify-content: space-between;
  padding: 34px;
  color: #fff;
  background: linear-gradient(150deg, #167A39 0%, #1B2A44 72%, #0A121C 100%);
}

.logo-frame {
  width: 190px;
  height: 190px;
  padding: 14px;
  overflow: hidden;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.16);
}

.brand-logo {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: contain;
  object-position: center;
}

.aside-copy {
  margin-top: auto;
  padding: 76px 0 30px;
}

.aside-kicker,
.form-kicker {
  color: #a7e2cf;
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.aside-copy h1 {
  margin: 10px 0 12px;
  font-size: 2.35rem;
  letter-spacing: 0;
}

.aside-copy p {
  max-width: 260px;
  margin: 0;
  color: #d7f3e9;
  line-height: 1.6;
}

.aside-line {
  width: 48px;
  height: 4px;
  border-radius: 2px;
  object-fit: cover;
  object-position: center;
}

.aside-footer {
  margin-top: 16px;
  color: #b7e4d4;
  font-size: 0.72rem;
}

.login-content {
  padding: 58px 58px 48px;
}

.welcome-copy {
  margin-bottom: 32px;
}

.form-kicker {
  color: #1E9B48;
}

.welcome-copy h2 {
  margin: 10px 0 8px;
  color: #121A2B;
  font-size: 2rem;
  font-weight: 800;
}

.welcome-copy p {
  margin: 0;
  color: #64756f;
}

.btn-primary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-radius: 9px;
  padding: 0.85rem 1rem;
  font-weight: 700;
  background: #1E9B48;
  border: 0;
  box-shadow: 0 8px 16px rgba(0, 127, 95, 0.18);
}

.btn-primary:hover,
.btn-primary:focus {
  background: #167A39;
}

.login-form .form-control {
  padding: 0.82rem 0.9rem;
  border-radius: 9px;
  border: 1px solid #d5e2dc;
}

.password-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.password-toggle {
  margin-bottom: 0.5rem;
  padding: 0;
  border: 0;
  background: transparent;
  color: #1E9B48;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.password-toggle:hover,
.password-toggle:focus-visible {
  color: #1B2A44;
  text-decoration: underline;
}

.login-form .form-control:focus {
  border-color: #008f68;
  box-shadow: 0 0 0 0.2rem rgba(0,143,104,0.13);
}

.demo-box {
  margin-top: 18px;
  background: #f0faf5;
  border: 1px solid #c8e8da;
  border-radius: 9px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  color: #16634c;
}

.demo-box span {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  opacity: 0.8;
}

.demo-box strong {
  font-size: 1rem;
}

.demo-box small {
  opacity: 0.8;
}

@media (max-width: 700px) {
  .login-panel {
    grid-template-columns: 1fr;
  }

  .login-aside {
    min-height: 0;
    padding: 22px;
  }

  .brand-logo {
    width: 100%;
    height: 100%;
  }

  .aside-copy {
    padding: 30px 0 18px;
  }

  .aside-copy h1 { font-size: 1.8rem; }
  .aside-copy p { display: none; }
  .login-content { padding: 34px 22px 28px; }
}
</style>