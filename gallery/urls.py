from django.conf.urls.defaults import *
urlpatterns = patterns('gallery',
    (r'^$', 'views.album_index'),
    (r'^ajax/(\d+)/(\d+)/(\d+)/(\d+)/$', 'views.ajax_slide'),
    (r'^([0-9]+)/$', 'views.album_view'),
    (r'^([0-9]+)/([0-9]+)/([0-9]+)x([0-9]+)/$', 'views.generate_thumbnail'),
    (r'^([0-9]+)/([0-9]+)/$', 'views.album_view_object'),
    (r'^([0-9]+)/([0-9]+)/next/$', 'views.album_view_next'),
    (r'^([0-9]+)/([0-9]+)/previous/$', 'views.album_view_previous'),
)
