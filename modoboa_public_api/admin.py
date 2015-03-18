from django.contrib import admin

from .models import ModoboaInstance, ModoboaExtension


class ModoboaInstanceAdmin(admin.ModelAdmin):

    """
    Admin class for ModoboaInstance model.
    """

    list_display = (
        "ip_address", "hostname", "known_version", "last_request"
    )


class ModoboaExtensionAdmin(admin.ModelAdmin):

    """Admin class for ModoboaExtension model."""

    list_display = ("name", "version")


admin.site.register(ModoboaInstance, ModoboaInstanceAdmin)
admin.site.register(ModoboaExtension, ModoboaExtensionAdmin)
