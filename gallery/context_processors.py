from gallery.config import ADMIN_IMAGE_SIZE
from gallery import models

import installation_settings

def get_random_image():
    """
    Returns a random image or returns an empty variable
    """
    if'gallery' in installation_settings.INSTALLED_APPS:
        try:
            image = models.Object.objects.all().order_by('?')[0]
        except IndexError:
            image = None
    else: 
        image = None
    return image


def gallery(self):
    return {
        'admin_image_size': ADMIN_IMAGE_SIZE,
        'random_gallery_image': get_random_image(),
    }
