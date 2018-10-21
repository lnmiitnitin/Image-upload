# Image-upload
# create virualenv inside image_api folder.
# Install requirements we mentioned in the requirements.txt
# start redis on server with host_name=127.0.0.1 and port=6379
# Run following command to start celery to support async task
  celery -A api  worker -l info
# start web server by following commands within virtualenv
  python manage.py runserver
