# -*- coding: utf-8 -*-
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _
from django.utils import translation

from gallery import models


import os
import datetime

import Image

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def get_context(request):
    from cms.views import get_page_context
    from cms.models import Page
    c = get_page_context(request, translation.get_language(), Page.objects.get(pk=settings.GALLERY_PAGE_ID))

    c.update({'title': 'Gallery'})
    return c


class AjaxSlideError(Exception):
    """Exception for ajax slide show"""


def ajax_slide(request, page_number, album_id, width, height):
    """A method called by an Ajax request which shows an image
    as part of a slide show
    """
    page_dict = {}
    page_number = int(page_number)

    album = get_object_or_404(models.Album, pk=album_id)
    objects = album.get_objects()

    album_size = len(objects)
    if not album_size >= page_number - 1:
        raise AjaxSlideError(
                "Trying to access page %s for album id %s, "
                "but the album only have %s images"
                % (page_number, album_id, album_size))

    page_dict['album_id'] = album_id
    object = objects[page_number - 1]
    page_dict['object'] = object

    page_dict['iwidth'] = width
    page_dict['iheight'] = height
    page_dict['image_size_str'] = "%sx%s" % (width, height)

    if album_size > 1:
        if page_number > 1:
            page_dict['previous_page'] = page_number - 1
        if page_number < album_size:
            page_dict['next_page'] = page_number + 1
    return render_to_response('gallery/ajax_view_img.html', page_dict)


def object_view(view_func):
    def _func(request, album_id, object_id, *args, **kwargs):
        album = get_object_or_404(models.Album, pk=album_id)
        object = get_object_or_404(models.Object, pk=object_id)
        if object.album != album:
            raise Http404
        return view_func(request, object, *args, **kwargs)
    return _func



def album_index(request):
    albums = models.Album.objects.filter(parent__isnull=True)
    return render_to_response('gallery/index.html', {
        'albums': albums,
    }, context_instance=get_context(request))


def album_view(request, id):
    album = get_object_or_404(models.Album, pk=id)
    #objects = album.object_set.all()
    #objects = objects.order_by('date', 'name')
    #objects = objects.order_by('name')
    objects = album.get_objects()
    #print [o.date for o in objects]
    return render_to_response('gallery/album.html', {
        'album': album,
        'objects': objects,
    }, context_instance=get_context(request))

class EmptyInput(forms.widgets.TextInput):
    def render(self, name, value, attrs=None):
        # Clear the value when rerendering the form.
        value = None
        return super(EmptyInput, self).render(name, value, attrs)

class CommentForm(forms.ModelForm):
    captcha = forms.CharField(max_length=10, help_text=_(u'Enter the word you see on the image below:'), widget=EmptyInput)

    class Meta:
        model = models.Comment
        fields = ('name', 'email', 'homepage', 'text')

    def clean_captcha(self):
        captcha = self.cleaned_data.get('captcha')
        # Make sure the captcha is provided and matches
        if not captcha or captcha != self.request.session['captcha']:
            raise forms.ValidationError(_(u'The captcha does not match. Please try again.'))

    def __init__(self, request):
        super(CommentForm, self).__init__(request.method == 'POST' and request.POST or None)
        self.request = request

@object_view
def album_view_object(request, object):
    form = CommentForm(request)
    success = False
    if request.method == 'POST':
        if form.is_valid():
            comment = form.save(commit=False)
            comment.object = object
            comment.ip = request.META['REMOTE_ADDR']
            comment.date = datetime.datetime.now()
            comment.save()
            success = True

    request.session['captcha'] = None

    if success:
        return HttpResponseRedirect('')

    comment_list = object.comment_set.all()

    return render_to_response('gallery/object.html', {
        'form': form,
        'album': object.album,
        'object': object,
        'comment_list': comment_list,
    }, context_instance=get_context(request))

@object_view
def album_view_next(request, object):
    next = object.get_next()
    if next:
        return HttpResponseRedirect(next.get_absolute_url())
    else:
        return HttpResponseRedirect(object.album.get_absolute_url())


@object_view
def album_view_previous(request, object):
    prev = object.get_prev()
    if prev:
        return HttpResponseRedirect(prev.get_absolute_url())
    else:
        return HttpResponseRedirect(object.album.get_absolute_url())


def get_file_path(filename, size):
    dirname = 'size_%dx%d' % size
    return os.path.join(settings.MEDIA_ROOT, 'gallery', dirname, filename)


def get_file_url(filename, size):
    dirname = 'size_%dx%d' % size
    return settings.MEDIA_URL+'/'.join(['gallery', dirname, filename])


def calculate_size(size, boundaries, f=min):
    ratio = size[0] / float(size[1])
    scale = f(float(boundaries[0])/size[0], float(boundaries[1])/size[1])
    if scale > 1:
        scale = 1
    return (int(size[0]*scale), int(size[1]*scale))

def thumbnail_exists(object, boundaries):
    filename = object.original.path
    basename = os.path.basename(object.original.name)
    output_filename = get_file_path(basename, boundaries)

    if os.path.exists(output_filename):
        if not os.path.getmtime(filename) > os.path.getmtime(output_filename):
            return get_file_url(basename, boundaries)
        else:
            os.unlink(output_filename)


def generate_thumbnail(request, album_id, object_id, w, h):
    boundaries = (int(w), int(h))
    object = get_object_or_404(models.Object, pk=object_id)

    url = thumbnail_exists(object, boundaries)
    if url:
        return HttpResponseRedirect(url)
    else:
        # XXX: Duplicate code
        basename = os.path.basename(object.original.name)
        output_filename = get_file_path(basename, boundaries)

    image = object.open()
    object.set_size(image.size)

    size = calculate_size(image.size, boundaries)

    if image.mode not in ('L', 'RGBA'):
        image = image.convert('RGBA')

    image = image.resize(size, Image.ANTIALIAS)
    
    # TODO: Use os.path.exists
    try:
        os.mkdir(os.path.dirname(output_filename))
    except OSError: # Probably the directory already exists
        pass
    
    image.save(output_filename, image.format)

    return HttpResponseRedirect(get_file_url(basename, boundaries))