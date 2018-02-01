"""Modoboa API forms."""
from django import forms


class ClientVersionForm(forms.Form):
    """A simple form to validate a client version."""

    client_version = forms.CharField()
    client_site = forms.CharField()
