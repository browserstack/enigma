var currentStatusFilterState = 'hidden';

function focusFilterStatus (elem) {
  const ulElem = $(elem).children('ul');
  if(currentStatusFilterState == 'hidden') {
    currentStatusFilterState = 'shown';
    ulElem.show();
  } else {
    currentStatusFilterState = 'hidden';
    ulElem.hide();
  }
};
