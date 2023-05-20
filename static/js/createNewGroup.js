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
      addMemberSelection(members[iter])
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

$(function () {
  $('#newGroupName').on('input', function () {
    var groupName = $(this).val();
    var groupNamePattern = /[A-Za-z0-9][A-Za-z0-9-]{2,}/;
    var error = document.getElementById("invalidGroupName")
    if (groupNamePattern.test(groupName)) {
      $(this).removeClass("border-red-500");
      error.classList.add("hidden");
    } else {
      $(this).addClass("border-red-500");
      error.classList.remove("hidden");
    }
  });
});

$(function () {
  $('#newGroupReason').on('input', function () {
    var groupReason = $(this).val();
    var groupReasonPattern = /.+/;
    var error = document.getElementById("invalidGroupReason")
    if (groupReasonPattern.test(groupReason)) {
      $(this).removeClass("border-red-500");
      error.classList.add("hidden");
    } else {
      $(this).addClass("border-red-500");
      error.classList.remove("hidden");
    }
  });
});

function showNotificiation(type, message, title) {
  if (type === "success") {
    $(".notification_success").removeClass("hidden")
    $(".notification_fail").addClass("hidden")
  }
  else if (type === "failed") {
    $(".notification_success").addClass("hidden")
    $(".notification_fail").removeClass("hidden")
  }
  $(".notification_message").html(message)
  $(".notification_title").html(title)
  $("#notification_bar").removeClass("hidden")
}

function showRequestSuccessMessage(message) {
  const successMessage = document.getElementById('request-success-message')
  successMessage.innerText = message;
  const modal = document.getElementById("request-submitted-modal");
  const modalOverlay = document.getElementById("modalOverlay");
  modal.classList.remove("hidden");
  modalOverlay.classList.remove("hidden");
}

function closeNotification() {
  $("#notification_bar").addClass("hidden")
}

function submitRequest() {
  const members = $('#member-selection-table').children('tr');
  const emails = [];
  var isValid = true;
  var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
  var newGroupNamePattern = /[A-Za-z0-9][A-Za-z0-9-]{2,}/;
  var newGroupReasonPattern = /.+/;
  var urlBuilder = "/group/create"


  for (iter = 0; iter < members.length; iter++) {
    emails.push($(members[iter]).attr("email"));
  }

  const selectedUserList = emails
  const newGroupName = $("#newGroupName").val();
  const newGroupReason = $("#newGroupReason").val();
  const requiresAccessApprove = $("#requiresAccessApprove").prop("checked");

  if (!newGroupNamePattern.test(newGroupName)) {
    var error = document.getElementById("invalidGroupName");
    var newGroup = document.getElementById("newGroupName");
    newGroup.classList.add("border-red-500");
    error.classList.remove("hidden");
    isValid = false;
  }

  if (!newGroupReasonPattern.test(newGroupReason)) {
    var error = document.getElementById("invalidGroupReason");
    var newGroup = document.getElementById("newGroupReason");
    newGroup.classList.add("border-red-500");
    error.classList.remove("hidden");
    isValid = false;
  }

  if (!isValid)
    return;
  else {
    $.ajax({
      url: urlBuilder,
      type: "POST",
      data: {
        newGroupName: newGroupName,
        newGroupReason: newGroupReason,
        requiresAccessApprove: requiresAccessApprove,
        selectedUserList: selectedUserList,
        csrfmiddlewaretoken: csrf_token
      },
      success: function (result) {
        showRequestSuccessMessage(result.status.msg)
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
            class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 focus:ring-blue-500 sm:left-6" ${ selectedList[user["email"]]? "checked": "" } onclick="handleMemberSelection(this.parentElement.parentElement)"></input>
        </td>
        <td id="description-td" class="whitespace-nowrap py-2 pr-3 text-sm font-normal ${ selectedList[user["email"]]? "text-blue-600" : "text-gray-900"}">
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
