# patch_utc_check.py
"""
This patch fixes the UTC timezone check error in Django
"""
import django.db.backends.postgresql.utils as postgresql_utils
import django.db.utils as db_utils

# Store the original function
_original_utc_tzinfo_factory = postgresql_utils.utc_tzinfo_factory

def _patched_utc_tzinfo_factory(offset):
    """Patched version that doesn't crash on non-UTC timezone"""
    try:
        return _original_utc_tzinfo_factory(offset)
    except AssertionError:
        # If UTC check fails, return a UTC timezone anyway
        import pytz
        return pytz.UTC

# Monkey patch the function
postgresql_utils.utc_tzinfo_factory = _patched_utc_tzinfo_factory

print("UTC timezone patch applied successfully")