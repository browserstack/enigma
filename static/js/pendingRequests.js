function closeNotification(){
  $("#notification_bar").addClass("hidden")
}

function showDeclineModal() {
  $('#decline_modal').removeClass("hidden")
}

const clickDeclineFinalButton =  () => {
  $('#decline_modal').addClass("hidden")
  showNotificiation("failed", "Request Declined");
}

function showNotificiation(type, message) {
  if(type === "success"){
    $(".notification_success").removeClass("hidden")
    $(".notification_fail").addClass("hidden")
    console.log("success")
  }
  else if(type === "failed") {
    $(".notification_success").addClass("hidden")
    $(".notification_fail").removeClass("hidden")
  }
  $(".notification_message").html(message)
  $("#notification_bar").removeClass("hidden")
}
