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

const selectCheckbox = (moduleTag, checked) => {
  if(checked) {
    $(`#${moduleTag}-checkbox`).prop('checked', true);
    $(`#${moduleTag}-tablerow`).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(`#${moduleTag}-tabledesc`).removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(`#${moduleTag}-checkbox`).prop('checked', false);
    $(`#${moduleTag}-tablerow`).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(`#${moduleTag}-tabledesc`).removeClass('text-blue-600').addClass('text-gray-900');
  }
};

const addModuleSelection = (moduleTag, moduleDesc) => {
  const selectionList = $('#module-selection-table');
  const newSpan = $("#module-selection-row-template").clone(true, true);
  selectedList[moduleTag] = true;

  selectCheckbox(moduleTag, true);

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = moduleDesc;
  newSpan.attr('id', `module-selection-${moduleTag}`);

  handleSelectionView();
};

const removeSelectionSpanElem = (elem) => {
  const spanId = elem.id || elem.attr('id');
  const moduleTag = spanId.replace('module-selection-', '');
  selectedList[moduleTag] = false;

  elem.remove();
  selectCheckbox(moduleTag, false);

  handleSelectionView();
};

const removeModuleSelection = (moduleTag) => {
  removeSelectionSpanElem($(`#module-selection-${moduleTag}`));
};

const removeModuleSelectionUI = (elem) => {
  removeSelectionSpanElem(elem.parentElement.parentElement);
};

const removeAllModules = () => {
  const modules = $('#module-selection-table').children('tr');
  for(iter = 0; iter < modules.length; iter++) {
    removeSelectionSpanElem(modules[iter]);
  }
};

const handleModuleSelection = (elem, moduleTag, moduleDesc) => {
  if(elem.checked) {
    addModuleSelection(moduleTag, moduleDesc);
  } else {
    removeModuleSelection(moduleTag);
  }
};

const raiseAccessRequest = () => {
  const modules = $('#module-selection-table').children('tr');
  const accessTags = [];

  for(iter = 0; iter < modules.length; iter++) {
    accessTags.push(`accesses=${modules[iter].id.replace('module-selection-', '')}`);
  }

  const finalUrl = `/access/requestAccess?${accessTags.join("&")}`;
  window.location = finalUrl;
};


function search(event, elem) {
  if(event.key === "Enter") {
    $(elem).val()

    $.ajax({
      url: "/api/v1/getAccessModules",
      data: {"search": $(elem).val()}
    }).done(function(data, statusText, xhr) {
      if(data["modulesList"]) {
        $("#module-list-table tr").remove()

        const rows = data["modulesList"].map((moduleList) => {
          if(!selectedList[moduleList[0]]) {
            return `<tr id="${moduleList[0]}-tablerow" class="hover:bg-blue-50 hover:text-blue-700">
              <td class="relative w-12 px-6 sm:w-16 sm:px-8">
                <input type="checkbox" class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600 sm:left-6" onclick="handleModuleSelection(this, '${moduleList[0]}', '${moduleList[1]}');" id="${moduleList[0]}-checkbox"></input>
              </td>
              <td class="whitespace-nowrap py-4 pr-3 text-sm font-medium text-gray-900" id="${moduleList[0]}-tabledesc">${moduleList[1]}</td>
            </tr>`
          } else {
            return `<tr id="${moduleList[0]}-tablerow" class="bg-gray-50">
              <td class="relative w-12 px-6 sm:w-16 sm:px-8">
                <input type="checkbox" class="absolute left-4 top-1/2 -mt-2 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-600 sm:left-6" checked onclick="handleModuleSelection(this, '${moduleList[0]}', '${moduleList[1]}');" id="${moduleList[0]}-checkbox"></input>
              </td>
              <td class="whitespace-nowrap py-4 pr-3 text-sm font-medium text-blue-600" id="${moduleList[0]}-tabledesc">${moduleList[1]}</td>
            </tr>`
          }
        })
        $("#module-list-table").append(rows.join(""))
      } else if(data["search_error"]) {
        showNotification()
      }
    })
  }
}
