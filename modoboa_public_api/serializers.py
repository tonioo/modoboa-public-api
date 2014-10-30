from rest_framework import serializers


class VersionSerializer(serializers.Serializer):

    """
    The current version.
    """

    version = serializers.CharField(max_length=10)
