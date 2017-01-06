"""Custom serializers."""

from rest_framework import serializers

from . import constants
from . import models


class VersionSerializer(serializers.Serializer):
    """A serializer to represent a version."""

    name = serializers.CharField()
    version = serializers.CharField()
    url = serializers.URLField()


class BaseExtensionSerializer(serializers.ModelSerializer):
    """A simple serializer for ModoboaExtension."""

    class Meta:
        model = models.ModoboaExtension
        fields = ("name", )


class ModoboaExtensionSerializer(BaseExtensionSerializer):
    """A serializer for the ModoboaExtension model."""

    version = serializers.CharField(max_length=10)

    class Meta(BaseExtensionSerializer.Meta):
        fields = BaseExtensionSerializer.Meta.fields + ("version", )


class ExtensionListField(serializers.ListField):
    """Custom list field."""

    child = serializers.CharField()

    def to_representation(self, value):
        """Override representation."""
        return [extension.name for extension in value.all()]


class InstanceSerializer(serializers.ModelSerializer):
    """A serializer for Instance."""

    extensions = ExtensionListField(required=False)

    class Meta:
        model = models.ModoboaInstance
        fields = (
            "pk", "hostname", "known_version",
            "domain_counter", "domain_alias_counter",
            "mailbox_counter", "alias_counter",
            "extensions")

    def validate_hostname(self, value):
        """Check if hostname is allowed."""
        if value in constants.BAD_HOSTNAME_LIST:
            raise serializers.ValidationError("Invalid hostname.")
        return value

    def set_instance_extensions(self, instance, extensions):
        """Fetch and set extensions."""
        extensions = [extension.replace("_", "-") for extension in extensions]
        extensions = models.ModoboaExtension.objects.filter(
            name__in=list(set(extensions)))
        instance.extensions = list(extensions)

    def create(self, validated_data):
        """Fetch IP address from request."""
        extensions = validated_data.pop("extensions", None)
        ip_address = self.context["request"].META.get("REMOTE_ADDR")
        qset = models.ModoboaInstance.objects.filter(
            ip_address=ip_address, hostname=validated_data["hostname"])
        if qset.exists():
            raise serializers.ValidationError("Instance already registered")
        instance = models.ModoboaInstance.objects.create(
            ip_address=ip_address, **validated_data)
        if extensions:
            self.set_instance_extensions(instance, extensions)
        return instance

    def update(self, instance, validated_data):
        """Fetch IP address from request."""
        instance.ip_address = self.context["request"].META.get("REMOTE_ADDR")
        extensions = validated_data.pop("extensions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if extensions:
            self.set_instance_extensions(instance, extensions)
        return instance
