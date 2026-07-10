import re

# Common patterns for secrets
SECRET_PATTERNS = [
    # AWS Access Key ID
    r"(?i)\b(AKIA[0-9A-Z]{16})\b",
    # AWS Secret Access Key
    r"(?i)(aws_secret_access_key\s*=\s*['\"])([a-zA-Z0-9/+=]{40})(['\"])",
    # Passwords in URLs (e.g., http://user:password@host)
    r"(?i)(://[^:]+:)([^@]+)(@)",
    # JSON passwords/tokens (e.g., "password": "my_secret", 'token': 'abc')
    r"(?i)((?:password|secret|token|api_key|apikey|auth)[\"']?\s*[:=]\s*[\"'])([^\"']+)([\"']?)",
    # Bearer tokens
    r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]+)\b",
]

# Compile patterns
_COMPILED_PATTERNS = [re.compile(p) for p in SECRET_PATTERNS]


from typing import Any


def mask_secrets_in_string(text: Any) -> str:
    """Replaces matched secrets in the string with asterisks."""
    if not text or not isinstance(text, str):
        return str(text) if text is not None else ""

    for pattern in _COMPILED_PATTERNS:
        # We need to replace only the matched group if one exists, otherwise the whole match.
        # It's safer to just replace the whole match if no groups, but our patterns heavily use lookbehinds.
        # The lookbehinds aren't part of the match, so we just replace the match.

        def replacer(match: re.Match) -> str:
            groups = match.groups()
            if len(groups) == 3:
                # Group 1 is prefix, Group 2 is secret, Group 3 is suffix
                return f"{groups[0]}********{groups[2]}"
            elif len(groups) == 2:
                # Group 1 is prefix, Group 2 is secret
                return f"{groups[0]}********"
            else:
                return "********"

        text = pattern.sub(replacer, text)

    return str(text)


def mask_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively mask secrets in a dictionary."""
    masked: dict[str, Any] = {}
    secret_keys = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "auth",
        "access_token",
    }

    for key, value in data.items():
        key_str = str(key).lower()
        is_secret_key = any(s in key_str for s in secret_keys)

        if is_secret_key and isinstance(value, str):
            masked[key] = "*" * 8
        elif isinstance(value, dict):
            masked[key] = mask_dict(value)
        elif isinstance(value, list):
            masked[key] = [
                (
                    mask_dict(i)
                    if isinstance(i, dict)
                    else (mask_secrets_in_string(str(i)) if isinstance(i, str) else i)
                )
                for i in value
            ]
        elif isinstance(value, str):
            masked[key] = mask_secrets_in_string(value)
        else:
            masked[key] = value

    return masked
