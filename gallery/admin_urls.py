from django.conf.urls.defaults import *

urlpatterns = patterns('gallery',
    (r'^gallery/album/add/$', 'admin_views.album_add_edit'),
    (r'^gallery/album/([0-9]+)/$', 'admin_views.album_add_edit'),
    (r'^gallery/album/([0-9]+)/objectlist/$', 'admin_views.album_objectlist'),
    (r'^gallery/album/([0-9]+)/upload/$', 'admin_views.album_upload'),
    (r'^gallery/album/([0-9]+)/upload/([0-9a-f]+)/$', 'admin_views.album_upload'),
    (r'^gallery/album/([0-9]+)/([0-9]+)/set_preview/$', 'admin_views.album_object_set_preview'),
    (r'^gallery/album/([0-9]+)/([0-9]+)/set_description/$', 'admin_views.album_object_set_description'),
    (r'^gallery/album/([0-9]+)/([0-9]+)/delete/$', 'admin_views.album_object_delete'),
)
