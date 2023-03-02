$(function () {
  $("#tabs").tabs();
});

const focusActiveTab = (elem) => {
  const inputElem = $(elem).children('a');
  const active = document.getElementsByClassName("active");
  if (active != inputElem) {
    $(active).removeClass("active text-blue-600 border-blue-600 dark:text-blue-500 dark:border-blue-500")
      .addClass("border-transparent hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300");
    $(inputElem).removeClass("border-black hover:text-gray-600 hover:border-gray-300 dark:hover:text-gray-300")
      .addClass("active text-blue-600 border-blue-600 dark:text-blue-500 dark:border-blue-500");
  }
};
