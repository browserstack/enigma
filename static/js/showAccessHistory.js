let currentStatusFilterState = 'hidden';

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

const selectLI = (elem) => {
  const inputElem = $(elem).children('span').children('input');
  const checkboxSpan = $(elem).children('span')[0];
  const textSpan = $(elem).children('span')[1];

  if(inputElem.is(':checked')) {
    $(elem).removeClass("text-white bg-blue-600").addClass("text-gray-900");
    inputElem.prop('checked', false);
    $(checkboxSpan).removeClass("text-white").addClass("text-blue-600");
    $(textSpan).removeClass("font-semibold").addClass("font-normal");
  } else {
    $(elem).removeClass("text-gray-900").addClass("text-white bg-blue-600");
    inputElem.prop('checked', true);
    $(checkboxSpan).removeClass("text-blue-600").addClass("text-white");
    $(textSpan).removeClass("font-normal").addClass("font-semibold");
  }
};
