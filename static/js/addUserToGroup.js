const handleSelectionView = (defaultLength) => {

  let finalCount = $('#user-selection-table').children('tr').length - defaultLength

  if(finalCount < 1) {
    $('#user-selection-list').children('nav').hide();
    $('#user-selected-count').hide();
  } else {
    $('#user-selection-list').children('nav').css('display', 'flex');
    $('#user-selected-count').show();
    $('#user-selected-count').text(finalCount + ' new selected');
  }
};

const selectCheckbox = (userTag, checked) => {
  if(checked) {
    $(`#${userTag}-marker`).show();
    $(`#${userTag}-checkbox`).prop('checked', true);
    $(`#${userTag}-tablerow`).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(`#${userTag}-tabledesc`).removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(`#${userTag}-marker`).hide();
    $(`#${userTag}-checkbox`).prop('checked', false);
    $(`#${userTag}-tablerow`).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(`#${userTag}-tabledesc`).removeClass('text-blue-600').addClass('text-gray-900');
  }
};

const addUserSelection = (userTag, userDesc, defaultLength) => {
  const selectionList = $('#user-selection-table');
  const newSpan = $("#user-selection-row-template").clone(true, true);

  selectCheckbox(userTag, true);

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = userDesc;
  newSpan.attr('id', `user-selection-${userTag}`);

  handleSelectionView(defaultLength);
};

const removeSelectionSpanElem = (elem, defaultLength) => {
  const spanId = elem.id || elem.attr('id');
  const userTag = spanId.replace('user-selection-', '');

  elem.remove();
  selectCheckbox(userTag, false);

  handleSelectionView(defaultLength);
};

const removeUserSelection = (userTag, defaultLength) => {
  removeSelectionSpanElem($(`#user-selection-${userTag}`),defaultLength);
};

const removeUserSelectionUI = (elem, defaultLength) => {
  removeSelectionSpanElem(elem.parentElement.parentElement, defaultLength);
};

const removeAllUsers = (defaultLength) => {
  const modules = $('#user-selection-table').children('tr');
  for(iter = defaultLength; iter < modules.length; iter++) {
    removeSelectionSpanElem(modules[iter]);
  }

  handleSelectionView(defaultLength);
};

function updateSelectedUser(defaultLength) {
  const users_list = $('#user-selection-table').children('tr');
  const users_array = [];
  for(iter = defaultLength; iter < users_list.length; iter++) {
    users_array.push(`${users_list[iter].cells[0].innerHTML}`);
  }

  $('#selected-users').val(users_array);
}

const selectAllUsers = (defaultLength) => {
  const users = $('#user-table').children('tr');
  for(iter = 0; iter < users.length; iter++) {
    const user = users[iter].id.split('-tablerow')[0];
    if(!$(`#${user}-checkbox`).prop('checked')) {
      addUserSelection(users[iter].id.split('-tablerow')[0], users[iter].cells[1].innerHTML, defaultLength);
    }
  }
  updateSelectedUser(defaultLength);
}

const selectAllUserToggle = (elem, defaultLength) => {
  if(elem.checked) {
    selectAllUsers(defaultLength);
  } else {
    removeAllUsers(defaultLength);
  }
}

const handleUserSelection = (elem, userTag, userDesc, defaultLength) => {
  if(elem.checked) {
    addUserSelection(userTag, userDesc, defaultLength);
  } else {
    removeUserSelection(userTag, defaultLength);
  }
  updateSelectedUser(defaultLength)
};

function submitRequest(event, elem) {
  event.preventDefault();
  form = $(elem);
  let actionUrl = form.attr('action');
  $.ajax({
    type: "POST",
    url: actionUrl,
    data: form.serialize(),
    error: (xhr, statusText, data) => {
      if(xhr.responseJSON) {
        showNotification("failed", xhr.responseJSON["error"]["error_msg"], xhr.responseJSON["error"]["msg"]);
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

function showNotification(type, title, message) {
  // TODO
};
