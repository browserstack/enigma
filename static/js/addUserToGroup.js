var userSelectedList = {};
var disabled = false;

const handleUserSelectionCheckbox = (elem) => {
  $(elem).prop('checked', !$(elem).prop('checked'));
}

const handleSelectionView = () => {

  let finalCount = $('#user-selection-table').children('tr').length
  if(disabled) {
    finalCount = "All";
  }

  if(finalCount < 1) {
    $('#user-selection-list').children('nav').hide();
    $('#user-selected-count').hide();
  } else {
    $('#user-selection-list').children('nav').css('display', 'flex');
    $('#user-selected-count').show();
    $('#user-selected-count').text(finalCount + ' new selected');
  }
};

const selectCheckbox = (elem, checked) => {
  if(checked) {
    $(elem).find('input').prop('checked', true);
    $(elem).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(elem).children('td#adduser-description-td').removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(elem).find('input').prop('checked', false);
    $(elem).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(elem).children('td#adduser-description-td').removeClass('text-blue-600').addClass('text-gray-900');
  }
};

const addUserSelection = (elem) => {
  const selectionList = $('#user-selection-table');
  const newSpan = $("#user-selection-row-template").clone(true, true);

  selectCheckbox(elem, true);
  const email = $(elem).attr("email");

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = email;
  newSpan.attr('email', email);

  userSelectedList[email] = true;
  handleSelectionView();
};

const removeSelectionSpanElem = (rightElem, leftElem) => {
  rightElem.remove();
  selectCheckbox(leftElem, false);

  userSelectedList[$(leftElem).attr("email") || $(rightElem).attr("email")] = false;
  handleSelectionView();
};

const removeUserSelection = (elem) => {
  $("#selectAllUsers").prop("checked", false);
  removeSelectionSpanElem($("#user-selection-table").find(`tr[email="${$(elem).attr('email')}"]`), elem);
};

const removeUserSelectionUI = (elem) => {
  rightElem = elem.parentElement.parentElement;
  if($(rightElem).attr("selectAll")) {
    $("#selectAllUsers").prop("checked", false);
    disabled = false;
    handleDisableMode();
    $(rightElem).remove();
    handleSelectionView();
  } else {
    removeSelectionSpanElem(rightElem, $("#user-table").find(`tr[email="${$(rightElem).attr('email')}"]`));
  }
};

const removeAllUsers = (disabledState) => {
  disabled = disabledState;
  const users = $('#user-selection-table').children('tr');
  for(iter = 0; iter < users.length; iter++) {
    if ($(users[iter]).attr('selectAll')) {
      $("#selectAllUsers").prop("checked", false);
      $(users[iter]).remove();
    } else {
      removeSelectionSpanElem(users[iter], $("#user-table").find(`tr[email="${$(users[iter]).attr('email')}"]`));
    }
  }
  handleDisableMode();
  handleSelectionView();
};

function updateSelectedUser() {
  const users_list = $('#user-selection-table').children('tr');
  const users_array = [];
  for(iter = 0; iter < users_list.length; iter++) {
    users_array.push($(users_list[iter]).attr("email"));
  }

  $('#selected-users').val(JSON.stringify(users_array));
}

const selectAllUsers = () => {
  removeAllUsers(true);
  const selectionList = $('#user-selection-table');
  const newSpan = $("#user-selection-row-template").clone(true, true);
  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = "All User Selected";
  newSpan.attr("selectAll", true);
  handleSelectionView();
}

const selectAllUserToggle = (elem) => {
  if(elem.checked) {
    selectAllUsers();
  } else {
    removeAllUsers(false);
  }
}

const handleUserSelection = (elem) => {
  if(disabled) return;
  if(!$(elem).find('input').prop('checked')) {
    addUserSelection(elem);
  } else {
    removeUserSelection(elem);
  }
  updateSelectedUser();
};

const handleDisableMode = () => {
  selectedList = {};
  const users = $('#user-table').children('tr');
  for (iter = 0; iter < users.length; iter++) {
    if (disabled) {
      $(users[iter]).find('input').prop('checked', true);
      $(users[iter]).removeAttr("onclick");
      $(users[iter]).find('input').attr("disabled", true);
      $(users[iter]).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
      $(users[iter]).children('td#description-td').removeClass('text-gray-900').addClass('text-blue-600');
    } else {
      $(users[iter]).attr("onclick", "handleUserSelection(this)");
      $(users[iter]).find('input').attr("disabled", false);
      $(users[iter]).find('input').prop('checked', false);
      $(users[iter]).children('td#description-td').addClass('text-gray-900').removeClass('text-blue-600');
      $(users[iter]).addClass('hover:bg-blue-50 hover:text-blue-700').removeClass('bg-gray-50');
    }
  }
}

function submitRequest(event, elem) {
  event.preventDefault();
  form = $(elem);
  let actionUrl = form.attr('action');
  const selectAllUsers = $("#selectAllUsers").prop("checked");
  requestData = form.serialize() + "&selectAllUsers=" + selectAllUsers;
  $.ajax({
    type: "POST",
    url: actionUrl,
    data: requestData,
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["msg"], xhr.responseJSON["error"]["error_msg"]);
      }
      else {
        showNotification("failed", "Failed to send the request", "Something went wrong");
      }
    }
  }).done(function(data, statusText, xhr) {
    let status = xhr.status;
    if(status != 200) {
      showNotification("failed", data["error"]["error_msg"], data["error"]["msg"]);
    }
    else {
      showRedirectModal("Request submitted");
    }
  })
};

function showRedirectModal(title, message="") {
  $("#redirect_to_dashboard").show();
  $("#modal-title").html(title);
  $("#modal-message").html(message);
};


function update_users(search, page, groupName) {
  $.ajax({
    url: "/api/v1/getActiveUsers",
    data: {"search": search, "page":page, "groupName":groupName},
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      const msg = XMLHttpRequest.responseJSON;
      showNotificiation("failed", msg["error"]);
    }
  }).done(function(data, statusText, xhr) {
    if(data["users"]) {
      const users = data["users"];
      $("#user-table tr").remove();

      const rows = users.map((user) => {
        return `<tr onclick="handleUserSelection(this)" email="${user["email"]}" user_name="${user["first_name"]} ${user["last_name"]}" class="${(userSelectedList[user["email"]] || disabled)? "bg-gray-50": "hover:bg-blue-50 hover:text-blue-700"}">
        <td class="relative w-12 px-6 sm:w-16 sm:px-8">
          <input type="checkbox" id="adduser-checkbox-td" value="${user["email"]}"
            class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 focus:ring-blue-500 sm:left-6" ${ (userSelectedList[user["email"]] || disabled)? "checked": "" } onclick="handleUserSelectionCheckbox(this)" ${(disabled) ? "disabled" : ""}></input>
        </td>
        <td id="adduser-description-td" class="whitespace-nowrap py-4 pr-3 text-sm font-normal ${ (userSelectedList[user["email"]] || disabled)? "text-blue-600" : "text-gray-900"}">
          ${user["first_name"]} ${user["last_name"]} ${user["email"]}</td>
      </tr>`;
      })

      $("#user-table").append(rows.join(""));

      if(data["next_page"]) {
        $("#user-list-nav").removeClass("hidden");
        $("#next_page").attr("onclick", `change_page('${data["next_page"]}', '${groupName}')`);
      } else {
        $("#user-list-nav").removeClass("hidden");
        $("#next_page").attr("onclick", `change_page('None', '${groupName}')`);
      }

      if(data["prev_page"]) {
        $("#user-list-nav").removeClass("hidden");
        $("#prev_page").attr("onclick", `change_page('${data["prev_page"]}', '${groupName}')`);
      } else {
        $("#user-list-nav").removeClass("hidden");
        $("#prev_page").attr("onclick", `change_page('None', '${groupName}')`);
      }

      if(!data["next_page"] && ! data["prev_page"]) {
        $("#user-list-nav").addClass("hidden")
      }
      $("#user-scroll-bar").scrollTop(0)
      if(data["search_error"]) {
        showNotificiation("failed", data["search_error"], "Search Error")
      }
    }
  })
}

function addUserSearch(event, elem, groupName) {
  if(event.key === "Enter") {
    update_users($(elem).val(), undefined, groupName);
  }
}

function get_search_val() {
  return $("#global-search").val();
}

function change_page(page, groupName) {
  if(page !== 'None'){
    update_users(get_search_val(), Number(page), groupName);
  }
}

$(window).on("load", () => {
  const groupName = $("#groupNameHeading").attr("groupName");
  update_users("", undefined, groupName);
})
