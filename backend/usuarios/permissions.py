from rest_framework.permissions import BasePermission


class RolePermission(BasePermission):
    message = 'No tienes permisos para realizar esta acción.'

    def has_module_permission(self, request):
        path = request.path.strip('/').split('/')
        section = path[1] if path and path[0] == 'api' and len(path) > 1 else 'dashboard'
        section = {
            'device': 'dispositivos',
            'dispositivos': 'dispositivos',
            'bateria': 'dispositivos',
            'ram': 'dispositivos',
            'almacenamiento': 'dispositivos',
            'redes': 'sims',
            'sims': 'sims',
            'consumos': 'sims',
            'usuarios': 'usuarios',
            'roles': 'usuarios',
        }.get(section, section)
        permisos = getattr(request.user, 'permisos', None)
        return not isinstance(permisos, dict) or permisos.get(section, True)

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False):
            return True
        if not self.has_module_permission(request):
            return False

        role = getattr(getattr(user, 'rol', None), 'nombre', '').upper()
        if role == 'ADMIN':
            return True
        if role == 'SUPERVISOR':
            return request.method in {'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT', 'PATCH'}
        if role == 'TRABAJADOR':
            return request.method in {'GET', 'HEAD', 'OPTIONS'}
        return False