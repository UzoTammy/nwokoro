web: gunicorn nwokoro.wsgi
worker: celery -A nwokoro worker --loglevel=info
beat: celery -A nwokoro beat --loglevel=info