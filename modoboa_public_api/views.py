"""
API views.
"""
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ModoboaInstance
from .forms import ClientVersionForm


class CurrentVersionView(APIView):

    """Get current modoboa version."""

    def get(self, request, fmt=None):
        form = ClientVersionForm(request.GET)
        if not form.is_valid():
            return Response(
                {"error": "Client version is missing or incorrect"},
                status=status.HTTP_400_BAD_REQUEST
            )
        remote_host = request.META.get("REMOTE_HOST")
        remote_addr = request.META.get("REMOTE_ADDR")
        args = {"ip_address": remote_addr}
        if remote_host:
            args["remote_host"] = remote_host
        try:
            mdinst = ModoboaInstance.objects.get(**args)
        except ModoboaInstance.DoesNotExist:
            mdinst = ModoboaInstance.objects.create(
                known_version=form.cleaned_data["client_version"],
                **args
            )
        else:
            if mdinst.known_version != form.cleaned_data["client_version"]:
                mdinst.known_version = form.cleaned_data["client_version"]
                mdinst.save()
        data = {"version": settings.MODOBOA_CURRENT_VERSION[0],
                "changelog_url": settings.MODOBOA_CURRENT_VERSION[1]}
        return Response(data)

