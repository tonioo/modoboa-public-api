"""Modoboa API models."""

from django.db import models

from versionfield import VersionField


class ModoboaInstance(models.Model):
    """A model to represent a modoboa instance."""

    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    known_version = VersionField()
    created = models.DateTimeField(auto_now_add=True)
    last_request = models.DateTimeField(auto_now=True)

    # Statistics
    domain_counter = models.PositiveIntegerField(default=0)
    mailbox_counter = models.PositiveIntegerField(default=0)
    alias_counter = models.PositiveIntegerField(default=0)

    # Used extensions
    extensions = models.ManyToManyField("ModoboaExtension", blank=True)

    class Meta:
        unique_together = [("hostname", "ip_address")]

    def __str__(self):
        return "[{0}] {1} -> {2}".format(
            self.ip_address, self.hostname, self.known_version)


class ModoboaExtension(models.Model):
    """A modoboa extension with its latest version."""

    name = models.CharField(max_length=255, unique=True)
    version = VersionField()
