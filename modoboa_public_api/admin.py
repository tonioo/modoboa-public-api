from django.contrib import admin

from .models import ModoboaInstance, ModoboaExtension


class ModoboaInstanceAdmin(admin.ModelAdmin):
    """Admin class for ModoboaInstance model."""

    list_display = (
        "hostname", "known_version",
        "domain_counter", "domain_alias_counter",
        "mailbox_counter", "alias_counter",
        "created", "last_request",
    )
    list_filter = ("known_version", )
    search_fields = ["ip_address", "hostname"]


class ModoboaExtensionAdmin(admin.ModelAdmin):

    """Admin class for ModoboaExtension model."""

    list_display = ("name", "version")


admin.site.register(ModoboaInstance, ModoboaInstanceAdmin)
admin.site.register(ModoboaExtension, ModoboaExtensionAdmin)
