"""
Runtime security mitigations applied at process startup.

Each mitigation here should reference the ticket / advisory it addresses
and be removed once the underlying issue is properly resolved (typically
by a dependency upgrade).
"""

import requests.adapters


_original_send = requests.adapters.HTTPAdapter.send


def _force_identity_encoding(self, request, *args, **kwargs):
    """Mitigation for GHSA-mf9v-mfxr-j63j (CTO-4807).

    urllib3 < 2.7.0 has a decompression-bomb safeguard bypass in parts of
    its streaming API. urllib3 2.7.0 (the patched version) requires
    Python >= 3.10, but this project's CI matrix still includes Python 3.9
    so we cannot bump the pin.

    Forcing Accept-Encoding: identity on every outbound HTTP request makes
    servers return uncompressed bodies, so urllib3's decompression code
    path is never exercised at runtime and the bug cannot trigger.

    Remove this patch (and the import from EnigmaAutomation/__init__.py)
    once the Python runtime is upgraded and urllib3 can be bumped to
    >= 2.7.0.
    """
    request.headers["Accept-Encoding"] = "identity"
    return _original_send(self, request, *args, **kwargs)


requests.adapters.HTTPAdapter.send = _force_identity_encoding
