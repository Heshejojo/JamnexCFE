import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '../stores/auth';

const routes = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('../views/DashboardView.vue'),
    meta: { requiresAuth: true, permiso: 'dashboard' },
  },
  {
    path: '/dispositivos',
    name: 'dispositivos',
    component: () => import('../views/DispositivosView.vue'),
    meta: { requiresAuth: true, permiso: 'dispositivos' },
  },
  {
    path: '/sims',
    name: 'sims',
    component: () => import('../views/SimsView.vue'),
    meta: { requiresAuth: true, permiso: 'sims' },
  },
  {
    path: '/usuarios',
    name: 'usuarios',
    component: () => import('../views/UsuariosView.vue'),
    meta: { requiresAuth: true, permiso: 'usuarios' },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.requiresAuth && !auth.token) return '/login';
  if (to.meta.requiresAuth && auth.token && !auth.user) await auth.fetchCurrentUser();
  if (to.meta.requiresAuth && !auth.token) return '/login';

  const permission = to.meta.permiso;
  if (!permission || !auth.user) return true;
  if (auth.user.is_superuser || auth.user.permisos?.[permission] === true) return true;

  const allowedRoutes = [
    { permiso: 'dashboard', path: '/' },
    { permiso: 'dispositivos', path: '/dispositivos' },
    { permiso: 'sims', path: '/sims' },
    { permiso: 'usuarios', path: '/usuarios' },
  ];
  const fallback = allowedRoutes.find(({ permiso }) => auth.user.permisos?.[permiso] === true);
  return fallback?.path || '/login';
});

export default router;
