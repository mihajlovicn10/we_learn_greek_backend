from rest_framework.throttling import SimpleRateThrottle


class AdminLoginThrottle(SimpleRateThrottle):
    """Per-IP limit on Django admin login POSTs (the admin is not a DRF view)."""

    scope = 'admin_login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
