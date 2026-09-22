"""Constants."""

# Default or reserved names (RFC 2606, RFC 6761) that installations report
# when they are not configured. Subdomains are rejected too, so
# mail.example.com and localhost.localdomain are filtered out.
BAD_HOSTNAME_LIST = [
    "localhost",
    "localdomain",
    "example",
    "example.com",
    "example.net",
    "example.org",
    "invalid",
    "test",
]

# Upper bound for the statistics counters sent by instances, well above
# any real installation, so a single client cannot skew the totals.
MAX_COUNTER_VALUE = 1000000

# Official extensions are a few dozens.
MAX_EXTENSIONS = 100
