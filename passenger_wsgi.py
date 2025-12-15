import sys, os

PROJECT_HOME = '/home/bilimsto/bookstore'
if PROJECT_HOME not in sys.path:
    sys.path.insert(0, PROJECT_HOME)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.backend.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
