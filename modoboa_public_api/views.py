"""
API views.
"""
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ModoboaInstance, ModoboaExtension
from .forms import ClientVersionForm
from .serializers import ModoboaExtensionSerializer

BAD_HOSTNAME_LIST = [
    "localhost",
    "example.com"
]


class CurrentVersionView(APIView):

    """Get current modoboa version."""

    def get(self, request, fmt=None):
        form = ClientVersionForm(request.GET)
        if not form.is_valid():
            return Response(
                {"error": "Client version and/or site is missing or incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        args = {
            "ip_address": request.META.get("REMOTE_ADDR"),
            "hostname": form.cleaned_data["client_site"]
        }
        if ModoboaInstance.objects.filter(**args).count():
            mdinst = ModoboaInstance.objects.get(**args)
        elif ModoboaInstance.objects.filter(hostname=args["hostname"]).count():
            mdinst = ModoboaInstance.objects.get(hostname=args["hostname"])
            mdinst.ip_address = args["ip_address"]
        elif ModoboaInstance.objects.filter(ip_address=args["ip_address"]).count():
            mdinst = ModoboaInstance.objects.get(ip_address=args["ip_address"])
            if args["hostname"] not in BAD_HOSTNAME_LIST:
                mdinst.hostname = args["hostname"]
        elif args["hostname"] not in BAD_HOSTNAME_LIST:
            mdinst = ModoboaInstance(**args)
        else:
            mdinst = None
        if mdinst is not None:
            if mdinst.known_version != form.cleaned_data["client_version"]:
                mdinst.known_version = form.cleaned_data["client_version"]
            mdinst.save()
        data = {"version": settings.MODOBOA_CURRENT_VERSION[0],
                "changelog_url": settings.MODOBOA_CURRENT_VERSION[1]}
        return Response(data)


class ExtensionListView(APIView):

    """List all defined extensions."""

    def get(self, request, fmt=None):
        extensions = ModoboaExtension.objects.all()
        serializer = ModoboaExtensionSerializer(extensions, many=True)
        return Response(serializer.data)
