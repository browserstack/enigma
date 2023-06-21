function remove_user_from_group(membership_id) {
  showRemoveMemberModal(membership_id)
}

function remove_user_from_user_confirmed(membership_id) {
  url = "/group/removeGroupMember";
  var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
  $.ajax({
    url: url,
    type: "POST",
    data: { "membershipId": membership_id, 'csrfmiddlewaretoken': csrf_token},
    success: function(data) {
      $(`td[remove_user_button_id='${membership_id}-remove-user-button']`).html("");
      $(`td[user_state_id='${membership_id}-user-state']`).html("Revoked");
      checkbox_elem = $(`input[user_checkbox_id='${membership_id}-user-checkbox']`);

      $(checkbox_elem).prop("checked", false);
      $(checkbox_elem).prop("disabled", true);
      showNotification("success", "Request sent successfully!")
    },
    error: function(jqXHR, exception) {
      showNotification("failed", "Failed to send the request", "Something went wrong");
    },
  });

  closeRemoveMemberModal();
}

function showRemoveMemberModal(membership_id) {
  $('#remove_member_modal').show();
  $('#final-remove-button').attr("onclick", `remove_user_from_user_confirmed('${membership_id}')`)
}

function closeRemoveMemberModal() {
    $('#remove_member_modal').hide();
}

function updateOwners(elem, groupName) {
  let form = $(elem)
  let actionUrl = `/group/updateOwners/${groupName}`;

  $.ajax({
    type: "POST",
    url: actionUrl,
    data: form.serialize(),
    error: (xhr, status, error) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["msg"], xhr.responseJSON["error"]["error_msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong");
      }
    }
  }).done(function(data, statusText, xhr){
    let status = xhr.status;
    if(status !== 200) {
      showNotification("failed", data["error"]["error_msg"], data["error"]["msg"]);
    }
    else {
      location.reload(true);
    }
  })
}

function markRevoked(elem) {
    id = $(elem).attr("id");
    var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();

    urlBuilder = "/group/revokeAccess"
    $.ajax({url: urlBuilder,
        method: "POST",
        data: {
          request_id: id,
          csrfmiddlewaretoken: csrf_token
        },
        success: function(result){
          revoke_button_elem = $(`td[revoke_button_id='inactive-${id}-revoke-button']`).find("button");
          $(revoke_button_elem).hide();
          statuses = $(`td[status_id='access-status-${id}']`).children();
          $(statuses[0]).hide();
          $(statuses[1]).show();
        },
        error: function(result){
          showNotification("failed", "Error occurred while marking revoke! - " + result["responseJSON"]["message"], "error");
        }});
  };
