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
    $(`#${moduleTag}-marker`).show();
    $(`#${moduleTag}-checkbox`).prop('checked', true);
    $(`#${moduleTag}-tablerow`).removeClass('hover:bg-blue-50 hover:text-blue-700').addClass('bg-gray-50');
    $(`#${moduleTag}-tabledesc`).removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(`#${moduleTag}-marker`).hide();
    $(`#${moduleTag}-checkbox`).prop('checked', false);
    $(`#${moduleTag}-tablerow`).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(`#${moduleTag}-tabledesc`).removeClass('text-blue-600').addClass('text-gray-900');
  }
};

const addModuleSelection = (moduleTag, moduleDesc) => {
  const selectionList = $('#module-selection-table');
  const newSpan = $("#module-selection-row-template").clone(true, true);

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
  const groupName = $('#groupNameHeading').html();
  const accessTags = [];

  for(iter = 0; iter < modules.length; iter++) {
    accessTags.push(`accessList=${modules[iter].id.replace('module-selection-', '')}`);
  }
  accessTags.push(`groupName=${groupName}`);

  const finalUrl = `/group/requestAccess?${accessTags.join("&")}`;
  window.location = finalUrl;
};
