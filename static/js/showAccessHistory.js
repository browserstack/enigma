let currentStatusFilterState = 'hidden';

const focusFilterStatus = (elem) => {
  const ulElem = $(elem).children('ul');
  if (currentStatusFilterState == 'hidden') {
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

  if (inputElem.is(':checked')) {
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


function showInfoDiv(element, request_id, requested_on, updated_on) {
  console.log('displaying....')
  console.log('updated_on-->', requested_on)
  var infoDiv = $(`#infoDiv-${request_id}`);
  infoDiv.removeClass("hidden");

  var currentDate = new Date();

  var requested_date = new Date((requested_on).split(',').slice(0, 2).join(','));

  var diffMilliseconds = currentDate - requested_date;
  var diffSeconds = diffMilliseconds / 1000;
  var diffMinutes = diffSeconds / 60;
  var diffHours = diffMinutes / 60;
  var diffDays = diffHours / 24;
  diffDays = Math.round(diffDays);
  infoDiv.children('div').children('div#process').children('span.text-slate-400').text(`${diffDays} days`)

}

function hideInfoDiv(elem, request_id) {
  var infoDiv = $(`#infoDiv-${request_id}`);
  infoDiv.addClass("hidden");
  console.log("hiding...")
  // infoDiv.classList.add("hidden");
}

