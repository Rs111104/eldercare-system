from alembic import command
from alembic.config import Config
import os

here = os.path.dirname(__file__)
root = os.path.abspath(os.path.join(here, '..'))
rc = Config(os.path.join(root, 'alembic.ini'))
rc.set_main_option('script_location', os.path.join(root, 'alembic'))

# Use DATABASE_URL from environment if present
import sys
# ensure project root is on sys.path so `import app` works when running this script
if root not in sys.path:
    sys.path.insert(0, root)

from app.config import settings
if settings.DATABASE_URL:
    rc.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

if __name__ == '__main__':
    # allow applying multiple heads if repository contains multiple heads
    try:
        command.upgrade(rc, 'head')
    except Exception:
        command.upgrade(rc, 'heads')
