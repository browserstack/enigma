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

$(document).ready(function(){
  if(  $('#users-tab tbody tr').length >= 1  ) {
       $('#myTable').addClass('add-scroll');
   }
 });
