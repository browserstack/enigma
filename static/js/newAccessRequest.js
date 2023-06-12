const selectedList = {};

const handleSelectionView = () => {
  const finalCount = $('#module-selection-table').children('tr').length;

  if(finalCount < 1) {
    $('#module-selection-empty').show();
    $('#module-selection-list').hide();
    $('#module-selection-list').children('nav').hide();
    $('#module-selected-count').hide();
  } else {
    $('#module-selection-empty').hide();
    $('#module-selection-list').show();
    $('#module-selection-list').children('nav').css('display', 'flex');
    $('#module-selected-count').show();
    $('#module-selected-count').text(finalCount + ' selected');
  }
};

const selectCheckbox = (elem, checked) => {
  if(checked) {
    $(elem).find('input').prop('checked', true);
    $(elem).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(elem).children('td#description-td').removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(elem).find('input').prop('checked', false);
    $(elem).children('td#description-td').addClass('text-gray-900').removeClass('text-blue-600');
    $(elem).addClass('hover:bg-blue-50 hover:text-blue-700').removeClass('bg-gray-50');
  }
};

const addModuleSelection = (elem) => {
  const selectionList = $('#module-selection-table');
  const newSpan = $("#module-selection-row-template").clone(true, true);
  
  selectCheckbox(elem, true);
  const moduleDesc = $(elem).attr("module_desc");
  const moduleTag = $(elem).attr("module_tag");
  selectedList[moduleTag] = true;

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = moduleDesc;
  newSpan.attr('module_tag', moduleTag);

  handleSelectionView();
};

const removeSelectionSpanElem = (rightElem, leftElem) => {

  rightElem.remove();
  selectCheckbox(leftElem, false);
  selectedList[$(leftElem).attr("module_tag") || $(rightElem).attr("module_tag")] = false;

  handleSelectionView();
};

const removeModuleSelection = (elem) => {
  removeSelectionSpanElem($("#module-selection-table").find(`tr[module_tag="${$(elem).attr('module_tag')}"]`), elem);
};

const removeModuleSelectionUI = (elem) => {
  rightElem = elem.parentElement.parentElement;
  removeSelectionSpanElem(rightElem, $("#module-list-table").find(`tr[module_tag="${$(rightElem).attr('module_tag')}"]`));
};

const removeAllModules = () => {
  const modules = $('#module-selection-table').children('tr');
  for(iter = 0; iter < modules.length; iter++) {
    removeSelectionSpanElem(modules[iter], $("#module-list-table").find(`tr[module_tag="${$(modules[iter]).attr('module_tag')}"]`));
  }
};

const handleModuleSelection = (elem) => {
  if(!$(elem).find('input').prop('checked')) {
    addModuleSelection(elem);
  } else {
    removeModuleSelection(elem);
  }
};

const handleModuleSelectionCheckbox = (elem) => {
  $(elem).prop('checked', !$(elem).prop('checked'));
}

const raiseAccessRequest = () => {
  const modules = $('#module-selection-table').children('tr');
  const accessTags = [];

  for(iter = 0; iter < modules.length; iter++) {
    accessTags.push(`accesses=${$(modules[iter]).attr("module_tag")}`);
  }

  const finalUrl = `/access/requestAccess?${accessTags.join("&")}`;
  window.location = finalUrl;
};


function search(event, elem) {
  if(event.key === "Enter") {
    fetchAccessModules($(elem).val());
  }
}

const fetchAccessModules = (search=undefined) => {
  $.ajax({
    url: "/api/v1/getAccessModules",
    data: {"search": search},
    error: function (XMLHttpRequest, textStatus, errorThrown) {
      const msg = XMLHttpRequest.responseJSON;
      showNotificiation("Failed", msg["error"]);
    }
  }).done(function(data, statusText, xhr) {
    if(data["modulesList"]) {
      $("#module-list-table tr").remove()

      const rows = data["modulesList"].map((moduleList) => {
        return `<tr onclick="handleModuleSelection(this)" module_tag="${moduleList[0]}"  module_desc="${ moduleList[1] }"  class="${selectedList[moduleList[0]]? "bg-gray-50": "hover:bg-blue-50 hover:text-blue-700"}">
        <td class="relative w-12 px-6 sm:w-16 sm:px-8">
          <input type="checkbox" class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600 sm:left-6" ${ selectedList[moduleList[0]]? "checked": "" } onclick="handleModuleSelectionCheckbox(this)"></input>
        </td>
        <td class="whitespace-nowrap py-4 pr-3 text-sm font-medium ${ selectedList[moduleList[0]]? "text-blue-600" : "text-gray-900"}" id="description-td">${ moduleList[1] }</td>
      </tr>`
      });

      $("#module-list-table").append(rows.join(""));
    }
  });
}

$(window).on("load", ()=> {
  fetchAccessModules();
})
