"""Custom serializers."""

from rest_framework import serializers

from .models import ModoboaExtension


class VersionSerializer(serializers.Serializer):

    """
    The current version.
    """

    version = serializers.CharField(max_length=10)


class ModoboaExtensionSerializer(serializers.ModelSerializer):

    """A serializer for the ModoboaExtension model."""

    version = serializers.CharField(max_length=10)

    class Meta:
        model = ModoboaExtension
        fields = ("name", "version")
