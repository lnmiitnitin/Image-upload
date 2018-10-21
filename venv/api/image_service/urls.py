from django.conf.urls import url
from .views import UploadImagesView,ListImageView,GetUploadStatusView


urlpatterns = [
    url('images/upload/(?P<job_id>[A-Za-z0-9_@./#&+-]*)/$', GetUploadStatusView.as_view(), name="check-status"),
    url('^images/upload/$', UploadImagesView.as_view(), name="upload-image"),
    url('^images/$', ListImageView.as_view(), name="images-all"),
]
