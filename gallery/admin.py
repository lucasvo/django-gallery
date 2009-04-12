from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Template, Context, loader
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden, HttpResponseNotAllowed
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django import forms
from django.core.files import File

from PIL import Image
import cStringIO

from django.conf.urls.defaults import *

from django.contrib import admin

from gallery.models import Album
from gallery.models import Object
from gallery.models import Comment
from gallery.settings import *

class AlbumForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}))
    class Meta:
        model = Album
        fields = ('name', 'description',  'position', 'ordering')
    
class AlbumAdmin(admin.ModelAdmin):
    list_display = ['name', 'admin_preview_thumbnail', 'number_of_objects']
    
    def get_urls(self):
        urls = super(AlbumAdmin, self).get_urls()
        album_urls = patterns('',
            url(r'add/$', self.admin_site.admin_view(self.album_add_edit)),
            url(r'([0-9]+)/reorder/$', self.admin_site.admin_view(self.album_reorder)),
            url(r'([0-9]+)/([0-9]+)/$', self.admin_site.admin_view(self.object_edit)),
            url(r'([0-9]+)/$', self.admin_site.admin_view(self.album_add_edit)),
            url(r'([0-9]+)/objectlist/$', self.admin_site.admin_view(self.album_objectlist), name="album_object_list"),
            url(r'([0-9]+)/upload/$', self.album_upload),
            url(r'([0-9]+)/([0-9]+)/delete/$', self.admin_site.admin_view(self.album_object_delete)),
        )
        return album_urls + urls

    def get_album_and_object(self,album_id, object_id):
        """TODO: Maybe move this to a manger or the model?"""
        album = get_object_or_404(Album, pk=album_id)
        object = get_object_or_404(Object, pk=object_id)
        if object.album != album:
            raise Http404
        return album, object
    
    def album_add_edit(self, request, id=None):
        model = self.model
        opts = model._meta
        
        if id:
            album = get_object_or_404(Album, pk=id)
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
                        
        return render_to_response('admin/gallery/album_add_edit.html', {
                'title':'%s %s' % (add and _('Add') or _('Edit'), _('album')),            
                'album': album,
                'add': add,
                'form':form,
                'root_path':self.admin_site.root_path,
                'opts':opts,
                'sessionid':request.COOKIES[settings.SESSION_COOKIE_NAME],
            }, context_instance=RequestContext(request))
            
    def album_objectlist(self, request, id=None):
        album = get_object_or_404(Album, pk=id)
        objects = album.get_objects()
        
        return render_to_response('admin/gallery/album_objectlist.html', {
            'album': album,
            'objects':objects,
        }, context_instance=RequestContext(request))
        
    def album_upload(self, request, id=None):
        album = get_object_or_404(Album, pk=id)

        # We are getting the session id in the URL, so we can't just use request.user. Flash has a 
        # different cookie storage and does not send the sessionid cookie from django.
        if request.GET.get('ssid'):
            sessionid = request.GET['ssid']
        else: 
            return HttpResponseForbidden()
        
        if sessionid:
            from django.contrib.sessions.middleware import SessionMiddleware
            from django.contrib.auth import get_user
            request.COOKIES[settings.SESSION_COOKIE_NAME] = sessionid
            SessionMiddleware().process_request(request)
            user = get_user(request) 
        else:
            user = request.user
    
        # Make sure the user has permission
        if not user.is_staff:
            return HttpResponseForbidden()
    
        # Finally handle the upload
        filedata = request.FILES['Filedata']

        if filedata.size > MAX_FILE_SIZE:
            print "Image file too big"
            return HttpResponseNotAllowed("Image too big")
                
        # Check if it's an image
        image_content = cStringIO.StringIO()

        for chunk in filedata.chunks():
            #print dir(image_content)
            image_content.write(chunk)
            image_content.seek(0)
        try:
            img = Image.open(image_content)
        except Exception, e:
            print e
            return HttpResponseNotAllowed(str(e))
            
        if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
            print "Image size too big"
            return HttpResponseNotAllowed(str("Image size too big"))

        # Save it
        object = Object(
                album=album,
                type='p',
                name=str(filedata),
            )
        
        object.original.save(str(filedata), filedata, save=True)
        
        object.save()

        return HttpResponse('OK')
        
    def object_edit(self, request, album_id, object_id):
        if request.method != "POST":
            return HttpResponseNotAllowed('No POST Data')
        album, object = self.get_album_and_object(album_id, object_id)
        if request.POST.get('name', None):
            object.name = request.POST['name']
        if request.POST.get('caption', False):
            object.caption = request.POST['caption']
        if request.POST.get('preview', None) == "on":
            album.preview = object
            album.save()
        object.save()
        return HttpResponse('OK')
         
    def album_object_delete(self, request, album_id, object_id):
        album, object = self.get_album_and_object(album_id, object_id)
        # Do not delete the whole album when deleting the preview object!
        if album.preview == object:
            album.preview = None
            album.save()
        object.delete()
        
        return HttpResponseRedirect('../../')
        
    def album_reorder(self, request, album_id):
        objects = request.POST.getlist('object[]')
        i = 0
        for id in objects:
            object = Object.objects.get(pk=id)
            object.position = i
            i = i+1
            object.save()
        return HttpResponse('OK')

admin.site.register(Album, AlbumAdmin)
    
class ObjectAdmin( admin.ModelAdmin ):
    list_display = ['name', 'position']
    list_filter = ['album', ]
    
admin.site.register(Object, ObjectAdmin)  
  
class CommentAdmin(admin.ModelAdmin):
    list_display = ['object', 'name', 'email', 'ip', 'date']

admin.site.register(Comment, CommentAdmin)
