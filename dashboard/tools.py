"""Some tools."""

import datetime
import re
from urllib.parse import urlparse

from django.conf import settings
from django.utils import timezone

LINE_PATTERN = (
    r'(\S+)\s+\S+\s+\S+\s+'        # IP address (v4 or v6), idents
    r'\[([^\]]+)\]\s+'              # datetime
    r'"([A-Z]+)\s+(\S+)[^"]*"\s+'     # method and path
    r'(\d+)\s+'                      # status
    r'(\d+)\s+'                      # bandwidth
    r'"([^"]*)"\s+'                   # referrer
    r'"([^"]*)"'                      # user agent
)

ALLOWED_SERVICE_LIST = (
    "/extensions",
    "/versions",
    "/instances",
    "/current_version",
)

# 09/Oct/2016:06:25:33 +0200
DATETIME_FORMAT = "%d/%b/%Y:%H:%M:%S %z"
NAIVE_DATETIME_FORMAT = "%d/%b/%Y:%H:%M:%S"

VERSION_PATTERN = re.compile(r"(\d+)(?:\.(\d+))?(?:\.(\d+))?")


def version_tuple(version):
    """Turn a free-form version into a comparable tuple.

    known_version is a plain CharField fed by the clients, so it can hold
    anything from "2.10.0" to "1.10.2.dev5+ga327ccf0". Only the leading
    numeric components are meaningful; missing ones count as 0 and an
    unparsable value sorts first.
    """
    match = VERSION_PATTERN.match(version or "")
    if not match:
        return (0, 0, 0)
    return tuple(int(part) if part else 0 for part in match.groups())


def parse_log_datetime(value):
    """Return an aware datetime from an nginx $time_local field.

    The UTC offset is part of the field and must be kept, otherwise the
    period is off by the server offset and mixes naive datetimes into a
    USE_TZ project. Return None when the field cannot be read.
    """
    try:
        return datetime.datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        pass
    try:
        naive = datetime.datetime.strptime(value, NAIVE_DATETIME_FORMAT)
    except ValueError:
        return None
    return timezone.make_aware(naive)


def parse_access_logs():
    """Parse nginx logs.

    Always return a (services, period) tuple. period is None when no
    usable content could be read, so the dashboard degrades instead of
    crashing when the log file is not configured or not readable. It is
    computed from the counted hits themselves, the log being not
    necessarily ordered.
    """
    log_path = getattr(settings, "NGINX_LOG_FILE_PATH", "")
    if not log_path:
        return {}, None
    pattern = re.compile(LINE_PATTERN)
    services = {}
    from_datetime = None
    to_datetime = None
    try:
        with open(log_path) as fp:
            # Production logs are big: never load the whole file in memory.
            for line in fp:
                match = pattern.search(line)
                if match is None:
                    continue
                ip_address, raw_datetime = match.group(1), match.group(2)
                # Strip the API version prefix, if any.
                path = urlparse(match.group(4)).path.removeprefix("/1")
                for asrv in ALLOWED_SERVICE_LIST:
                    if not path.startswith(asrv):
                        continue
                    if asrv == "/instances" and path != "/instances/search/":
                        path = "/instances/update/"
                    stats = services.setdefault(
                        path, {"total": 0, "ips": set()})
                    stats["total"] += 1
                    stats["ips"].add(ip_address)
                    break
                else:
                    continue
                timestamp = parse_log_datetime(raw_datetime)
                if timestamp is None:
                    continue
                if from_datetime is None or timestamp < from_datetime:
                    from_datetime = timestamp
                if to_datetime is None or timestamp > to_datetime:
                    to_datetime = timestamp
    except OSError:
        return {}, None
    if from_datetime is None:
        return services, None
    return services, [from_datetime, to_datetime]
