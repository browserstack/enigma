function showDeclineModal(request_id, action, messageId) {
  $('#decline_modal').show();
  $("#declineHeading").html("<p class='text-lg leading-6 font-medium'>"+request_id+"<p/>")
  $('#decline_modal').find("form").attr("onsubmit", `clickDeclineFinalButton(this, '${request_id}', '${action}', '${messageId}');return false`)
}

function closeDeclineModal() {
  $("#declineReason").val('');
  $("#otherType").hide();
  $('#decline_modal').hide();
}

const clickDeclineFinalButton = (elem, requestId, action, messageId) => {
  closeDeclineModal();
  const declineReason = $("#declineReasonText").val();
  const urlBuilder = `/decline/${action}/${requestId}`;
  let button = $(elem);
  handleButtonLoading(button, true);
  $.ajax({
    url: urlBuilder,
    data: {"reason": declineReason},
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      if(XMLHttpRequest.responseJSON) {
        showNotification("failed", XMLHttpRequest.responseJSON["response"][requestId]["error"]);
      }
      handleButtonLoading(button, true, "Decline");
    }
  }).done(function (data) {
    updateStatus(false, messageId, requestId);
    handleButtonLoading(button, true, "Decline");
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

function handleButtonLoading(elem, status, text=null) {
  if(status) {
    elem.attr('disabled', true);
    elem.html("");
    let svgElem = $("#buttonLoading").clone(true, true);
    svgElem.removeClass("collapse");
    svgElem.appendTo(elem);
  } else {
    elem.attr('disabled', false);
    elem.html(text);
  }
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

function approveAccess(elem, requestId, action, messageId) {
  const urlBuilder = `/accept_bulk/${action}?requestId=${encodeURIComponent(requestId)}`
  let button = $(elem);
  handleButtonLoading(button, true);
  $(elem.parentElement).find("button#declineButton").attr('disabled', true);
  $.ajax({
    url: urlBuilder,
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      if(XMLHttpRequest.responseJSON) {
        showNotification("failed", XMLHttpRequest.responseJSON["response"][requestId]["error"])
      }
      handleButtonLoading(button, false, "Accept");
      $(elem.parentElement).find("button#declineButton").attr('disabled', false);
    }
  }).done(() => {
    updateStatus(true, messageId, requestId);
    handleButtonLoading(button, false, "Accept");
    $(elem.parentElement).find("button#declineButton").attr('disabled', false);
  })
}
