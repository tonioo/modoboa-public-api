"""Modoboa API forms."""
from django import forms


class ClientVersionForm(forms.Form):
    """A simple form to validate a client version."""

    # Same limits as ModoboaInstance, or the database rejects the save.
    client_version = forms.CharField(max_length=30)
    client_site = forms.CharField(max_length=255)
