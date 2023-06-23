function closeNotification() {
  $("#notification_bar").hide()
}

function showNotification(type, message, title=undefined) {
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

function rotateArrowOnCheck(access_tag) {
  const checkbox = $(`#${access_tag}_arrow`);
  if(checkbox.hasClass("-rotate-90")) {
    checkbox.removeClass("-rotate-90");
  }
  else {
    checkbox.addClass("-rotate-90");
  }
}
