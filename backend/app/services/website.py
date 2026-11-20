"""Public website policy. No network requests are made when rendering a hospital."""
import ipaddress
import re
from urllib.parse import urlsplit


def safe_website_url(value):
    if not isinstance(value, str) or re.search(r'[\s\\<>"\x00-\x1f]', value):
        return None
    try:
        url = urlsplit(value)
        host = (url.hostname or '').lower().rstrip('.')
        if url.scheme not in ('http', 'https') or url.username or url.password or url.port not in (None, 80, 443):
            return None
        if '.' not in host or host.endswith(('.localhost', '.local', '.internal', '.test')) or host == 'metadata.google.internal':
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        if not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?', host) or host.replace('.', '').isdigit():
            return None
        return value
    except ValueError:
        return None


def public_website(url, status, evidence=None, checked_at=None):
    if status == 'verified' and safe_website_url(evidence) and checked_at:
        return safe_website_url(url)
    return None
