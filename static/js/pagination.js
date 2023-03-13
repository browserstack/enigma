let activePage = 0
const rowsShown = 2;

function paginate() {
  $('#paginated').after('<nav id="nav"></nav>');
    $('#nav').addClass('mt-8 flex items-center justify-between border-t border-gray-200 sm:px-0 pt-6 px-4 sm:px-6 lg:px-8 pb-6 w-full');
    $('#nav').append('<div id="prevDiv" class="-mt-px flex w-0 flex-1"></div')
    $('#prevDiv').append ('<a href="#" class="inline-flex items-center border-t-2\
                              border-transparent pt-4 pr-1 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">\
                              <svg class="mr-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"\
                              fill="currentColor" aria-hidden="true"> <path fill-rule="evenodd"\
                              d="M18 10a.75.75 0 01-.75.75H4.66l2.1 1.95a.75.75 0 11-1.02 1.1l-3.5-3.25a.75.75 0 010-1.1l3.5-3.25a.75.75\
                              0 111.02 1.1l-2.1 1.95h12.59A.75.75 0 0118 10z" clip-rule="evenodd" /> </svg> Previous </a> ')
    $('#nav').append('<div id="pageItem" class="md:-mt-px md:flex"><ul class="pagination"></ul></div')
    $('#nav').append('<div id="nextDiv" class="-mt-px flex w-0 flex-1 justify-end"></div')
    $('#nextDiv').append ('<a href="#" class="inline-flex items-center\
                              border-t-2 border-transparent pt-4 pl-1 text-sm font-medium text-gray-500 hover:border-gray-300 hover:text-gray-700">\
                              Next <svg class="ml-3 h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"\
                              fill="currentColor" aria-hidden="true"> <path fill-rule="evenodd" d="M2 10a.75.75 0 01.75-.75h12.59l-2.1-1.95a.75.75\
                              0 111.02-1.1l3.5 3.25a.75.75 0 010 1.1l-3.5 3.25a.75.75 0 11-1.02-1.1l2.1-1.95H2.75A.75.75 0 012 10z"\
                              clip-rule="evenodd" /> </svg> </a> ')
    var rowsTotal = $('#paginated tbody tr').not('.filtered').length;
    var numPages = Math.ceil(rowsTotal/rowsShown);
    for (i = 0;i < numPages;i++) {
        var pageNum = i + 1;
        $('.pagination').append ('<li class="px-4 inline-flex items-center border-t-2 pt-4 text-sm font-medium text-gray-500 hover:text-gray-700 hover:border-gray-300"><a href="#" rel="'+i+'">'+pageNum+'</a></li>');
        if (i==0){
          $("#prevDiv").addClass("invisible");
          if(numPages == i+1) {
            $("#nextDiv").addClass("invisible");
          }
        }
    }

    $('.pagination li:first').removeClass('text-gray-500 hover:text-gray-700 hover:border-gray-300').addClass('active border-blue-500 text-blue-600');
    $('#paginated tbody tr').not('.filtered').hide();
    $('#paginated tbody tr').not('.filtered').slice (0, rowsShown).show();


    $('.pagination li').bind('click', function() {
      $('.pagination li').removeClass('active border-blue-500 text-blue-600').addClass('text-gray-500 hover:text-gray-700 hover:border-gray-300');
      $(this).removeClass('text-gray-500 hover:text-gray-700 hover:border-gray-300').addClass('active border-blue-500 text-blue-600');
      var currPage = $(this).children('a').attr('rel');
      var page = parseInt(currPage) + parseInt(1)
      if (page == 1) {
        $("#prevDiv").addClass("invisible");
        if (page != numPages){
          $("#nextDiv").removeClass("invisible");
        }else{
          $("#nextDiv").addClass("invisible");
        }
      } else if (page < numPages) {
          $("#prevDiv").removeClass("invisible");
          $("#nextDiv").removeClass("invisible");
      } else {
        $("#prevDiv").removeClass("invisible");
        $("#nextDiv").addClass("invisible");
      }
      var startItem = currPage * rowsShown;
      var endItem = startItem + rowsShown;
      $('#paginated tbody tr').not('.filtered').hide().slice(startItem, endItem).css('display','table-row');
    });

    $("#nextDiv").click(function () {
      if ($(".pagination li").next().length != 0) {
        $('.pagination li.active').next().removeClass('text-gray-500 hover:text-gray-700 hover:border-gray-300').addClass('active border-blue-500 text-blue-600');
        $('.pagination li.active').prev().removeClass('active border-blue-500 text-blue-600').addClass('text-gray-500 hover:text-gray-700 hover:border-gray-300');
        $(".pagination li.active a").trigger("click");
      }
    });

    $("#prevDiv").click(function () {
      if ($(".pagination li").prev().length != 0) {
        $('.pagination li.active').prev().removeClass('text-gray-500 hover:text-gray-700 hover:border-gray-300').addClass('active border-blue-500 text-blue-600');
        $('.pagination li.active').next().removeClass('active border-blue-500 text-blue-600').addClass('text-gray-500 hover:text-gray-700 hover:border-gray-300');
        $(".pagination li.active a").trigger("click");
      }
    });
}

$(document).ready (function () {
  paginate()
});

function selectLI (elem, elem_index) {
  all_selected_filters = checkboxFilterStyling(elem, elem_index)
  filterTable = '#paginated tbody tr'
  filterProducts(all_selected_filters, filterTable)
  repaginate()
}

function repaginate(){
  pageElem = $('#nav')
  if (pageElem) {
    pageElem.remove();
  }
  paginate()
}

function filterUser (elem, elem_index) {
  all_selected_filters = checkboxFilterStyling(elem, elem_index)
  filterTable = '#users-tab tbody tr'
  filterProducts(all_selected_filters, filterTable)
  $(filterTable).not('.filtered').show()
}

function filterProducts(filters, filterTable) {
  dataStatus = []
  cols = []
  if (filters.length != 0){
    $(filterTable).addClass('filtered').css('display','none');
    for(var i=0; i<filters.length; i++) {
      dataStatus.push('[data-status-' + filters[i].split(":")[0] + '="' + filters[i].split(":")[1] + '"]')
      if (cols.indexOf(filters[i].split(":")[0]) == -1){
        cols.push(filters[i].split(":")[0])
      }
    }
    if (cols.length > 1){
      var result = dataStatus.flatMap(
        (v, i) => dataStatus.slice(i+1).map( w => v + '' + w )
      );
      for (let x in result){
        $(filterTable + result[x]).removeClass('filtered');
      }
    }else{
      $(filterTable + dataStatus).removeClass('filtered');
    }
  }else{
    $(filterTable).removeClass('filtered');
  }
}

var all_selected_filters = [];
function checkboxFilterStyling(elem, elem_index){
  inputElem = $(elem).children('span').children('input')
  const textSpan = $(elem).children('span')[1];
  for(var i=0; i<inputElem.length; i++) {
    if(inputElem[i].checked) {
      inputElem.prop('checked', false);
      var selected = all_selected_filters.indexOf(elem_index + ":" + inputElem[i].value);
      all_selected_filters.splice(selected, 1);
      $(textSpan).removeClass("font-semibold").addClass("font-normal");
    }else{
      inputElem.prop('checked', true);
      all_selected_filters.push(elem_index + ":" + inputElem[i].value);
      $(textSpan).removeClass("font-normal").addClass("font-semibold");
    }
  }
  return all_selected_filters
}
