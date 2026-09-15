"""API views."""
from django.conf import settings

from rest_framework import decorators, mixins, response, status, viewsets
from rest_framework.views import APIView

from .models import ModoboaInstance
from .forms import ClientVersionForm

from . import constants
from . import models
from . import serializers


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
        if request.GET.get("client_version") == "1.2.0-rc2":
            # Temp. fix
            request.GET = request.GET.copy()
            request.GET["client_version"] = "1.2.0"
        form = ClientVersionForm(request.GET)
        if not form.is_valid():
            return response.Response(
                {"error": (
                    "Client version and/or site is missing or incorrect")},
                status=status.HTTP_400_BAD_REQUEST
            )
        args = {
            "ip_address": request.META.get("REMOTE_ADDR"),
            "hostname": form.cleaned_data["client_site"]
        }
        # Several rows can share a hostname (the new API registers a new row
        # when an instance changes IP) or an IP address (NAT), so pick the
        # most recently seen one instead of expecting a single match.
        instances = ModoboaInstance.objects.order_by("-last_request")
        mdinst = instances.filter(**args).first()
        if mdinst is None:
            mdinst = instances.filter(hostname=args["hostname"]).first()
            if mdinst is not None:
                mdinst.ip_address = args["ip_address"]
        if mdinst is None:
            mdinst = instances.filter(ip_address=args["ip_address"]).first()
            if (mdinst is not None and
                    args["hostname"] not in constants.BAD_HOSTNAME_LIST):
                mdinst.hostname = args["hostname"]
        if (mdinst is None and
                args["hostname"] not in constants.BAD_HOSTNAME_LIST):
            mdinst = ModoboaInstance(**args)
        if mdinst is not None:
            if mdinst.known_version != form.cleaned_data["client_version"]:
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

    @decorators.action(methods=["get"], detail=False)
    def search(self, request, *args, **kwargs):
        """Search an instance."""
        hostname = request.GET.get("hostname")
        if not hostname:
            return response.Response({
                "error": "No hostname provided."
            }, status=status.HTTP_400_BAD_REQUEST)
        ip_address = request.META.get("REMOTE_ADDR")
        instance = models.ModoboaInstance.objects.filter(
            ip_address=ip_address, hostname=hostname).first()
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
