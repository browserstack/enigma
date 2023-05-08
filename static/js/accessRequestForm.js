function submitRequest(event, elem, multi, access_tag) {
  event.preventDefault()
  form = $(elem)
  let actionUrl = form.attr('action');
  $.ajax({
    type: "POST",
    url: actionUrl,
    data: form.serialize(),
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["error_msg"], xhr.responseJSON["error"]["msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong")
      }
    }
  }).done(function(data, statusText, xhr) {
    let status = xhr.status;

    if(status != 200) {
      showNotification("failed", data["error"]["error_msg"], data["error"]["msg"]);
    }
    else {
      showNotification("success", data["status"]["title"], data["status"]["msg"]);
      if(multi) {
        markedSubmitted(access_tag)
      }
    }
  })
}

function rotateArrowOnCheck(access_tag) {
  const checkbox = $(`#${access_tag}_arrow`)
  if(checkbox.hasClass("-rotate-90")) {
    checkbox.removeClass("-rotate-90")
  }
  else {
    checkbox.addClass("-rotate-90")
  }
}

function markedSubmitted(access_tag) {
  $(`#${access_tag}_dropdown`).prop("checked", false);
  $(`#${access_tag}_dropdown`).attr("disabled", true);
  $(`#${access_tag}_status`).removeClass("bg-gray-100").addClass("bg-emerald-100")
  $(`#${access_tag}_status`).removeClass("text-gray-800").addClass("text-emerald-800")
  $(`#${access_tag}_status`).html("Details submitted")
}

function showNotification(type, title, message) {
  // TODO
}
