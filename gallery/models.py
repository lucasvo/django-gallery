from django.conf import settings
from django.db import models
from django.db.models import permalink

import os.path
import datetime
import time
import re

from gallery.config import IMAGE_SIZES, ADMIN_IMAGE_SIZE

class Album(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    position = models.IntegerField(default=0)

    ORDERING_CHOICES = (
            ('d', 'Sort by date (ascending)'),
            ('D', 'Sort by date (descending)'),
            ('f', 'Sort by file name (ascending)'),
            ('F', 'Sort by file name (descending)'),
            ('m', 'Sort manually'),
        )
    ordering = models.CharField(max_length=1, choices=ORDERING_CHOICES, default='d')

    preview = models.ForeignKey('Object', null=True, blank=True, related_name='preview')

    def get_preview(self):
        if not self.preview:
            objects = self.get_objects()
            if objects:
                return objects[0]
        else:
            return self.preview

    @permalink
    def get_absolute_url(self):
        return ('gallery.views.album_view', (self.id,))

    def __unicode__(self):
        return self.name

    def admin_preview_thumbnail(self):
        from gallery.templatetags.gallery_extras import resized_image
        return '<a href="%d/">%s</a>' % (self.id, resized_image(self.preview, '512x128'))
    admin_preview_thumbnail.short_description = 'Preview'
    admin_preview_thumbnail.allow_tags = True

    def number_of_objects(self):
        return self.object_set.count()

    def reorder_objects(self):
        objects = self.object_set.all()
        objects = objects.order_by('name')
        for n, object in enumerate(objects):
            object.position = n+1
            object.save()

    def get_objects(self):
        objects = self.object_set.all()

        if objects.filter(position=0):
            self.reorder_objects()

        return objects

    def delete(self):
        # Explicitly delete all objects, so they thumbnails get deleted.
        for o in self.object_set.all():
            o.delete()
        super(Album, self).delete()
        
    class Meta:
        ordering = ('position',)

class Object(models.Model):
    album = models.ForeignKey(Album)

    TYPE_CHOICES = (
            ('p', 'Photo'),
            ('m', 'Movie'),
        )
    type = models.CharField(max_length=1, choices=TYPE_CHOICES)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    original = models.FileField(upload_to='gallery/originals/', null=True, blank=True, max_length=255)

    position = models.IntegerField(default=0)

    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)

    date = models.DateTimeField(null=True, blank=True)

    def get_next(self):
        try:
            return self.album.object_set.filter(position__gt=self.position).order_by('position')[0]
        except IndexError:
            return None

    def get_previous(self):
        try:
            return self.album.object_set.filter(position__lt=self.position).order_by('-position')[0]
        except IndexError:
            return None

    def get_next_url(self):
        next = self.get_next()
        if next:
            return next.get_absolute_url()
        else:
            return self.album.get_absolute_url()

    def get_previous_url(self):
        prev = self.get_previous()
        if prev:
            return prev.get_absolute_url()
        else:
            return self.album.get_absolute_url()

    def open(self, rotate=True):
        import Image
        image = Image.open(self.original.path)

        if rotate:
            # Try to respect EXIF rotation
            # TODO: This is a bit hacky
            try:
                exif = image._getexif()
                orientation = exif[274]
            except:
                orientation = None
                #date = datetime.datetime.fromtimestamp(os.path.getmtime(self.get_original_filename()))

            # TODO: This is untested.
            if orientation == 6:
                image = image.rotate(270)
            elif orientation == 3:
                image = image.rotate(180)
            elif orientation == 8:
                image = image.rotate(90)

        # TODO: date (306)

        return image

    def update_properties(self, image=None):
        if not image:
            image = self.open(rotate=False)

        # TODO: This is a bit hacky
        try:
            exif = image._getexif()
            try:
                date = exif[36867]
            except:
                date = exif[306]
            #print 'exif', date
            if date:
                # from http://snippets.dzone.com/posts/show/4089
                date = datetime.datetime(*(time.strptime(date, "%Y:%m:%d %H:%M:%S")[0:6]))
                #print 'ok', date
        except:
            #date = datetime.datetime.fromtimestamp(os.path.getmtime(self.get_original_filename()))
            date = None

        if date:
            self.date = date

        self.save()

    def set_size(self, size=None):
        if not size:
            image = self.open()
            self.update_properties(image)
            size = image.size
        self.width = size[0]
        self.height = size[1]
        self.save()

    def get_size(self):
        if not self.width:
            self.set_size()
        return (self.width, self.height)

    def __unicode__(self):
        return self.name

    def generate_thumbnails(self):
        for size in IMAGE_SIZES:
            self.generate_thumbnail(size)

    def generate_thumbnail(self, size):
        pass

    @permalink
    def get_url_for_exact_size(self, size):
        return ('gallery.views.generate_thumbnail',
            (self.album.id, self.id, size[0], size[1]))

    def get_url_for_size(self, size):
        from views import calculate_size, thumbnail_exists
        real_size = calculate_size(self.get_size(), size)
        if real_size[0] >= self.width and real_size[1] >= self.height:
            return self.original.url
        for ts in IMAGE_SIZES:
            if real_size[0] <= ts[0] and real_size[1] <= ts[1]:
                url = thumbnail_exists(self, ts)
                if not url:
                    return self.get_url_for_exact_size(ts)
                else:
                    return url

        # Do not return the original
        return self.get_url_for_exact_size(ts)

    def delete(self):
        # Delete any thumbnails, if they exist.
        # TODO: Better implementation
        folder_re = re.compile('size_[0-9]+x[0-9]')
        dirs = [d for d in os.listdir(os.path.join(settings.MEDIA_ROOT, 'gallery')) if folder_re.match(d)]
        basename = os.path.basename(self.original.name)
        for d in dirs:
            name = os.path.join(settings.MEDIA_ROOT, 'gallery', d, basename)
            if os.path.exists(name):
                try:
                    os.unlink(name)
                except OSError:
                    pass
        super(Object, self).delete()

    def get_url_for_admin(self):
        return self.get_url_for_size(ADMIN_IMAGE_SIZE)

    @permalink
    def get_absolute_url(self):
        return ('gallery.views.album_view_object', (self.album.id, self.id,))

    class Meta:
        ordering = ('position',)

class Comment(models.Model):
    object = models.ForeignKey(Object)
    name = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    homepage = models.CharField(max_length=100, null=True, blank=True)
    text = models.TextField()
    ip = models.IPAddressField()
    date = models.DateTimeField()

    def __unicode__(self):
        return '%s (%s)' % (self.name, self.object)
