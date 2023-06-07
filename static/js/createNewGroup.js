const selectedList = {}

const handleSelectionView = () => {
  const finalCount = $('#member-selection-table').children('tr').length;

  if (finalCount < 1) {
    $('#member-selection-empty').show();
    $('#member-selection-list').hide();
    $('#member-selection-list').children('nav').hide();
    $('#member-selected-count').hide();
  } else {
    $('#member-selection-empty').hide();
    $('#member-selection-list').show();
    $('#member-selection-list').children('nav').css('display', 'flex');
    $('#member-selected-count').show();
    $('#member-selected-count').text(finalCount + ' selected');
  }
};

const selectAllToggleSelection = (elem) => {
  if(elem.checked) {
    const members = $("#users-list-table").children('tr');
  
    for (iter = 0; iter < members.length; iter++) {
      if(!selectedList[$(members[iter]).attr("email")]){
        addMemberSelection(members[iter])
      }
    }
  } else {
    removeAllMembers()
  }

};

const selectMemberSelectionCheckbox = (elem, checked) => {
  if (checked) {
    $(elem).find('input').prop('checked', true);
    $(elem).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(elem).children('td#description-td').removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(elem).find('input').prop('checked', false);
    $(elem).children('td#description-td').addClass('text-gray-900').removeClass('text-blue-600');
    $(elem).addClass('hover:bg-blue-50 hover:text-blue-700').removeClass('bg-gray-50');
  }
};

const addMemberSelection = (elem) => {
  const selectionList = $('#member-selection-table');
  const newSpan = $("#member-selection-row-template").clone(true, true);
  selectMemberSelectionCheckbox(elem, true);
  const user_name = $(elem).attr("user_name");
  const email = $(elem).attr("email");

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = user_name;
  newSpan.attr("email", email)

  selectedList[email] = true;
  handleSelectionView();
};


const removeSelectionSpanElem = (rightElem, leftElem) => {

  rightElem.remove();
  selectMemberSelectionCheckbox(leftElem, false);

  selectedList[$(leftElem).attr("email") || $(rightElem).attr("email")] = false;
  handleSelectionView();
};

const removeMemberSelection = (elem) => {
  removeSelectionSpanElem($("#member-selection-table").find(`tr[email="${$(elem).attr('email')}"]`), elem);
};

const removeMemberSelectionUI = (elem) => {
  rightElem = elem.parentElement.parentElement;
  removeSelectionSpanElem(rightElem, $("#users-list-table").find(`tr[email="${$(rightElem).attr('email')}"]`));
};

const removeAllMembers = () => {
  const members = $('#member-selection-table').children('tr');
  for (iter = 0; iter < members.length; iter++) {
    removeSelectionSpanElem(members[iter], $("#users-list-table").find(`tr[email="${$(members[iter]).attr('email')}"]`));
  }
};

const handleMemberSelection = (elem) => {
  if (!$(elem).find('input').prop('checked')) {
    addMemberSelection(elem);
  } else {
    removeMemberSelection(elem);
  }
};

const handleMemberSelectionCheckbox = (elem) => {
  $(elem).prop('checked', !$(elem).prop('checked'));
}

const validateGroupName = (elem) => {
  const groupName = $(elem).val();
  const groupNamePattern = /[A-Za-z0-9][A-Za-z0-9-]{2,}/;
  const error = $("#invalidGroupName")
  if (groupNamePattern.test(groupName)) {
    $(elem).removeClass("border-red-500");
    error.addClass("hidden");
    return true;
  } else {
    $(elem).addClass("border-red-500");
    error.removeClass("hidden");
    return false;
  }
}

const validateGroupReason = (elem) => {
  const groupReason = $(elem).val();
  const groupReasonPattern = /.+/;
  const error = $("#invalidGroupReason")
  if (groupReasonPattern.test(groupReason)) {
    $(elem).removeClass("border-red-500");
    error.addClass("hidden");
    return true;
  } else {
    $(elem).addClass("border-red-500");
    error.removeClass("hidden");
    return false;
  }
}

// Implementation Pending
function showNotificiation(type, message, title) {

}

function showRedirectModal(title, message="") {
  $("#redirect_to_dashboard").show();
  $("#modal-title").html(title);
  $("#modal-message").html(message);
}

function closeNotification() {
  $("#notification_bar").addClass("hidden")
}

function submitRequest() {
  const members = $('#member-selection-table').children('tr');
  const emails = [];
  var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
  console.log(csrf_token)
  var urlBuilder = "/group/create"


  for (iter = 0; iter < members.length; iter++) {
    emails.push($(members[iter]).attr("email"));
  }

  const selectedUserList = emails
  const newGroupNameElem = $("#newGroupName");
  const newGroupReasonElem = $("#newGroupReason");
  const requiresAccessApprove = $("#requiresAccessApprove").prop("checked");

  if (!validateGroupName(newGroupNameElem) || !validateGroupReason(newGroupReasonElem)) {
    return;
  }
  else {
    $.ajax({
      url: urlBuilder,
      type: "POST",
      data: {
        "newGroupName": newGroupNameElem.val(),
        "newGroupReason": newGroupReasonElem.val(),
        "requiresAccessApprove": requiresAccessApprove,
        "selectedUserList": selectedUserList,
        "csrfmiddlewaretoken": csrf_token
      },
      success: function (result) {
        showRedirectModal("Request Submitted", result.status.msg)
      },
      error: function (XMLHttpRequest, textStatus, errorThrown) {
        const msg = JSON.parse(XMLHttpRequest.responseText).error.msg
        showNotificiation("failed", msg)
      }
    });
  }
}

function update_users(search, page) {
  $.ajax({
    url: "/api/v1/getActiveUsers",
    data: {"search": search, "page":page}
  }).done(function(data, statusText, xhr) {
    if(data["users"]) {
      const users = JSON.parse(data["users"]);
      $("#users-list-table tr").remove();

      const rows = users.map((user) => {
        return `<tr onclick="handleMemberSelection(this)" email="${user["email"]}" user_name="${user["first_name"]} ${user["last_name"]}" class="${selectedList[user["email"]]? "bg-gray-50": "hover:bg-blue-50 hover:text-blue-700"}">
        <td id="checkbox-td" class="relative w-12 px-6 sm:w-16 sm:px-8">
          <input type="checkbox" value="${user["email"]}"
            name="selectedUserList"
            class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 focus:ring-blue-500 sm:left-6" ${ selectedList[user["email"]]? "checked": "" } onclick="handleMemberSelectionCheckbox(this)"></input>
        </td>
        <td id="description-td" class="whitespace-nowrap py-4 pr-3 text-sm font-normal ${ selectedList[user["email"]]? "text-blue-600" : "text-gray-900"}">
          ${user["first_name"]} ${user["last_name"]} ${user["email"]}</td>
      </tr>`;
      })

      $("#users-list-table").append(rows.join(""));
      
      if(data["next_page"]) {
        $("#next_page").attr("onclick", `change_page('${data["next_page"]}')`);
      } else {
        $("#next_page").attr("onclick", `change_page('None')`);
      }

      if(data["previous_page"]) {
        $("#prev_page").attr("onclick", `change_page('${data["previous_page"]}')`);
      } else {
        $("#prev_page").attr("onclick", `change_page('None')`);
      }
    }
  })
}


function search(event, elem) {
  if(event.key === "Enter") {
    update_users($(elem).val(), undefined);
  }
}

function get_search_val() {
  return $("#global-search").val();
}

function change_page(page) {
  if(page !== 'None'){
    update_users(get_search_val(), Number(page));
  }
}

$(window).on("load", () => {
  update_users("", undefined)
})
