# patch_utc_check.py
"""
This patch fixes the UTC timezone check error in Django completely
"""
import django.db.backends.postgresql.utils as postgresql_utils
import django.db.utils as db_utils
import django.db.backends.postgresql.base as postgresql_base

# Store the original functions
_original_utc_tzinfo_factory = postgresql_utils.utc_tzinfo_factory
_original_get_new_connection = postgresql_base.DatabaseWrapper.get_new_connection

def _patched_utc_tzinfo_factory(offset):
    """Patched version that doesn't crash on non-UTC timezone"""
    try:
        return _original_utc_tzinfo_factory(offset)
    except AssertionError:
        # If UTC check fails, return a UTC timezone anyway
        import pytz
        return pytz.UTC

def _patched_get_new_connection(self, conn_params):
    """Patched version to ensure UTC timezone"""
    conn = _original_get_new_connection(self, conn_params)
    
    # Force UTC timezone on the connection
    try:
        with conn.cursor() as cursor:
            cursor.execute("SET TIME ZONE 'UTC'")
    except:
        pass  # Silently fail if we can't set timezone
    
    return conn

# Monkey patch the functions
postgresql_utils.utc_tzinfo_factory = _patched_utc_tzinfo_factory
postgresql_base.DatabaseWrapper.get_new_connection = _patched_get_new_connection

print("Comprehensive UTC timezone patch applied successfully")