"""
Modoboa API models.
"""
from django.db import models

from versionfield import VersionField


class ModoboaInstance(models.Model):

    """
    A model to represent a modoboa instance.
    """

    hostname = models.CharField(max_length=255)
    ip_address = models.IPAddressField()
    known_version = VersionField()

    class Meta:
        unique_together = [("hostname", "ip_address")]
