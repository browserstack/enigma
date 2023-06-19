function remove_user_from_group(membership_id) {
  showRemoveMemberModal(membership_id)
}

function remove_user_from_user_confirmed(btnElem) {

  const membership_id = $(btnElem).attr("membership_id");
  url = "http://localhost:8000/group/removeGroupMember";
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
    },
    error: function(jqXHR, exception) {
    },
  });

  closeRemoveMemberModal();
}

function showRemoveMemberModal(membership_id) {
  $('#remove_member_modal').show();
  button_elem = document.getElementsByName("final-remove-button")[0];
  $(button_elem).attr("membership_id", membership_id);
}

function closeRemoveMemberModal() {
    $('#remove_member_modal').hide();
}

$(document).on("submit", "#updateOwners", function(e){
  e.preventDefault()

  let form = $(this)
  let actionUrl = form.attr('action');

  $.ajax({
    type: "POST",
    url: actionUrl,
    data: form.serialize(),
    error: (xhr, status, error) => {
      alert("Failed to Update Owners");
    }
  }).done(function(data, statusText, xhr){
    let status = xhr.status;
    if(status !== 200) {
      alert(data["error"] || "Failed to update Owners")
    }
    else {
      location.reload(true);
    }
  })
})

$(document).on('click', '.group-revoke-button', function(){
    id = $(this).attr("id");
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
          status_elem = $(`td[status_id='access-status-${id}']`);
          $(status_elem).html(`<span class="inline-flex text-gray-500">
                <svg xmlns="http://www.w3.org/2000/svg" height="18px" viewBox="0 0 24 24" width="18px" fill="#000000" class="h-6 w-6" stroke="currentColor"><path d="M14.59 8L12 10.59 9.41 8 8 9.41 10.59 12 8 14.59 9.41 16 12 13.41 14.59 16 16 14.59 13.41 12 16 9.41 14.59 8zM12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z"></path></svg>
                <span class="px-3 text-gray-700">Revoked</span>
            </span>`);
        },
        error: function(result){
          alert("Error occured while marking revoke! - "+result["responseJSON"]["error"])
        }});
  });
