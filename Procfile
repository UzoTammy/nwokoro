release: python manage.py migrate
web: gunicorn nwokoro.wsgi --worker-class gthread --threads 4 --timeout 120
worker: celery -A nwokoro worker --loglevel=info
beat: celery -A nwokoro beat --loglevel=info