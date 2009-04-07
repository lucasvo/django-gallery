from gallery.models import Album
from gallery.models import Object
from gallery.models import Comment
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Template, Context, loader
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.conf import settings
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from django import forms

from django.contrib import admin
class AlbumForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 4, 'cols': 60}))
    class Meta:
        model = Album
        #fields = ('name', 'description', 'parent', 'position', 'ordering', 'preview')
        fields = ('name', 'description', 'position',)
    
class AlbumAdmin( admin.ModelAdmin ):
    
    list_display = ['name', 'admin_preview_thumbnail', 'number_of_objects']
    
    def __call__(self,request,url):
        print 'request',str(request)
        print "url", url
        if url is None:
            return super(AlbumAdmin, self).__call__(request, url)
            #return self.model
            #meta=model._meta
        if url.endswith('add'):
            # url(gallery/album/add/$)
            return self.album_add_edit(request)
        elif url.endswith('/objectlist'):
            #url(([0-9]+)/objectlist/$)
            self.album_objectlist(request)
        elif url.endswith('/upload'):
            # url(([0-9]+)/upload/$)
            self.album_upload(request)
        elif url.endswith('/set_preview'):
            # url(([0-9]+)/([0-9]+)/set_preview/$)
            self.album_object_set_preview(request)
        elif url.endswith('/set_description'):
            #url(([0-9]+)/([0-9]+)/set_description/)
            self.album_object_set_description(request)
        elif url.endswith('/delete'):
            #url(([0-9]+)/([0-9]+)/delete/$)
            self.album_object_delete(request)
        elif url.isdigit():
            #url(gallery/album/([0-9]+)/$)
            return self.album_add_edit(request)
        else:
            return super(AlbumAdmin, self).__call__(request, url)
    
    def album_add_edit(self,request, id=None):
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
        return render_to_response('gallery/album_add_edit.html', {
                'title':'%s %s' % (add and _('Add') or _('Edit'), _('album')),            
                'album': album,
                'add': add,
                'form':form,
                'root_path':self.admin_site.root_path,
                'opts':opts
            }, context_instance=RequestContext(request))
    def album_objectlist(self,request, id=None):
        album = get_object_or_404(Album, pk=id)

        return render_to_response('gallery/album_objectlist.html', {
            'album': album,
        }, context_instance=RequestContext(request))
    def album_upload(self,request, id, sessionid=None):
        album = get_object_or_404(Album, pk=id)
    
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
            return HttpResponse(str(e), status=416)
    
        # Save it
        object = Object(
                album=album,
                type='p',
                name=filedata['filename'],
            )
        object.save_original_file(filedata['filename'], filedata['content'])
    
        return HttpResponse('OK')
    def get_album_and_object(self,album_id, object_id):
        album = get_object_or_404(Album, pk=album_id)
        object = get_object_or_404(Object, pk=object_id)
        if object.album != album:
            raise Http404
        return album, object
    def album_object_set_preview(self,request, album_id, object_id):
        album, object = self.get_album_and_object(album_id, object_id)
        album.preview = object
        album.save()
        return HttpResponseRedirect('../../')
    def album_object_set_description(self,request, album_id, object_id):
        album, object = self.get_album_and_object(album_id, object_id)
        object.description = request.POST.get('description')
        object.save()
        return HttpResponseRedirect('../../')
    def album_object_delete(self,request, album_id, object_id):
        album, object = self.get_album_and_object(album_id, object_id)
        # Do not delete the whole album when deleting the preview object!
        if album.preview == object:
            album.preview = None
            album.save()
        object.delete()
        return HttpResponseRedirect('../../')

#admin.site.unregister(Album)
admin.site.register(Album, AlbumAdmin)
    
class ObjectAdmin( admin.ModelAdmin ):
    list_display = ['name', 'position']
    list_filter = ['album', ]
    
admin.site.register(Object, ObjectAdmin)  
  
class CommentAdmin(admin.ModelAdmin):
    list_display = ['object', 'name', 'email', 'ip', 'date']

admin.site.register(Comment, CommentAdmin)

#from django.conf.urls.defaults import *
#urlpatterns = patterns('',
 #                      (r'^admin/', include('gallery.admin_urls')),
  #                     )