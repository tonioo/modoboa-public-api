"""API factories."""

import factory

from . import models


class ModoboaExtensionFactory(factory.DjangoModelFactory):
    """Factory for ModoboaExtension."""

    class Meta:
        model = models.ModoboaExtension

    version = "1.0.0"


class ModoboaInstanceFactory(factory.DjangoModelFactory):
    """Factory for ModoboaInstance."""

    class Meta:
        model = models.ModoboaInstance

    ip_address = "1.2.3.4"
    known_version = "1.0.0"
