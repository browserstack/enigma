let submitted_forms = 0

function submitRequest(event, elem, multi, access_tag, accesses="") {
  event.preventDefault()
  form = $(elem)
  let actionUrl = form.attr('action');
  $.ajax({
    type: "POST",
    url: actionUrl,
    data: form.serialize(),
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["msg"], xhr.responseJSON["error"]["error_msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong");
      }
    }
  }).done(function(data, statusText, xhr) {
    let status = xhr.status;

    if(status != 200) {
      showNotification("failed", data["error"]["error_msg"], data["error"]["msg"]);
    }
    else {
      if(multi) {
        showNotification("success", data["status"]["title"], data["status"]["msg"]);
        markedSubmitted(access_tag);
        submitted_forms += 1;

        if(submitted_forms == accesses) {
          showRedirectModal("All Requests submitted");
        }
      }
      else {
        showRedirectModal("Request submitted");
      }
    }
  })
}

function showRedirectModal(title, message="") {
  $("#redirect_to_dashboard").show();
  $("#modal-title").html(title);
  $("#modal-message").html(message);
}

function markedSubmitted(access_tag) {
  $(`#${access_tag}_dropdown`).prop("checked", false);
  $(`#${access_tag}_dropdown`).attr("disabled", true);
  $(`#${access_tag}_status`).removeClass("bg-gray-100").addClass("bg-emerald-100");
  $(`#${access_tag}_status`).removeClass("text-gray-800").addClass("text-emerald-800");
  $(`#${access_tag}_status`).html("Details submitted");
  rotateArrowOnCheck(access_tag);
}
