function form_post(event, formId, action) {
  event.preventDefault();
  if (action == 'update'){
    create_post(formId)
  }
}

function create_post(formId) {
  modName = $('#' + formId + " input[name='modname']").val()
  error_message = "There was an error in updating User Identity for module " + modName + ". Please contact Admin"
  let actionUrl = $('#'+formId).attr('action');
  $.ajax({
      url : actionUrl, // the endpoint
      type : "POST", // http method
      data : $('#' + formId).serialize(),

      // handle a successful response
      success : function(json, textStatus, jqXHR) {
          var msg = jQuery.parseJSON(json);
          if (! msg.error){
            modName = $('#' + formId + " input[name='modname']").val()
            showNotification("failed", error_message)
          }
          else {
            modName = $('#' + formId + " input[name='modname']").val()
            showNotification("failed", error_message)
          }
      },

      // handle a non-successful response
      error : function(jqXHR, status, err) {
        errorObj = JSON.parse(jqXHR.responseJSON);
        modName = $('#' + formId + " input[name='modname']").val()
        showNotification("failed", error_message)
      }
  });
};
