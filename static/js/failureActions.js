function handleButtonLoading(elem, status) {
  let parentElem = $(elem.parentElement);
  let text = $(elem).html();
  let button = $(elem);
  if(status) {
    parentElem.find("button#resolveButton").attr('disabled', true);
    parentElem.find("button#declineButton").attr('disabled', true);
    parentElem.find("button#actionButton").attr('disabled', true);
    button.html("");
    let newSpan;
    if (text == "Resolve") {
      newSpan = $("#resolveButtonLoading").clone(true, true);
    } else {
      newSpan = $("#actionButtonLoading").clone(true, true);
    }
    newSpan.removeClass("collapse");
    newSpan.appendTo(button);
  } else {
    parentElem.find("button#resolveButton").attr('disabled', false);
    parentElem.find("button#declineButton").attr('disabled', false);
    parentElem.find("button#actionButton").attr('disabled', false);
    button.html(text);
  }
}

function sendAPICall(elem, requestId, url, messageId, desc) {
  url =`${url}?requestId=${requestId}`;
  handleButtonLoading(elem, true);
  $.ajax({
    url: url,
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["msg"], xhr.responseJSON["error"]["error_msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong");
      }
      handleButtonLoading(elem, false);
    }
  }).done((data) => {
    showNotification("success", data["status_list"][0]["title"], data["status_list"][0]["msg"]);
    updateStatus(desc, messageId, requestId);
    handleButtonLoading(elem, false);
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
