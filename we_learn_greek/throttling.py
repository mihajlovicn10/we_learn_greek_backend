from rest_framework.throttling import SimpleRateThrottle, UserRateThrottle


class ContentBurstThrottle(UserRateThrottle):
    """Per user (or per IP when anonymous) short-window limit on word-content endpoints."""

    scope = 'content_burst'


class ContentSustainedThrottle(UserRateThrottle):
    """Per user (or per IP when anonymous) daily limit on word-content endpoints."""

    scope = 'content_sustained'


CONTENT_THROTTLES = [ContentBurstThrottle, ContentSustainedThrottle]


class AdminLoginThrottle(SimpleRateThrottle):
    """Per-IP limit on Django admin login POSTs (the admin is not a DRF view)."""

    scope = 'admin_login'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}
