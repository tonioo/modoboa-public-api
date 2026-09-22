"""API test cases."""

import datetime

from django.conf import settings
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from . import factories
from . import models


class CoreComponentTestCase(TestCase):
    """Modoboa itself is stored as a ModoboaExtension row."""

    def test_seeded_from_settings(self):
        """Migration 0011 created the row from the setting."""
        core = models.ModoboaExtension.objects.core()
        self.assertEqual(core.name, "modoboa")
        self.assertEqual(core.version, settings.MODOBOA_CURRENT_VERSION[0])
        self.assertEqual(core.url, settings.MODOBOA_CURRENT_VERSION[1])

    def test_only_one_core_row(self):
        """A second core row is rejected by the database."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            models.ModoboaExtension.objects.create(
                name="other", version="1.0.0", is_core=True)

    def test_core_row_is_not_an_extension(self):
        """The core row is excluded from the extension queryset."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
        self.assertEqual(models.ModoboaExtension.objects.count(), 2)
        extensions = models.ModoboaExtension.objects.extensions()
        self.assertEqual(
            [extension.name for extension in extensions], ["modoboa-amavis"])


class InstanceViewSetTestCase(TestCase):
    """TestCase for InstanceViewSet."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
        factories.ModoboaExtensionFactory(name="modoboa-stats")
        cls.md_instance = factories.ModoboaInstanceFactory(
            hostname="mail.pouet.fr", ip_address="127.0.0.1")

    def setUp(self):
        """Replace client."""
        super(InstanceViewSetTestCase, self).setUp()
        self.client = APIClient()

    def test_create(self):
        """Test creation of instance."""
        url = reverse("instance-list")
        # Minimal set
        data = {
            "hostname": "mail.example.tld",
            "known_version": "1.0.0"
        }
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)

        # Full set
        data.update({
            "hostname": "mail.example2.tld",
            "domain_counter": 10, "mailbox_counter": 10,
            "alias_counter": 10, "domain_alias_counter": 10,
            "extensions": ["modoboa-amavis"],
        })
        response = self.client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, 201)
        instance = response.json()
        instance = models.ModoboaInstance.objects.get(pk=instance["pk"])
        self.assertTrue(
            instance.extensions.filter(name="modoboa-amavis").exists())

    def test_update(self):
        """Test instance update."""
        url = reverse("instance-detail", args=[9999])
        data = {
            "hostname": "mail.pouet.fr", "known_version": "1.2.3",
            "domain_counter": 10, "extensions": [
                "modoboa-amavis", "modoboa_stats"]
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)
        url = reverse("instance-detail", args=[self.md_instance.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.md_instance.refresh_from_db()
        self.assertEqual(self.md_instance.domain_counter, 10)
        self.assertEqual(self.md_instance.extensions.count(), 2)
        self.assertTrue(
            self.md_instance.extensions.filter(
                name="modoboa-amavis").exists())
        self.assertTrue(
            self.md_instance.extensions.filter(
                name="modoboa-stats").exists())
        data["extensions"] = ["modoboa-amavis"]
        url = reverse("instance-detail", args=[self.md_instance.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.md_instance.refresh_from_db()
        self.assertEqual(self.md_instance.extensions.count(), 1)

    def test_update_other_instance(self):
        """A client cannot update a row it matches neither by IP nor hostname."""
        other = factories.ModoboaInstanceFactory(hostname="mail.other.fr")
        url = reverse("instance-detail", args=[other.pk])
        data = {
            "hostname": "mail.pouet.fr", "known_version": "6.6.6",
            "domain_counter": 1000000
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)
        response = self.client.patch(
            url, data={"domain_counter": 1000000}, format="json")
        self.assertEqual(response.status_code, 404)
        other.refresh_from_db()
        self.assertEqual(other.hostname, "mail.other.fr")
        self.assertEqual(other.ip_address, "1.2.3.4")
        self.assertEqual(other.known_version, "1.0.0")
        self.assertEqual(other.domain_counter, 0)

    def test_update_after_ip_change(self):
        """An instance whose IP changed can still update its row."""
        moved = factories.ModoboaInstanceFactory(hostname="mail.moved.fr")
        url = reverse("instance-detail", args=[moved.pk])
        data = {"hostname": "mail.moved.fr", "known_version": "1.1.0"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        moved.refresh_from_db()
        self.assertEqual(moved.ip_address, "127.0.0.1")
        self.assertEqual(moved.known_version, "1.1.0")

    def test_update_after_hostname_change(self):
        """An instance whose hostname changed can still update its row."""
        url = reverse("instance-detail", args=[self.md_instance.pk])
        data = {"hostname": "mail.renamed.fr", "known_version": "1.1.0"}
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.md_instance.refresh_from_db()
        self.assertEqual(self.md_instance.hostname, "mail.renamed.fr")

    def test_update_clear_extensions(self):
        """An empty extension list removes all extensions."""
        self.md_instance.extensions.set(
            models.ModoboaExtension.objects.extensions())
        url = reverse("instance-detail", args=[self.md_instance.pk])
        data = {
            "hostname": "mail.pouet.fr", "known_version": "1.0.0",
            "extensions": []
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.md_instance.extensions.count(), 0)

        # Omitting the field leaves extensions untouched.
        self.md_instance.extensions.set(
            models.ModoboaExtension.objects.extensions())
        del data["extensions"]
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.md_instance.extensions.count(), 2)

    def test_update_dev_version(self):
        """Test update with a dev version."""
        data = {
            "hostname": "mail.pouet.fr",
            "known_version": "1.10.2.dev5+ga327ccf0",
            "domain_counter": 10, "extensions": [
                "modoboa-amavis", "modoboa_stats"]
        }
        url = reverse("instance-detail", args=[self.md_instance.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.md_instance.refresh_from_db()
        self.assertEqual(
            self.md_instance.known_version, data["known_version"])

    def test_search(self):
        """Test instance search."""
        url = "{}?hostname={}".format(
            reverse("instance-search"), "mail.pouet.fr")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        instance = response.json()
        self.assertEqual(instance["pk"], self.md_instance.pk)

        url = "{}?hostname={}".format(
            reverse("instance-search"), "mail.pouet.com")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(reverse("instance-search"))
        self.assertEqual(response.status_code, 400)


    def test_search_duplicates(self):
        """The most recently seen row wins when several match."""
        recent = factories.ModoboaInstanceFactory(
            hostname="mail.pouet.fr", ip_address="127.0.0.1")
        models.ModoboaInstance.objects.filter(pk=self.md_instance.pk).update(
            last_request=recent.last_request - datetime.timedelta(days=1))
        url = "{}?hostname={}".format(
            reverse("instance-search"), "mail.pouet.fr")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["pk"], recent.pk)


class VersionViewSetTestCase(TestCase):
    """TestCase for VersionViewSet."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
        factories.ModoboaExtensionFactory(name="modoboa-stats")
        factories.ModoboaExtensionFactory(name="modoboa-webmail")

    def setUp(self):
        """Replace client."""
        super(VersionViewSetTestCase, self).setUp()
        self.client = APIClient()

    def test_list(self):
        """Test list."""
        url = reverse("version-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        versions = response.json()
        self.assertEqual(len(versions), 4)

    def test_list_uses_core_row(self):
        """Modoboa version and url come from database."""
        core = models.ModoboaExtension.objects.core()
        core.version = "9.9.9"
        core.url = "https://example.test/releases/9.9.9"
        core.save()
        response = self.client.get(reverse("version-list"))
        self.assertEqual(response.status_code, 200)
        versions = response.json()
        # Modoboa is still served last.
        self.assertEqual(versions[-1], {
            "name": "modoboa", "version": "9.9.9",
            "url": "https://example.test/releases/9.9.9"})

    def test_list_without_core_row(self):
        """Modoboa is still announced when the row is missing."""
        models.ModoboaExtension.objects.filter(is_core=True).delete()
        response = self.client.get(reverse("version-list"))
        self.assertEqual(response.status_code, 200)
        versions = response.json()
        self.assertEqual(len(versions), 4)
        self.assertEqual(
            versions[-1]["version"], settings.MODOBOA_CURRENT_VERSION[0])


# Deprecated viewsets

class ExtensionViewSetTestCase(TestCase):
    """TestCase for ExtensionViewSet."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
        factories.ModoboaExtensionFactory(name="modoboa-stats")
        factories.ModoboaExtensionFactory(name="modoboa-webmail")
        cls.core = models.ModoboaExtension.objects.core()

    def setUp(self):
        """Replace client."""
        super(ExtensionViewSetTestCase, self).setUp()
        self.client = APIClient()

    def test_list(self):
        """Test list."""
        url = reverse("extension-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        versions = response.json()
        self.assertEqual(len(versions), 3)
        # Modoboa itself is not an extension.
        self.assertNotIn(
            self.core.name, [version["name"] for version in versions])


class CurrentVersionAPI(TestCase):
    """Current version test cases."""

    def setUp(self):
        """Replace client."""
        super(CurrentVersionAPI, self).setUp()
        self.client = APIClient()

    def test_current_version(self):
        """Check API call."""
        url = reverse("current_version")
        url = "{}?client_version={}&client_site={}".format(
            url, "1.0.0", "mail.pouet.com")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertIn("version", content)
        self.assertIn("changelog_url", content)
        self.assertTrue(
            models.ModoboaInstance.objects.filter(
                hostname="mail.pouet.com", known_version="1.0.0")
            .exists())

    def test_current_version_from_database(self):
        """Version is read from the core row."""
        models.ModoboaExtension.objects.filter(is_core=True).update(
            version="9.9.9", url="https://example.test/releases/9.9.9")
        url = reverse("current_version")
        url = "{}?client_version={}&client_site={}".format(
            url, "1.0.0", "mail.pouet.com")
        content = self.client.get(url).json()
        self.assertEqual(content["version"], "9.9.9")
        self.assertEqual(
            content["changelog_url"], "https://example.test/releases/9.9.9")

    def test_current_version_fallback(self):
        """Endpoint still answers when the core row is missing."""
        models.ModoboaExtension.objects.filter(is_core=True).delete()
        url = reverse("current_version")
        url = "{}?client_version={}&client_site={}".format(
            url, "1.0.0", "mail.pouet.com")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.json()
        self.assertEqual(
            content["version"], settings.MODOBOA_CURRENT_VERSION[0])
        self.assertEqual(
            content["changelog_url"], settings.MODOBOA_CURRENT_VERSION[1])

    def test_duplicated_instances(self):
        """Rows sharing a hostname or an IP address do not crash the API."""
        url = reverse("current_version")
        old, recent = factories.ModoboaInstanceFactory.create_batch(
            2, hostname="mail.pouet.com")
        models.ModoboaInstance.objects.filter(pk=old.pk).update(
            last_request=recent.last_request - datetime.timedelta(days=1))
        response = self.client.get("{}?client_version={}&client_site={}".format(
            url, "1.1.0", "mail.pouet.com"))
        self.assertEqual(response.status_code, 200)
        recent.refresh_from_db()
        self.assertEqual(recent.known_version, "1.1.0")
        self.assertEqual(recent.ip_address, "127.0.0.1")

        factories.ModoboaInstanceFactory.create_batch(
            2, hostname="mail.other.com", ip_address="127.0.0.1")
        response = self.client.get("{}?client_version={}&client_site={}".format(
            url, "1.1.0", "localhost"))
        self.assertEqual(response.status_code, 200)

    def test_too_long_values(self):
        """Values the database cannot store are rejected, not a crash."""
        url = reverse("current_version")
        response = self.client.get("{}?client_version={}&client_site={}".format(
            url, "1" * 31, "mail.pouet.com"))
        self.assertEqual(response.status_code, 400)
        response = self.client.get("{}?client_version={}&client_site={}".format(
            url, "1.0.0", "a" * 256))
        self.assertEqual(response.status_code, 400)
        self.assertFalse(models.ModoboaInstance.objects.exists())

    def test_bad_version(self):
        """Check that API does not crash."""
        url = reverse("current_version")
        url = "{}?client_version={}&client_site={}".format(
            url, "1.2.0-rc2", "mail.pouet.com")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            models.ModoboaInstance.objects.filter(
                hostname="mail.pouet.com", known_version="1.2.0")
            .exists())
