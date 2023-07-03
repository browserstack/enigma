var selectedList = {}
var disabled = false
const SELECTION_LIMIT = 20

const handleSelectionView = () => {
  let finalCount = $('#member-selection-table').children('tr').length;
  if(disabled) {
    finalCount = 'All';
  }

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
    removeAllMembers(true);
    const selectionList = $('#member-selection-table');
    const newSpan = $("#member-selection-row-template").clone(true, true);
    newSpan.appendTo(selectionList);
    newSpan.show();
    const tableData = newSpan.children('td');
    tableData[0].textContent = "All User Selected";
    newSpan.attr("selectAll", true);
    handleSelectionView();
  } else {
    removeAllMembers(false);
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

const handleDisableMode = () => {
  selectedList = {};
  const users = $('#users-list-table').children('tr');
  for (iter = 0; iter < users.length; iter++) {
    if (disabled) {
      $(users[iter]).find('input').prop('checked', true);
      $(users[iter]).removeAttr("onclick");
      $(users[iter]).find('input').attr("disabled", true);
      $(users[iter]).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
      $(users[iter]).children('td#description-td').removeClass('text-gray-900').addClass('text-blue-600');
    } else {
      $(users[iter]).attr("onclick", "handleMemberSelection(this)");
      $(users[iter]).find('input').attr("disabled", false);
      $(users[iter]).find('input').prop('checked', false);
      $(users[iter]).children('td#description-td').addClass('text-gray-900').removeClass('text-blue-600');
      $(users[iter]).addClass('hover:bg-blue-50 hover:text-blue-700').removeClass('bg-gray-50');
    }
  }
}

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
  if($(rightElem).attr("selectAll")){
    $("#selectAllUsers").prop("checked", false);
    disabled = false;
    handleDisableMode();
    $(rightElem).remove();
    handleSelectionView();
  } else {
    removeSelectionSpanElem(rightElem, $("#users-list-table").find(`tr[email="${$(rightElem).attr('email')}"]`));
  }
  $('#max-member-selected-warning').hide();
};

const removeAllMembers = (disabledState) => {
  disabled = disabledState; 
  const members = $('#member-selection-table').children('tr');
  for (iter = 0; iter < members.length; iter++) {
    if($(members[iter]).attr('selectAll')){
      $("#selectAllUsers").prop("checked", false);
      $(members[iter]).remove();
    } else {
      removeSelectionSpanElem(members[iter], $("#users-list-table").find(`tr[email="${$(members[iter]).attr('email')}"]`));
    }
  }
  handleDisableMode();
  handleSelectionView();
  $('#max-member-selected-warning').hide();
};

const findSelectedListLength = () => {
  let count = 0;
  Object.values(selectedList).forEach(val => {
    if(val) count++;
  })
  return count;
}

const handleMemberSelection = (elem) => {
  if(disabled) return;
  if (!$(elem).find('input').prop('checked')) {
    if(findSelectedListLength() === SELECTION_LIMIT) {
      $('#max-member-selected-warning').show();
      return;
    }
    addMemberSelection(elem);
  } else {
    removeMemberSelection(elem);
  }
  if(findSelectedListLength() === SELECTION_LIMIT) {
    $('#max-member-selected-warning').show();
  } else {
    $('#max-member-selected-warning').hide();
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

function showRedirectModal(title, message="") {
  $("#redirect_to_dashboard").show();
  $("#modal-title").html(title);
  $("#modal-message").html(message);
}

function handleButtonLoading(elem, status) {
  if(status) {
    elem.attr('disabled', true);
    elem.html("");
    let newSpan = $("#submitButtonLoading").clone(true, true);
    newSpan.removeClass("collapse");
    newSpan.appendTo(elem);
  } else {
    elem.attr('disabled', false);
    elem.html("Submit request");
  }
}

function submitRequest() {
  const members = $('#member-selection-table').children('tr');
  const emails = [];
  var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
  var urlBuilder = "/group/create"


  for (iter = 0; iter < members.length; iter++) {
    emails.push($(members[iter]).attr("email"));
  }

  const selectedUserList = emails
  const newGroupNameElem = $("#newGroupName");
  const newGroupReasonElem = $("#newGroupReason");
  const requiresAccessApprove = $("#requiresAccessApprove").prop("checked");
  const selectAllUsers = $("#selectAllUsers").prop("checked");

  if (!validateGroupName(newGroupNameElem) || !validateGroupReason(newGroupReasonElem)) {
    $(window).scrollTop(0)
    return;
  }
  else {
    let button = $('#submitNewGroup');
    handleButtonLoading(button, true);
    $.ajax({
      url: urlBuilder,
      type: "POST",
      data: {
        "newGroupName": newGroupNameElem.val(),
        "newGroupReason": newGroupReasonElem.val(),
        "requiresAccessApprove": requiresAccessApprove,
        "selectedUserList": selectedUserList,
        "csrfmiddlewaretoken": csrf_token,
        "selectAllUsers": selectAllUsers,
      },
      success: function (result) {
        showRedirectModal("Request Submitted", result.status.msg);
        handleButtonLoading(button, false);
      },
      error: function (XMLHttpRequest, textStatus, errorThrown) {
        if(XMLHttpRequest.responseJSON) {
          response = XMLHttpRequest.responseJSON.error
          showNotification("failed", response["msg"], response["error_msg"])
        } else {
          showNotification("failed", "Something when wrong while creating the group, contact admin.", "Internal Error")
        }
        handleButtonLoading(button, false);
      }
    });
  }
}

function update_users(search, page) {
  $.ajax({
    url: "/api/v1/getActiveUsers",
    data: {"search": search, "page":page},
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      if(XMLHttpRequest.responseJSON) {
        const msg = XMLHttpRequest.responseJSON;
        showNotificiation("failed", msg["error"], "Internal Error");
      }
    }
  }).done(function(data, statusText, xhr) {
    if(data["users"]) {
      const users = data["users"];
      $("#users-list-table tr").remove();

      const rows = users.map((user) => {
        return `<tr onclick="handleMemberSelection(this)" email="${user["email"]}" user_name="${user["first_name"]} ${user["last_name"]}" class="${(selectedList[user["email"]] || disabled)? "bg-gray-50": "hover:bg-blue-50 hover:text-blue-700"}">
        <td id="checkbox-td" class="relative w-12 px-6 sm:w-16 sm:px-8">
          <input type="checkbox" value="${user["email"]}"
            name="selectedUserList"
            class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 focus:ring-blue-500 sm:left-6" ${ (selectedList[user["email"]] || disabled)? "checked": "" } onclick="handleMemberSelectionCheckbox(this)" ${(disabled) ? "disabled" : ""}></input>
        </td>
        <td id="description-td" class="whitespace-nowrap py-4 pr-3 text-sm font-normal ${ (selectedList[user["email"]] || disabled)? "text-blue-600" : "text-gray-900"}">
          ${user["first_name"]} ${user["last_name"]} ${user["email"]}</td>
      </tr>`;
      })

      $("#users-list-table").append(rows.join(""));

      if(data["next_page"]) {
        $("#user-list-nav").removeClass("hidden");
        $("#next_page").attr("onclick", `change_page('${data["next_page"]}')`);
      } else {
        $("#user-list-nav").removeClass("hidden");
        $("#next_page").attr("onclick", `change_page('None')`);
      }

      if(data["prev_page"]) {
        $("#user-list-nav").removeClass("hidden");
        $("#prev_page").attr("onclick", `change_page('${data["prev_page"]}')`);
      } else {
        $("#user-list-nav").removeClass("hidden");
        $("#prev_page").attr("onclick", `change_page('None')`);
      }

      if(!data["next_page"] && ! data["prev_page"]) {
        $("#user-list-nav").addClass("hidden")
      }
      $("#user-scroll-bar").scrollTop(0)
      if(data["search_error"]) {
        alert(data["search_error"])
        showNotificiation(data["search_error"])
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
