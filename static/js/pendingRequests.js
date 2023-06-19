function showDeclineModal(request_id, action, messageId) {
  $('#decline_modal').show();
  $("#declineHeading").html("<p class='text-lg leading-6 font-medium'>"+request_id+"<p/>")
  $('#decline_modal').find("form").attr("onsubmit", `clickDeclineFinalButton('${request_id}', '${action}', '${messageId}');return false`)
}

function closeDeclineModal() {
  $("#declineReason").val('');
  $("#otherType").hide();
  $('#decline_modal').hide();
}

const clickDeclineFinalButton = (requestId, action, messageId) => {
  closeDeclineModal();
  const declineReason = $("#declineReasonText").val();
  const urlBuilder = `/decline/${action}/${requestId}`
  console.log(declineReason)
  console.log(urlBuilder)
  $.ajax({
    url: urlBuilder,
    data: {"reason": declineReason},
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      if(XMLHttpRequest.responseJSON) {
        showNotification("failed", XMLHttpRequest.responseJSON["response"][requestId]["error"])
      }
    }
  }).done(function (data) {
    updateStatus(false, messageId, requestId)
  })
}

function onChangeDeclineReason() {
  if($("#declineReason").val() === "customInput") {
    $("#otherType").show();
    $("#reason_box").prop('required',true);
  }
  else {
    $("#otherType").hide();
    $("#reason_box").prop('required',false);
    setDeclineReason($("#declineReason").val());
  }
}

function setDeclineReason(reason) {
  $("#declineReasonText").val(reason);
}

function updateStatus(type, id, requestId) {
  const newMessageBox = $("#message-box").clone(true, true);
  const item = $(`#${id}`);
  if(type) {
    newMessageBox.find('h3').html(`The request - ${requestId} is Approved`);
    newMessageBox.find('h3').addClass('text-green-800').removeClass('text-red-800');
    newMessageBox.addClass('bg-green-50').removeClass('bg-red-50');
    newMessageBox.find("svg#success").removeClass('hidden');
  } else {
    newMessageBox.find('h3').html(`The request - ${requestId} is Declined`);
    newMessageBox.find('h3').addClass('text-red-800').removeClass('text-green-800');
    newMessageBox.addClass('bg-red-50').removeClass('bg-green-50');
    newMessageBox.find("svg#failure").removeClass('hidden');
  }
  newMessageBox.appendTo(item);
  newMessageBox.show();
  $(`#${id}-actions`).hide();
}

function approveAccess(requestId, action, messageId) {
  const urlBuilder = `/accept_bulk/${action}?requestId=${encodeURIComponent(requestId)}`
  $.ajax({
    url: urlBuilder,
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      if(XMLHttpRequest.responseJSON) {
        showNotification("failed", XMLHttpRequest.responseJSON["response"][requestId]["error"])
      }
    }
  }).done(() => {
    updateStatus(true, messageId, requestId);
  })
}
