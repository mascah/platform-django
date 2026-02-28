release: python manage.py migrate
web: gunicorn config.wsgi:application
worker: REMAP_SIGTERM=SIGQUIT celery -A config.celery_app worker --loglevel=info --without-gossip --without-mingle --heartbeat-interval=60
beat: REMAP_SIGTERM=SIGQUIT celery -A config.celery_app beat --loglevel=info --max-interval 60
