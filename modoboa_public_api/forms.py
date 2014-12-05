"""
Modoboa API forms.
"""
from django import forms

from versionfield.forms import VersionField


class ClientVersionForm(forms.Form):

    """
    A simple form to validate a client version.
    """

    client_version = VersionField()
    client_site = forms.CharField()
