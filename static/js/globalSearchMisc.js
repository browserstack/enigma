
function change_page(page, change=null){
  page = Number(page);
  if(change) {
    page += change;
  }

  const query_param = current_query_params();

  query_param["page"] = [page];
  const url = create_url_from_query_params(query_param);
  window.location.href = url;
}

function current_query_params() {
  if(!window.location.href.includes('?')){
    return {};
  }
  let hashes = window.location.href.slice(window.location.href.indexOf('?')+1).split('&');
  if(hashes[0]===""){
    return {}
  }
  let query_params = {};
  for (hash of hashes) {
    hash = hash.split('=');
    if(!query_params[hash[0]]) {
      query_params[hash[0]] = [];
    }
    query_params[hash[0]].push(hash[1]);
  }

  return query_params;
}

function search(event) {
  event.preventDefault();

  const query_param = current_query_params();
  query_param["page"] = [];
  query_param["search"] ? query_param["search"].pop(): (query_param["search"] = []);
  query_param["search"].push(get_search_value());
  const url = create_url_from_query_params(query_param);
  window.location.href = url;
}

function select_filter(elem) {
  const query_param = current_query_params();
  query_param["page"] = [];
  key = $(elem).attr("key");

  if(elem.checked) {
    query_param[key] ? query_param[key].push($(elem).val()) : query_param[key] = [$(elem).val()];
  }
  else {
    const index =  query_param[key].indexOf($(elem).val());
    if(index > -1) {
      query_param[key].splice(index, 1);
    }
  }
  const url = create_url_from_query_params(query_param);
  window.location.href = url;
}

function create_url_from_query_params(query_param) {
  const query_array = [];
  for(const k in query_param) {
    if(query_param[k]){
      for(const val of query_param[k]) {
        query_array.push(`${k}=${val}`);
      }
    }
  }

  const query_string = query_array.join('&');
  const link = `${window.location.pathname}?`;
  return link+query_string;
}

function get_search_value() {
  return $("#global-search").val();
}
