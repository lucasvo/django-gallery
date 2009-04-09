# TODO: clean up
from django.template import RequestContext, Template, Context, loader
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django import forms

import Image
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from gallery import models
from gallery.config import MAX_FILE_SIZE, MAX_IMAGE_SIZE


class AlbumForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}))
    class Meta:
        model = models.Album
        #fields = ('name', 'description', 'parent', 'position', 'ordering', 'preview')
        fields = ('name', 'description', 'position',)


@staff_member_required
def album_add_edit(request, id=None):    
    if id:
        album = get_object_or_404(models.Album, pk=id)
        form = AlbumForm(request.method == 'POST' and request.POST or None, instance=album)
        add = False
    else:
        form = AlbumForm(request.method == 'POST' and request.POST or None)
        album = None
        add = True

    if request.method == 'POST':
        if form.is_valid():
            album = form.save()
            return HttpResponseRedirect('../%d/' % album.id)

    return render_to_response('gallery/album_add_edit.html', {
            'title':'%s %s' % (add and _('Add') or _('Edit'), _('album')),            
            'album': album,
            'add': add,
        }, context_instance=RequestContext(request))

@staff_member_required
def album_objectlist(request, id=None):
    album = get_object_or_404(models.Album, pk=id)

    return render_to_response('gallery/album_objectlist.html', {
            'album': album,
        }, context_instance=RequestContext(request))

def album_upload(request, id, sessionid=None):
    album = get_object_or_404(models.Album, pk=id)

    if sessionid:
        # We are getting the session id in the URL, so we can't just use request.user
        from django.contrib.sessions.middleware import SessionMiddleware
        from django.contrib.auth import get_user
        request.COOKIES[settings.SESSION_COOKIE_NAME] = sessionid
        SessionMiddleware().process_request(request)
        user = get_user(request) 
    else:
        user = request.user

    # For some reason, only the following status codes (which have a body) work:
    # 400 401 403 404 411 416 500 501 503 505

    # Make sure the user has permission
    if not user.is_staff:
        return HttpResponseForbidden()

    # Finally handle the upload
    filedata = request.FILES['fileinput']
    print "file size", filedata.size
    if filedata.size > MAX_FILE_SIZE:
        return HttpResponse(str(e), status=400)

    # Check if it's an image
    try:
        img = Image.open(StringIO(filedata['content']))
    except Exception, e:
        return HttpResponse(str(e), status=401)

    if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
        return HttpResponseNotAllowed("Image too big.")

    # Save it
    object = models.Object(
            album=album,
            type='p',
            name=str(filedata),
        )
    try:
        object.save_original_file(filedata['filename'], filedata['content'])
    except Exception, e:
        print e

    return HttpResponse('OK')

def get_album_and_object(album_id, object_id):
    album = get_object_or_404(models.Album, pk=album_id)
    object = get_object_or_404(models.Object, pk=object_id)
    if object.album != album:
        raise Http404
    return album, object

@staff_member_required
def album_object_set_preview(request, album_id, object_id):
    album, object = get_album_and_object(album_id, object_id)
    album.preview = object
    album.save()
    return HttpResponseRedirect('../../')

@staff_member_required
def album_object_set_description(request, album_id, object_id):
    album, object = get_album_and_object(album_id, object_id)
    object.description = request.POST.get('description')
    object.save()
    return HttpResponseRedirect('../../')

@staff_member_required
def album_object_delete(request, album_id, object_id):
    album, object = get_album_and_object(album_id, object_id)
    # Do not delete the whole album when deleting the preview object!
    if album.preview == object:
        album.preview = None
        album.save()
    object.delete()
    return HttpResponseRedirect('../../')
