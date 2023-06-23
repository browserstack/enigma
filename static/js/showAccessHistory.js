var currentStatusFilterState = 'hidden';

function showGroupModal(group_name) {
  $('#group_modal').show();
  $('#' + group_name).attr("selected",true);
}

function closeGroupModal() {
    $('#group_modal').hide();
}

function showMemberModal(group_name) {
    $('#member_modal').show();
    $('#grpname-' + group_name).attr("selected",true);
}

function closeMemberModal() {
    $('#member_modal').hide();
}

function clickAddmemberFinalButton() {
    const grp_name = $('#memberGroupName').val()
    const finalUrl = `/group/adduser/${grp_name}`;
    window.location = finalUrl;
}

const focusFilterStatus = (elem) => {
  const ulElem = $(elem).children('ul');
  if(currentStatusFilterState == 'hidden') {
    currentStatusFilterState = 'shown';
    ulElem.show();
  } else {
    const shownElem = $(".dropdown-search-collapse").children('ul');
    shownElem.hide();

    currentStatusFilterState = 'hidden';
    ulElem.hide();
  }
};

$(document).on("click", function (e) {
  var container = $(".dropdown-search-collapse");

  if (container.has(e.target).length === 0) {
    const ulElem = $(".dropdown-search-collapse").children('ul');
    if(currentStatusFilterState == 'shown') {
      currentStatusFilterState = 'hidden';
      ulElem.hide();
    }
  }
})


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
