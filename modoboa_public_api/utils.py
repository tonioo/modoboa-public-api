"""API utilities."""

import re

from . import constants

HOSTNAME_LABEL_RE = re.compile(r"^(?!-)[a-z0-9-]{1,63}(?<!-)$")


def normalize_hostname(value):
    """Return the hostname in canonical form, or None if it is not usable.

    Clients send whatever their site is configured with, so the value is
    lowercased and stripped of a trailing dot, then must be a dotted name
    (IPv4 addresses pass) outside the reserved domains of BAD_HOSTNAME_LIST.
    """
    hostname = value.strip().lower().rstrip(".")
    if len(hostname) > 253:
        return None
    labels = hostname.split(".")
    if len(labels) < 2:
        return None
    if not all(HOSTNAME_LABEL_RE.match(label) for label in labels):
        return None
    for bad_hostname in constants.BAD_HOSTNAME_LIST:
        if hostname == bad_hostname or hostname.endswith("." + bad_hostname):
            return None
    return hostname
