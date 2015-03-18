"""
Modoboa API models.
"""
from django.db import models
from django.utils import timezone

from versionfield import VersionField


class ModoboaInstance(models.Model):

    """
    A model to represent a modoboa instance.
    """

    hostname = models.CharField(max_length=255)
    ip_address = models.IPAddressField()
    known_version = VersionField()
    last_request = models.DateTimeField(default=timezone.now, auto_now=True)

    class Meta:
        unique_together = [("hostname", "ip_address")]

    def __str__(self):
        return "[{0}] {1} -> {2}".format(
            self.ip_address, self.hostname, self.known_version)


class ModoboaExtension(models.Model):

    """A modoboa extension with its latest version."""

    name = models.CharField(max_length=255, unique=True)
    version = VersionField()

    def __str__(self):
        return "{0}: {1}".format(self.name, self.version)
