"""API test cases."""

from django.core.urlresolvers import reverse
from django.test import TestCase

from rest_framework.test import APIClient

from . import factories
from . import models


class InstanceViewSetTestCase(TestCase):
    """TestCase for InstanceViewSet."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
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
            "domain_counter": 10, "extensions": ["modoboa-amavis"]
        }
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 404)
        url = reverse("instance-detail", args=[self.md_instance.pk])
        response = self.client.put(url, data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.md_instance.refresh_from_db()
        self.assertEqual(self.md_instance.domain_counter, 10)
        self.assertTrue(
            self.md_instance.extensions.filter(
                name="modoboa-amavis").exists())

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


# Deprecated viewsets

class ExtensionViewSetTestCase(TestCase):
    """TestCase for ExtensionViewSet."""

    @classmethod
    def setUpTestData(cls):
        """Create some data."""
        factories.ModoboaExtensionFactory(name="modoboa-amavis")
        factories.ModoboaExtensionFactory(name="modoboa-stats")
        factories.ModoboaExtensionFactory(name="modoboa-webmail")

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
