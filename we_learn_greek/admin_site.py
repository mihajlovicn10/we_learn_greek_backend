import math

from django.contrib.admin import AdminSite
from django.contrib.admin.apps import AdminConfig
from django.http import HttpResponse

from .throttling import AdminLoginThrottle


class ThrottledAdminSite(AdminSite):
    """Default admin site with rate-limited login attempts."""

    def login(self, request, extra_context=None):
        if request.method == 'POST':
            throttle = AdminLoginThrottle()
            if not throttle.allow_request(request, None):
                response = HttpResponse(
                    'Too many login attempts. Try again later.',
                    status=429,
                    content_type='text/plain',
                )
                wait = throttle.wait()
                if wait is not None:
                    response['Retry-After'] = str(math.ceil(wait))
                return response
        return super().login(request, extra_context)


class ThrottledAdminConfig(AdminConfig):
    default_site = 'we_learn_greek.admin_site.ThrottledAdminSite'
