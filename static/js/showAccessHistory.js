let currentStatusFilterState = 'hidden';

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

const focusGroupFilter = (elem) => {
  const ulElem = $(elem).children('form').children('ul');
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
    inputElem.prop('checked', false);
    $(textSpan).removeClass("font-semibold").addClass("font-normal");
  } else {
    inputElem.prop('checked', true);
    $(textSpan).removeClass("font-normal").addClass("font-semibold");
  }
};
