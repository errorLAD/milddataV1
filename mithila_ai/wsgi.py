"""
WSGI config for mithila_ai project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import logging
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mithila_ai.settings")

application = get_wsgi_application()

# Auto-run database migrations & seed CMS defaults on container startup
try:
    from django.core.management import call_command
    call_command("migrate", interactive=False)
    try:
        call_command("seed_cms_data")
    except Exception:
        pass
except Exception as e:
    logging.getLogger(__name__).warning(f"Startup migration warning: {e}")

