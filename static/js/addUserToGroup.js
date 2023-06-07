const userSelectedList = {};

const handleUserSelectionCheckbox = (elem) => {
  $(elem).prop('checked', !$(elem).prop('checked'));
}

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

const addUserSelection = (elem, defaultLength) => {
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
  handleSelectionView(defaultLength);
};

const removeSelectionSpanElem = (rightElem, leftElem, defaultLength) => {
  rightElem.remove();
  selectCheckbox(leftElem, false);

  userSelectedList[$(leftElem).attr("email") || $(rightElem).attr("email")] = false;
  handleSelectionView(defaultLength);
};

const removeUserSelection = (elem, defaultLength) => {
  $("#selectAllUsers").prop("checked", false);
  removeSelectionSpanElem($("#user-selection-table").find(`tr[email="${$(elem).attr('email')}"]`), elem, defaultLength);
};

const removeUserSelectionUI = (elem, defaultLength) => {
  rightElem = elem.parentElement.parentElement;
  $("#selectAllUsers").prop("checked", false);
  removeSelectionSpanElem(rightElem, $("#user-table").find(`tr[email="${$(rightElem).attr('email')}"]`), defaultLength);
  updateSelectedUser(defaultLength);
};

const removeAllUsers = (defaultLength) => {
  const users = $('#user-selection-table').children('tr');
  $("#selectAllUsers").prop("checked", false);
  for(iter = defaultLength; iter < users.length; iter++) {
    removeSelectionSpanElem(users[iter], $("#user-table").find(`tr[email="${$(users[iter]).attr('email')}"]`), defaultLength);
  }
  updateSelectedUser(defaultLength);
};

function updateSelectedUser(defaultLength) {
  const users_list = $('#user-selection-table').children('tr');
  const users_array = [];
  for(iter = defaultLength; iter < users_list.length; iter++) {
    users_array.push($(users_list[iter]).attr("email"));
  }

  $('#selected-users').val(users_array);
}

const selectAllUsers = (defaultLength) => {
  const users = $('#user-table').children('tr');
  for(iter = 0; iter < users.length; iter++) {
    if(!userSelectedList[$(users[iter]).attr('email')]) {
      addUserSelection(users[iter], defaultLength);
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

const handleUserSelection = (elem, defaultLength) => {
  if(!$(elem).find('input').prop('checked')) {
    addUserSelection(elem, defaultLength);
  } else {
    removeUserSelection(elem, defaultLength);
  }
  updateSelectedUser(defaultLength);
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
