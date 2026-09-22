"""API views."""
from django.conf import settings
from django.db.models import Q

from rest_framework import decorators, mixins, response, status, viewsets
from rest_framework.views import APIView

from .models import ModoboaInstance
from .forms import ClientVersionForm

from . import models
from . import serializers
from . import utils


def get_core_version():
    """Return (version, changelog url) for Modoboa itself.

    The value lives in database so a new release can be announced without a
    deployment. settings.MODOBOA_CURRENT_VERSION is kept as a fallback:
    /current_version/ is polled by every Modoboa instance out there and must
    not break because the row was removed.
    """
    core = models.ModoboaExtension.objects.core()
    if core is not None:
        return core.version, core.url
    return settings.MODOBOA_CURRENT_VERSION


# Legacy API, to deprecate

class CurrentVersionView(APIView):

    """Get current modoboa version."""

    def get(self, request, fmt=None):
        form = ClientVersionForm(request.GET)
        if not form.is_valid():
            return response.Response(
                {"error": (
                    "Client version and/or site is missing or incorrect")},
                status=status.HTTP_400_BAD_REQUEST
            )
        # Unusable hostnames still get an answer, they are just not recorded.
        hostname = utils.normalize_hostname(form.cleaned_data["client_site"])
        if hostname is not None:
            # Only a row matching both IP address and hostname is updated:
            # matching one of them would let anyone claiming a hostname, or
            # sharing an IP address, take over another instance's row. An
            # instance that changed IP gets a new row, like with the new API.
            # Several rows can match (concurrent registrations), so pick the
            # most recently seen one.
            ip_address = request.META.get("REMOTE_ADDR")
            mdinst = ModoboaInstance.objects.filter(
                ip_address=ip_address, hostname__iexact=hostname
            ).order_by("-last_request").first()
            if mdinst is None:
                mdinst = ModoboaInstance(
                    ip_address=ip_address, hostname=hostname)
            mdinst.known_version = form.cleaned_data["client_version"]
            mdinst.save()
        version, changelog_url = get_core_version()
        data = {"version": version, "changelog_url": changelog_url}
        return response.Response(data)


class ExtensionListViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """List all defined extensions."""

    queryset = models.ModoboaExtension.objects.extensions()
    serializer_class = serializers.ModoboaExtensionSerializer


# New API

class InstanceViewSet(mixins.CreateModelMixin, mixins.UpdateModelMixin,
                      viewsets.GenericViewSet):
    """Create or update instance."""

    queryset = ModoboaInstance.objects.all()
    serializer_class = serializers.InstanceSerializer

    def get_queryset(self):
        """Only let a client update an instance it can claim.

        There is no authentication and pks are sequential, so a client must
        match either the IP address or the hostname of the row. Requiring
        both would lock out instances that change IP (or hostname): Modoboa
        stores the pk once and never searches it again. Other rows answer
        404, like missing ones.
        """
        queryset = super().get_queryset()
        if self.action in ("update", "partial_update"):
            condition = Q(ip_address=self.request.META.get("REMOTE_ADDR"))
            hostname = self.request.data.get("hostname")
            if isinstance(hostname, str):
                hostname = utils.normalize_hostname(hostname)
                if hostname is not None:
                    condition |= Q(hostname__iexact=hostname)
            queryset = queryset.filter(condition)
        return queryset

    @decorators.action(methods=["get"], detail=False)
    def search(self, request, *args, **kwargs):
        """Search an instance."""
        hostname = request.GET.get("hostname")
        if not hostname:
            return response.Response({
                "error": "No hostname provided."
            }, status=status.HTTP_400_BAD_REQUEST)
        ip_address = request.META.get("REMOTE_ADDR")
        # An unusable hostname cannot be registered, so it is never found.
        hostname = utils.normalize_hostname(hostname)
        instance = hostname and models.ModoboaInstance.objects.filter(
            ip_address=ip_address, hostname__iexact=hostname
        ).order_by("-last_request").first()
        if not instance:
            return response.Response({
                "error": "Instance not found."
            }, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)


class VersionViewSet(viewsets.ViewSet):
    """List all versions."""

    def list(self, request):
        # is_core first in the ordering keeps Modoboa last, as before.
        components = list(
            models.ModoboaExtension.objects.order_by("is_core", "name"))
        data = [
            {"name": component.name, "version": component.version,
             "url": component.url}
            for component in components
        ]
        if not any(component.is_core for component in components):
            version, url = settings.MODOBOA_CURRENT_VERSION
            data.append({"name": "modoboa", "version": version, "url": url})
        serializer = serializers.VersionSerializer(data, many=True)
        return response.Response(serializer.data)
