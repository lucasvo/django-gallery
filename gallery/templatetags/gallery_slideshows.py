import re

from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

from django.template import Context, loader
from django import template
from gallery.models import Album, Object
from gallery.config import ADMIN_IMAGE_SIZE
from gallery.views import calculate_size


register = Library()

class SlideshowNode(template.Node):
    def __init__(self, id, size_str):
        self.id = id
        self.size_str = size_str

    def render(self, context):
        from gallery_extras import get_size

        try:
            album = Album.objects.get(pk=self.id)
        except:
            return "Album with ID: "+str(id)+" not found."
        object = album.get_objects()[0]

        m = re.findall('(\d+)', self.size_str)
        if m:
            swidth, sheight = m
            size_str = '%sx%s' % (swidth, sheight)
        else:
            size_str = '200x200'

        int_size = get_size(size_str)
        width, height = calculate_size(object.get_size(), int_size, min)

        t = loader.get_template('gallery/slideshows/slideshow.html')
        c = Context({
            'object':object,
            'album_id':self.id,
            'next_page':2,
            'iwidth':width,
            'iheight':height,
            'show_container':True,
            'image_size_str':size_str,
        })
        return mark_safe(t.render(c))


@register.tag()
def slideshow(parser, token):
    tag_name, id, size_str = token.split_contents()
    return SlideshowNode(id, size_str)

