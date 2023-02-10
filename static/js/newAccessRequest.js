const handleSelectionView = () => {
  const finalCount = $('#module-selection-list').children('span').length;

  if(finalCount < 1) {
    $('#module-selection-empty').show();
    $('#module-selection-list').hide();
    $('#module-selected-count').hide();
  } else {
    $('#module-selection-empty').hide();
    $('#module-selection-list').show();
    $('#module-selected-count').show();
    $('#module-selected-count').text(finalCount + ' selected');
  }
};

const addModuleSelection = (moduleTag, moduleDesc) => {
  const selectionList = $('#module-selection-list');
  const newSpan = $("#module-selection-span-template").clone(true, true);

  $('#' + moduleTag + '-marker').show();
  $('#' + moduleTag + '-checkbox').prop('checked', true);

  newSpan.appendTo(selectionList);
  newSpan.show();
  newSpan.children('div').text(moduleDesc);
  newSpan.attr('id', `module-selection-${moduleTag}`);
};

const removeSelectionSpanElem = (elem) => {
  const spanId = elem.id || elem.attr('id');
  const moduleTag = spanId.replace('module-selection-', '');

  elem.remove();
  $(`#${moduleTag}-marker`).hide();
  $(`#${moduleTag}-checkbox`).prop('checked', false);
  handleSelectionView();
};

const removeModuleSelection = (moduleTag) => {
  removeSelectionSpanElem($(`#module-selection-${moduleTag}`));
};

const removeModuleSelectionUI = (elem) => {
  removeSelectionSpanElem(elem.parentElement);
};

const handleModuleSelection = (elem, moduleTag, moduleDesc) => {
  if(elem.checked) {
    addModuleSelection(moduleTag, moduleDesc);
  } else {
    removeModuleSelection(moduleTag);
  }
  handleSelectionView();
};
