"""
Autenticación personalizada para APIs REST que no requiere CSRF.
Útil para endpoints públicos como login.
"""
from rest_framework.authentication import SessionAuthentication


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    Autenticación de sesión que no requiere CSRF token.
    Útil para endpoints públicos como login donde el frontend
    aún no tiene el token CSRF.
    """
    def enforce_csrf(self, request):
        # No aplicar verificación CSRF
        return

