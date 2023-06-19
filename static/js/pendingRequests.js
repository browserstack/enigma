function showDeclineModal(request_id) {
  $('#decline_modal').show();
  $(".declineHeading").html("<p class='text-lg leading-6 font-medium'>"+request_id+"<p/>")

}

function closeDeclineModal() {
  $('#decline_modal').hide();
}

const clickDeclineFinalButton = () => {
  closeDeclineModal();
  showNotificiation("failed", "Request Declined");
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
