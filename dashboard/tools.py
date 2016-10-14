"""Some tools."""

import datetime
import re
from urlparse import urlparse

LOG_FILE = "/var/log/nginx/api.modoboa.org-access.log"

LINE_PATTERN = (
    r''
    '(\d+.\d+.\d+.\d+)\s-\s-\s'             # IP address
    '\[(.+)\]\s'                            # datetime
    '"(GET|POST|PUT)\s(.+)\s\w+/.+"\s'      # path
    '(\d+)\s'                               # status
    '(\d+)\s'                               # bandwidth
    '"(.+)"\s'                              # referrer
    '"(.+)"'                                # user agent
)

ALLOWED_SERVICE_LIST = (
    "/extensions",
    "/versions",
    "/instances",
    "/current_version",
)

DATETIME_FORMAT = "%d/%b/%Y:%H:%M:%S"  # 09/Oct/2016:06:25:33 +0200


def parse_access_logs():
    """Parse nginx logs."""
    pattern = re.compile(LINE_PATTERN)
    with open(LOG_FILE) as fp:
        match = pattern.findall(fp.read())
    if not match:
        return {}
    services = {}
    from_datetime = datetime.datetime.strptime(
        match[0][1].split(" ")[0], DATETIME_FORMAT)
    to_datetime = datetime.datetime.strptime(
        match[-1][1].split(" ")[0], DATETIME_FORMAT)
    for res in match:
        service = urlparse(res[3])
        path = service.path
        if path.startswith("/1"):
            path = service.path.replace("/1", "")
        for asrv in ALLOWED_SERVICE_LIST:
            if path.startswith(asrv):
                if asrv == "/instances" and path != "/instances/search/":
                    path = "/instances/update/"
                if path not in services:
                    services[path] = {"total": 0, "ips": []}
                services[path]["total"] += 1
                if res[0] not in services[path]["ips"]:
                    services[path]["ips"].append(res[0])
    return services, [from_datetime, to_datetime]
