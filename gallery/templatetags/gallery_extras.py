from django.template import Library
from django.utils.html import escape
from django.utils.safestring import mark_safe

from gallery.settings import ADMIN_IMAGE_SIZE
from gallery.views import calculate_size


register = Library()

def get_size(size):
    if not size:
        return ADMIN_IMAGE_SIZE
    else:
        return [int(x) for x in size.split('x')]


def resized_url(object, size=None):
    return object.get_url_for_size(get_size(size))

register.filter(resized_url)


def resized_image(object, size=None):
    if not object:
        return ''
    if size == 'admin':
        size = None
        f = max
    else:
        f = min
    if size and size[-1] == 'm':
        size = size[:-1]
        f = max
    int_size = get_size(size)
    w, h = calculate_size(object.get_size(), int_size, f)
    return mark_safe('<img src="%s" width="%d" height="%d" alt="%s">' % (
            resized_url(object, size),
            w,
            h,
            escape(object.name)
        ))

register.filter(resized_image)
