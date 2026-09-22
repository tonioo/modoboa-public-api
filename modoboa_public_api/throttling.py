"""Rate limits for the endpoints that write to the database.

There is no authentication, so writes are limited per client IP address.
Legitimate clients write about once a day (Modoboa runs its public API
command from cron), the limits only stop floods. They can be changed from
the host project, with the scopes below as keys:

    REST_FRAMEWORK = {"DEFAULT_THROTTLE_RATES": {"instance_create": "5/hour"}}

Hits are counted in Django's default cache, Redis in production: it must be
shared between the server processes, a per-process LocMemCache multiplies
the limits by the number of processes.
"""

import logging

from rest_framework.settings import api_settings
from rest_framework.throttling import SimpleRateThrottle

logger = logging.getLogger(__name__)


class WriteRateThrottle(SimpleRateThrottle):
    """Throttle per REMOTE_ADDR, with a default rate."""

    default_rate = None

    def allow_request(self, request, view):
        # Fail open: an unreachable cache must not turn every instance
        # write into a 500, the limits are only a safety net.
        try:
            return super().allow_request(request, view)
        except Exception:
            logger.warning(
                "Rate limiting disabled, cache unavailable", exc_info=True)
            return True

    def get_rate(self):
        # Read the settings at call time, the class attribute DRF uses is
        # frozen at import.
        return api_settings.DEFAULT_THROTTLE_RATES.get(
            self.scope, self.default_rate)

    def get_ident(self, request):
        # DRF trusts X-Forwarded-For when NUM_PROXIES is unset, which would
        # let any client pick its own identity. nginx talks to the app
        # directly, so REMOTE_ADDR is the client, as everywhere else here.
        return request.META.get("REMOTE_ADDR")

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope, "ident": self.get_ident(request)}


class InstanceCreateThrottle(WriteRateThrottle):
    """POST /instances/: an instance registers once."""

    scope = "instance_create"
    default_rate = "10/hour"


class InstanceUpdateThrottle(WriteRateThrottle):
    """PUT/PATCH /instances/<pk>/, also slows down pk enumeration."""

    scope = "instance_update"
    default_rate = "30/hour"


class CurrentVersionThrottle(WriteRateThrottle):
    """Writes done by the legacy /current_version/ endpoint."""

    scope = "current_version"
    default_rate = "30/hour"
