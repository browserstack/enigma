function sendAPICall(requestId, url, messageId, desc) {
  url =`${url}?requestId=${requestId}`
  $.ajax({
    url: url,
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["msg"], xhr.responseJSON["error"]["error_msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong");
      }
    }
  }).done((data) => {
    showNotification("success", data["status_list"][0]["title"], data["status_list"][0]["msg"]);
    updateStatus(desc, messageId, requestId)
  })
}


function updateStatus(desc, id, requestId) {
  const newMessageBox = $("#message-box").clone(true, true);
  const item = $(`#${id}`);
  newMessageBox.find('h3').html(`The request - ${requestId} is ${desc}`);
  newMessageBox.find('h3').addClass('text-green-800').removeClass('text-red-800');
  newMessageBox.addClass('bg-green-50').removeClass('bg-red-50');
  newMessageBox.find("svg#success").removeClass('hidden');
  newMessageBox.appendTo(item);
  newMessageBox.show();
  $(`#${id}-actions`).hide();
}
