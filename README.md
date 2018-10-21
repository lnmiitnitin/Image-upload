# Image-upload
 1. create virualenv inside image_api folder.
 2. Install requirements we mentioned in the requirements.txt
 3. start redis on server with host_name=127.0.0.1 and port=6379
 4. Run following command to start celery to support async task
      celery -A api  worker -l info
 5. start web server by following commands within virtualenv
      python manage.py runserver
