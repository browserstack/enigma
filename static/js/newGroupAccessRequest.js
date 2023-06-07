const handleModuleSelectionCheckbox = (elem) => {
  $(elem).prop('checked', !$(elem).prop('checked'));
}

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
    $(elem).children('td#groupaccessrequest-description-td').removeClass('text-gray-900').addClass('text-blue-600');
  } else {
    $(elem).find('input').prop('checked', false);
    $(elem).removeClass('bg-gray-50').addClass('hover:bg-blue-50 hover:text-blue-700');
    $(elem).children('td#groupaccessrequest-description-td').removeClass('text-blue-600').addClass('text-gray-900');
  }
};

const addModuleSelection = (elem) => {
  const selectionList = $('#module-selection-table');
  const newSpan = $("#module-selection-row-template").clone(true, true);

  selectCheckbox(elem, true);
  const module_tag = $(elem).attr("module_tag");
  const module_desc = $(elem).attr("module_desc");

  newSpan.appendTo(selectionList);
  newSpan.show();
  const tableData = newSpan.children('td');
  tableData[0].textContent = module_desc;
  newSpan.attr('module_tag', module_tag);
  newSpan.attr('module_desc', module_desc);

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

const raiseAccessRequest = () => {
  const modules = $('#module-selection-table').children('tr');
  const groupName = $('#groupNameHeading').html();
  const accessTags = [];

  for(iter = 0; iter < modules.length; iter++) {
    accessTags.push(`accessList=${$(modules[iter]).attr("module_tag")}`);
  }
  accessTags.push(`groupName=${groupName}`);

  const finalUrl = `/group/requestAccess?${accessTags.join("&")}`;
  window.location = finalUrl;
};
