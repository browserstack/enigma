$(document).ready(function () {
  var users = ($("#createGroup_list_email").data('my-data'));
  var requestUser = $('#createGroup_list_email').data('request');

  for (let user of users) {
    user = user.fields
    if (requestUser.email != user.email && user.state == '1' && user.email) {
      var row = $('<tr>').attr('id', user.user + '-tablerow').addClass('hover:bg-blue-50 hover:text-blue-700');
      var checkboxCol = $('<td>').addClass('relative w-12 px-6 sm:w-16 sm:px-8');
      var checkbox = $('<input>').attr({
        'type': 'checkbox',
        'value': user.email,
        'username': user.user,
        'firstName': user.name,
        'lastName': '',
        'name': 'selectedUserList',
        'class': 'absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 sm:left-6',
        'id': user.user + '-checkbox'
      }).click(function () {
        handleMemberSelection({
          elem: this,
          username: user.user,
          firstName: user.name,
          lastName: '',
          email: user.email
        });
      });
      var marker = $('<div>').addClass('absolute inset-y-0 left-0 w-0.5 hidden').attr('id', user.user + '-marker');
      checkboxCol.append(marker).append(checkbox);
      var descCol = $('<td>').addClass('whitespace-nowrap py-4 pr-3 text-sm font-medium text-gray-900').attr('id', user.user + '-tabledesc').attr('value', user.username).text(user.name + ' ' + ' ' + user.email);
      row.append(checkboxCol).append(descCol);
      $('#createGroup_list_email').append(row);
    }
  }


})

$(document).ready(function () {
  function filterTableRows(query) {
    $('#createGroup_list_email tr').each(function () {
      if ($(this).text().toLowerCase().includes(query.toLowerCase())) {
        $(this).show();
      } else {
        $(this).hide();
      }
    });
  }

  $('#global-search').on('input', function () {
    filterTableRows($(this).val());
  });

  filterTableRows('');
});



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

const selectAllToggleSelection = (source) => {
  checkboxes = $('[name="selectedUserList"]');

  for (var i = 0, n = checkboxes.length; i < n; i++) {
    if (source.checked && checkboxes[i].checked == false) {
      checkboxes[i].checked = source.checked;
      handleMemberSelection({ elem: checkboxes[i], username: checkboxes[i].getAttribute("username"), firstName: checkboxes[i].getAttribute("firstName"), lastName: checkboxes[i].getAttribute("lastName"), email: checkboxes[i].getAttribute("value") })
    } else if (source.checked == false) {
      checkboxes[i].checked = source.checked;
      handleMemberSelection({ elem: checkboxes[i], username: checkboxes[i].getAttribute("username"), firstName: checkboxes[i].getAttribute("firstName"), lastName: checkboxes[i].getAttribute("lastName"), email: checkboxes[i].getAttribute("value") })
    }
  }
};

const selectMemberSelectionCheckbox = (username, checked) => {
  if (checked) {
    $(`#${username}-marker`).show();
    $(`#${username}-checkbox`).prop('checked', true);
    $(`#${username}-tablerow`).removeClass('hover:bg-blue-50 hover:text-blue-700');
    $(`#${username}-tabledesc`).removeClass('text-gray-900').addClass('text-black-600');
    $(`#${username}-tabledesc`).addClass('font-bold');
  } else {
    $('#selectAllUsers').prop('checked', false)
    $(`#${username}-marker`).hide();
    $(`#${username}-checkbox`).prop('checked', false);
    $(`#${username}-tablerow`).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(`#${username}-tabledesc`).removeClass('text-black-600');
    $(`#${username}-tabledesc`).removeClass('font-bold');
  }
};

const addMemberSelection = (username, firstName, lastName, email) => {
  const selectionList = $('#member-selection-table');
  const newSpan = $("#member-selection-row-template").clone(true, true);
  selectMemberSelectionCheckbox(username, true);

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = firstName + " " + lastName + " " + email;
  newSpan.attr('id', `member-selection-${username}`);
  newSpan.attr('email', email)
  id = `member-selection-${username}`

  handleSelectionView();
};


const removeSelectionSpanElem = (elem) => {
  const spanId = elem.id || elem.attr('id');
  const username = spanId.replace('member-selection-', '');

  elem.remove();
  selectMemberSelectionCheckbox(username, false);

  handleSelectionView();
};

const removeMemberSelection = (username) => {
  removeSelectionSpanElem($(`#member-selection-${username}`));
};

const removeMemberSelectionUI = (elem) => {
  removeSelectionSpanElem(elem.parentElement.parentElement);
};

const removeAllMembers = () => {
  const members = $('#member-selection-table').children('tr');
  for (iter = 0; iter < members.length; iter++) {
    removeSelectionSpanElem(members[iter]);
  }
};

const handleMemberSelection = ({ elem, username, firstName, lastName, email }) => {
  // console.log('clicked--->', { elem, username, firstName, lastName, email })
  if (elem.checked) {
    addMemberSelection(username, firstName, lastName, email);
  } else {
    removeMemberSelection(username);
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
    console.log("success")
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

$(document).on('click', '#submitNewGroup', function () {
  const members = $('#member-selection-table').children('tr');
  const emails = [];
  var isValid = true;
  var csrf_token = $('input[name="csrfmiddlewaretoken"]').val();
  var newGroupNamePattern = /[A-Za-z0-9][A-Za-z0-9-]{2,}/;
  var newGroupReasonPattern = /.+/;
  var urlBuilder = "/group/create"


  for (iter = 0; iter < members.length; iter++) {
    emails.push($(members[iter])[0].getAttribute("email"));
  }

  const selectedUserList = emails
  const newGroupName = document.getElementById('newGroupName').value;
  const newGroupReason = document.getElementById('newGroupReason').value;
  const requiresAccessApprove = document.getElementById('requiresAccessApprove').checked;

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
        var msg = result.status.msg;
        showRequestSuccessMessage(msg)
      },
      error: function (response) {
        var error_title = response.responseJSON.error.error_msg;
        var error_message = response.responseJSON.error.msg;
        showNotificiation("failed", error_message, error_title)
      }
    });
  }
});
