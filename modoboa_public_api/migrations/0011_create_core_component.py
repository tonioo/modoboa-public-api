from django.conf import settings
from django.db import migrations


def create_core_component(apps, schema_editor):
    """Turn settings.MODOBOA_CURRENT_VERSION into a database row."""
    ModoboaExtension = apps.get_model("modoboa_public_api", "ModoboaExtension")
    if ModoboaExtension.objects.filter(is_core=True).exists():
        return
    version, url = settings.MODOBOA_CURRENT_VERSION
    ModoboaExtension.objects.update_or_create(
        name="modoboa",
        defaults={"version": version, "url": url, "is_core": True},
    )


def remove_core_component(apps, schema_editor):
    ModoboaExtension = apps.get_model("modoboa_public_api", "ModoboaExtension")
    ModoboaExtension.objects.filter(is_core=True).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('modoboa_public_api', '0010_modoboaextension_is_core_modoboaextension_updated_and_more'),
    ]

    operations = [
        migrations.RunPython(create_core_component, remove_core_component),
    ]
