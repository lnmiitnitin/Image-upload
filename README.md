# Image Upload API
 1. create virualenv inside image_api folder.
 2. Install requirements as mentioned in the requirements.txt
 3. start redis on server with host_name=127.0.0.1 and port=6379
 4. Run following command to start celery to support async task
      ```python
         celery -A api  worker -l info
       ```
 5. start web server by following commands within virtualenv
      ```python
         python manage.py runserver
       ```
 Test Api
    1. upload images api
       ```
       http://127.0.0.1:8000/api/v1/images/upload/
       ```
    2. job status of upload api
       ```
       http://127.0.0.1:8000/api/v1/images/upload/94a074e4-e354-4dbb-82c9-e3c851b98299
       ```
    3. Get all uploaded images
       ```
       http://127.0.0.1:8000/api/v1/images
       
       ```
