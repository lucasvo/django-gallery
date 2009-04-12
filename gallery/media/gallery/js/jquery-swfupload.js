/// jQuery plugin to add support for SwfUpload
/// Derived from http://blog.codeville.net/2008/11/24/jquery-ajax-uploader-plugin-with-progress-bar/ (c) 2008 Steven Sanderson
/// (c) 2009 Lucas Vogelsang


(function($) {
    $.fn.makeSWFUploader = function(options) {
        return this.each(function() {
            var id = $(this).attr("id");        
            
            
            var swfu;
            var width = 109, height = 22;
            if (options) {
                width = options.width || width;
                height = options.height || height;
            }
            
            var defaults = {
                flash_url: '/media/gallery/SWFUpload/Flash/swfupload.swf',
                upload_url: "/upload",
                file_size_limit: "3 MB",
                file_types: "*.*",
                file_types_description: "All Files",
                debug: false,

            // Button Styling:
                button_image_url: "blankButton.png",
                button_width: width,
                button_height: height,
                button_placeholder_id: id,
                button_text: "<font face='Arial' size='13pt'>Choose file</span>",
                button_text_left_padding: (width - 70) / 2,
                button_text_top_padding: 1,                

            // Callbacks
				file_queued_handler : fileQueued,
				file_queue_error_handler : fileQueueError,
				file_dialog_complete_handler : fileDialogComplete,
				upload_start_handler : uploadStart,
				upload_progress_handler : uploadProgress,
				upload_error_handler : uploadError,
				upload_success_handler : uploadSuccess,
				upload_complete_handler : uploadComplete,
				queue_complete_handler : queueComplete,	// Queue plugin event
		    
		    // Custom Settings
		        custom_settings : {
					progressTarget : "upload-list",
					cancelButtonId : "btnCancel"
				},
            
            };
            swfu = new SWFUpload($.extend(defaults, options || {}));

        });
    }
})(jQuery);