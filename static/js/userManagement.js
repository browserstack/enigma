function closeModal(id) {
  $(`#${id}`).hide();
}

function showModal(id, elem) {
  $(`#${id}`).show();
  if(id === "offboard_member_modal") {
    const email = $(elem).attr("email");
    const description = `Are you sure you want to offboard ${email} member, this action can't be undone.`;
    $(`#${id}_description`).html(description);
    $(`#${id}_button`).attr("onclick", `startOffboarding('${email}', '${id}')`);
  }
  else {
    const request_id = $(elem).attr("requestId");
    $(`#${id}_button`).attr("onclick", `markRevoked('${request_id}', '${id}')`);
  }
}

function markRevoked(request_id, modal_id) {
  closeModal(modal_id);
  const actionUrl = `/access/markRevoked?requestId=${encodeURIComponent(request_id)}`;
  $.ajax({
    url: actionUrl,
    success: (data) => {
      const revoke_status_html = `<span class="inline-flex text-gray-500">
      <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 0 24 24" width="18px" fill="#000000" class="h-6 w-6" stroke="currentColor"><path d="M14.59 8L12 10.59 9.41 8 8 9.41 10.59 12 8 14.59 9.41 16 12 13.41 14.59 16 16 14.59 13.41 12 16 9.41 14.59 8zM12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"></path></svg>
          <span class="px-3 text-gray-700">Revoked</span>
      </span>`;

      $(`tr[requestId="${request_id}"]`).find("td#status").html(revoke_status_html);
      $(`tr[requestId="${request_id}"]`).find("td#mark_revoke").html('NA');
      showNotification("success", "Request revoked successfully");
    },
    error: (jqXHR) => {
      errorObj = jqXHR.responseJSON;
      if(errorObj && errorObj["error"]){
        showNotification("failed", errorObj["error"]);
      }
    }
  })
}

function exportToCSV() {
  const query_params = current_query_params();
  query_params["responseType"] = ["csv"];

  const actionUrl = create_url_from_query_params(query_params);
  window.open(actionUrl, '_blank');
}

function regrantAccess(request_id) {
  $.ajax({
    url: `/individual_resolve?requestId=${request_id}`,
    success: (data) => {
      showNotification("success", data["status_list"][0]["msg"], data["status_list"][0]["title"]);
    },
    error: (jqXHR) => {
      errorObj = jqXHR.responseJSON;
      if(errorObj) {
        showNotification("failed", errorObj["error"]["msg"], errorObj["error"]["error_msg"]);
      }
    }
  })
}


function startOffboarding(offboard_email, id) {
  closeModal(id);
  csrf_token = $("#csrf_token").val();
  $.ajax({
    url: "/user/offboardUser",
    type: "POST",
    data: { "offboard_email": offboard_email, 'csrfmiddlewaretoken': csrf_token },
    success: (data) => {
      if(data["message"]) {
        showNotification("success", data["message"]);
        user_row = $(`tr[email="${offboard_email}"]`).find(`td#status`);
        user_row.html("Offboarding");
        $(`tr[email="${offboard_email}"]`).find("td#action").html('NA');
      }
    },
    error: (jqXHR) => {
      errorObj = jqXHR.responseJSON;
      if(errorObj["error"]){
        showNotification("failed", errorObj["error"]);
      }
    }
  })
}
