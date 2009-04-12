if (add != true) {
$(function() {
    $("#spanButtonPlaceholder").makeSWFUploader({
        upload_url: "/admin/gallery/album/{{ album.id }}/upload/?ssid="+sessionid, 
        file_size_limit : "10 MB",
        file_types : "*.jpg; *.jpeg; *.png; *.tif; *.gif",
		file_types_description : file_types_description,
		file_upload_limit : 1000,
		file_queue_limit : 100,
           
        button_placeholder_id : "spanButtonPlaceholder",
        button_width: 69,
        button_height: 30,
		button_text: '',
		button_window_mode: SWFUpload.WINDOW_MODE.TRANSPARENT,
		button_cursor: SWFUpload.CURSOR.HAND,    
        
		custom_settings : {
			progressTarget : "upload-list",
			cancelButtonId : "btnCancel"
			},
				
		minimum_flash_version : "9.0.28",
		
		debug:false,
//		debug_handler: debug_console,

        });
});  
}

function load_sortable () {
// This function checks whether manual ordering is selected and enables/disables sorting.
if ($("#id_ordering").val() == "m") {
        // Make the object list sortable
        $("#objectlist").sortable({
            stop: function(i) {
                $.ajax({
                    type: "POST",
                    url: '/admin/gallery/album/'+album_id+'/reorder/',
                    data: $("#objectlist").sortable("serialize")
                });
          },
        });      
}
}

function reload_imgs() {
    $("#objectlist").load('/admin/gallery/album/'+album_id+'/objectlist/', function () {
    
	    // Initialize Thickbox
	    tb_init('a.thickbox, area.thickbox, input.thickbox');    
	    $(".TB_closeWindowButton").click(tb_remove);
	    
	    // Enable the Toolbar for the images
        $(".album_object").hover(
            function () {
                $(this).children(".toolbar").css("display", "block");
            }, 
            function () {
                $(this).children(".toolbar").css("display", "none");
            });
        $(".delete-link").click(function () {
            if(confirm(delete_confirm_msg)) {
                return true;
            } else {
                return false;
            }
            });
        $(".submit_object_infos").click(function () {
            id = $(this).parents(".object_info_form").attr("id").split("_", 1)[0];
            url = '/admin/gallery/album/'+album_id+'/'+id+'/';
            post = {
                name :      $("#id_object_"+id+"_name").val(),
                caption :   $("#id_object_"+id+"_caption").val(),
                preview :   $("#id_object_"+id+"_preview").val(),
                }
                
            console.log($("#id_object_"+id+"_preview").val());
            $.post(url, post, tb_remove, "html");
            return false;
        });
        load_sortable();
    });    
}

var tb_remove_callback = function () {
reload_imgs();
$("#upload-list").empty();
};

$(document).ready(function () {
    if (add != true) { reload_imgs(); }   
});
