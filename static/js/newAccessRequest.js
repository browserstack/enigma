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
    accessTags.push(`accesses=${modules[iter].id.replace('module-selection-', '')}`);
  }

  const finalUrl = `/access/requestAccess?${accessTags.join("&")}`;
  window.location = finalUrl;
};
