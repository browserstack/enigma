function closeNotification() {
  console.log("Hide notification")
  $("#notification_bar").hide()
}

function showNotification(type, message, title=undefined) {
  console.log("Show Notification")
  if(type === "success"){
    $("#notification_success").show();
    $("#notification_fail").hide();
  }
  else if(type === "failed") {
    $("#notification_success").hide();
    $("#notification_fail").show();
  }
  $("#notification_message").html(message);
  $("#notification_title").html(title);
  $("#notification_bar").show();
}


function showTooltip(id) {
  $(`#${id}`).removeClass("hidden");
}
function hideTooltip(id) {
  $(`#${id}`).addClass("hidden");
}
