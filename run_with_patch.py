# run_with_patch.py
#!/usr/bin/env python
"""
Run Django commands with UTC patch applied first
"""
import os
import sys

# Apply the patch first
import patch_utc_check

# Now run the Django command
if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hospitalmanagement.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)