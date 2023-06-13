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
    currentStatusFilterState = 'hidden';
    ulElem.hide();
  }
};
