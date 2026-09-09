"""Modoboa API models."""

from dateutil.relativedelta import relativedelta

from django.db import models
from django.utils import timezone


class ModoboaInstanceManager(models.Manager):
    """Custom manager for ModoboaInstance."""

    def active(self):
        """Return active instances (last_request <= 1 month)."""
        return self.get_queryset().filter(
            last_request__gte=timezone.now() - relativedelta(months=1))


class ModoboaInstance(models.Model):
    """A model to represent a modoboa instance."""

    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    known_version = models.CharField(max_length=30, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    last_request = models.DateTimeField(auto_now=True)

    # Statistics
    domain_counter = models.PositiveIntegerField(default=0)
    domain_alias_counter = models.PositiveIntegerField(default=0)
    mailbox_counter = models.PositiveIntegerField(default=0)
    alias_counter = models.PositiveIntegerField(default=0)

    # Used extensions
    extensions = models.ManyToManyField("ModoboaExtension", blank=True)

    objects = ModoboaInstanceManager()

    def __str__(self):
        return "[{0}] {1} -> {2}".format(
            self.ip_address, self.hostname, self.known_version)


class ModoboaExtensionManager(models.Manager):
    """Custom manager for ModoboaExtension."""

    def core(self):
        """Return the row describing Modoboa itself, if any."""
        return self.get_queryset().filter(is_core=True).first()

    def extensions(self):
        """Return actual extensions, ie. everything but Modoboa itself."""
        return self.get_queryset().filter(is_core=False)


class ModoboaExtension(models.Model):
    """A modoboa extension with its latest version.

    Modoboa itself is stored here too (is_core=True) so that announcing a
    new release is a data change instead of a commit and a deployment.
    """

    name = models.CharField(max_length=255, unique=True)
    version = models.CharField(max_length=30)
    deprecated = models.BooleanField(default=False)
    url = models.URLField(blank=True)
    is_core = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)

    objects = ModoboaExtensionManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_core"],
                condition=models.Q(is_core=True),
                name="unique_core_component",
            ),
        ]

    def __str__(self):
        return self.name
