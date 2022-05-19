// mainpage.js

'use strict';

// some global vars
let activeTabHeader = '';
let currTabName; 
let parentTabName = '';
let htmlBody; // sometimes should be global
// flags for yes/no page
let isYesNoActive = false;
let isYesNoPassed = false;
let isYesPressed = false;

let jsFuncs = {};

const spinnerHtml=`
  <p></p>
  <div class="spinner-cont text-center">
    <div class="spinner-border role="status">
      <span class="sr-only">
        Loading...
      </span>
    </div>
  </div>
  <p></p>
`

/* 
 * some subsidiary functions
 */

function getValOrText(field) {
  let val;
  val = $(field).val();
  // if empty val() try to get text() instead
  if( !(val) && typeof( $(field).text() != 'undefined') )
    val = $(field).text().trim();
  return val;
}

function getIdFromDropdown(dropdown) {
  if($(dropdown).val())
    for(const option of dropdown.find('option') ) {
      if( option.value == $(dropdown).val() )
        return $(option).attr('shadow_id');
    }
  ;
  return '';
}

// for csrf protection
function getCookie(c_name) {
  if (document.cookie.length > 0) {
    let c_start = document.cookie.indexOf(c_name + "=");
    if (c_start != -1) {
      c_start = c_start + c_name.length + 1;
      let c_end = document.cookie.indexOf(";", c_start);
      if (c_end == -1) c_end = document.cookie.length;
      return unescape(document.cookie.substring(c_start,c_end));
    }
  }
  return "";
}

function sendWithAjax(addr, objToSend, funcOnSuccess) {
  // preprocessor for array of arrays
  for( name of ['book_acc_pairs', 'goodslines','sidebar_filters_data'] ){
    if(name in objToSend)
      objToSend[name] = JSON.stringify(objToSend[name]);
  };
  // ajax call
  $.ajax({
    type:         'POST',
    headers:      {"X-CSRFToken":   getCookie('csrftoken') },
    url:          addr,
    data:         objToSend,
    cache:        false,
    success:      funcOnSuccess,  // it's arg = response data
    dataType:     'json',
  })
}


/* functions
 * for tab loading phase
 */

// function to load any tab part(frame, header, table etc.)
function loadTabPart(
  reqVars, 
  objToAppendTo, 
  callback = () => {} 
){ 
  let url;
  if(
    reqVars['tab_action'] == 'show_frame'
    || reqVars['tab_action'] == 'show_header'
  )
    url = '/tabs/' + reqVars['tab_action'] + '/' 
  else
    url = '/tabs/' + reqVars['tab_action'] + '/' 
      + (reqVars['tab_class'] ? (reqVars['tab_class'] + '/') : '')
      + (reqVars['tab_model'] ? (reqVars['tab_model'] + '/') : '')
  ;
  // send ajax
  sendWithAjax(
    url,
    reqVars,
    function(jsonData){ 
      // get html response
      htmlBody = jsonData['html_in_json'];
      // append tab's part to it's container
      objToAppendTo.append(htmlBody);
      // look for js to run on load and run it
      const addedJqueryHeader = $(objToAppendTo).find(
          '[tab_action="' + reqVars['tab_action'] + '"]'
          + '[tab_class="' + reqVars['tab_class'] + '"]'
          + '[tab_model="' + reqVars['tab_model'] + '"]'
      );
      const funcNames = $(addedJqueryHeader).attr('run_on_load');
      if(typeof funcNames !== 'undefined') {
        funcNames.split(' ').forEach(
          (funcName) => { 
            // run if func exists
            if(jsFuncs[funcName]) {
              jsFuncs[funcName](addedJqueryHeader); 
            };
          }
        )
      };
      // after the download
      callback();
    }
  );
}

// function to load all dropdowns in some downloaded/refreshed part
function loadDropdowns(objToAppendTo){
  let tabModel = '';
  let tabClass = '';
  // special case for materials-in-store dropdown 
  if($(objToAppendTo).hasClass('goodslines-cont')){
    const theHotId = $(objToAppendTo).closest('.tab-table-cont')
      .find('.row-id-able').attr('hot_transaction');
    if(theHotId == $('#consts-block').attr('goods_to_prod_hot_id')){
      tabClass = 'dropdown_store';
      tabModel = 'goodsline';
    } else if(theHotId == $('#consts-block').attr('shipping_hot_id')){
      tabClass = 'dropdown_stock';
      tabModel = 'goodsline';
    };
  };
  $(objToAppendTo).find('.load-dropdown').each( function() {
    loadTabPart({
        'tab_action' : 'show',
        'tab_class'  : tabClass ? tabClass : 'dropdown',
        'tab_model'  : tabModel ? tabModel : $(this).attr('field_var'),
        'row_id'   : '0',
      },$(this)
    );
  });
}

// function to load tab table, to some downloaded/refreshed part of tab
function loadTabTable(
  reqVars, // here's tab_class, tab_model, tab_name
  thisTablesParentCont // parent jquery object for loading tab table
){ 
  reqVars['tab_action'] = 'show';
  // add sidebar_dates
  reqVars['sidebar_date1'] = $('#datepicker1').val();
  reqVars['sidebar_date2'] = $('#datepicker2').val();
  // add sidebar filter's data
  const sidebarFiltersData = {};
  $('.sidebar-dropdown-select').each(function() {
    sidebarFiltersData[$(this).attr('field_var')] =
      getIdFromDropdown($(this))
    ;
  });
  reqVars['sidebar_filters_data'] = sidebarFiltersData;
  // add sidebar simple input's data
  $('.sidebar-simple-input').each(function() {
    sidebarFiltersData[$(this).attr('field_var')] = 
      $(this).val() ? $(this).val() : ''
    ;
  });
  reqVars['sidebar_filters_data'] = sidebarFiltersData;
  // show wheel if ness.
  if(
    !['empty', 'new', 'edit', 'dropdown', 'dropdown_store', 'dropdown_stock']
    .includes(reqVars['tab_class'])
  )
    $(thisTablesParentCont).append(spinnerHtml)
  ;
  loadTabPart( reqVars, 
    $(thisTablesParentCont),
    //.then
    function(){
      //
      // kill spinner
      $(thisTablesParentCont).find('.spinner-cont').remove();
      // load input dropdowns
      loadDropdowns( $(thisTablesParentCont) );
      // then if nessesary get and append goodslines table
      const goodslinesCont = $(thisTablesParentCont).find('.goodslines-cont');
      if( goodslinesCont.length ){
        reqVars['tab_class'] = 'pivot';
        if( 
          $(thisTablesParentCont).children('[tab_model]')
            .attr('tab_model') == 'killed_transaction'
        ) {
          reqVars['tab_model'] = 'killed_goodsline'
        } else {
          reqVars['tab_model'] = 'goodsline'
        };
        reqVars['root_transaction'] = reqVars['row_id'];
        reqVars['row_id'] = '0';
        loadTabTable(reqVars, goodslinesCont);
      };
    }
  );
}

// function to load full tab,  from frame to dropdowns
function loadFullTab(
  reqVars // here's tab_class, tab_model but tab_action, will set manually
){ 
  // check if such tab exists
  if(
      $('.tab-frame'
      + '[tab_class="' + reqVars['tab_class'] + '"]' 
      + '[tab_model="' + reqVars['tab_model'] + '"]'
    ).attr('id')
  ){
    // activate existing tab
    $('#tab-header-link-' + reqVars['tab_class'] + '__' + reqVars['tab_model'])
      .tab('show');
    return;
  };
  // load tab's frame
  reqVars['tab_action'] = 'show_frame';
  loadTabPart( reqVars, $('#tab-frames-cont'), 
    //.then
    function(){
      //
      // load tab's header
      reqVars['tab_action'] = 'show_header';
      loadTabPart(reqVars, $('#tab-headers-cont'), 
        //.then
        function(){
          // show the header(and the tab) after download
          const currTabHeaderId = $('<div>' + htmlBody + '</div>')
            .find('.tab-header-link').attr('id');
          $('#' + currTabHeaderId).tab('show');
          // tabheader's click = change active-tab value
          $('#' + currTabHeaderId).on('click', '', function() {
            activeTabHeader = $(this).parent();
          });
          // and save active-tab value now
          activeTabHeader = $('#' + currTabHeaderId).parent();
          //
          // and at last load tab's table
          const thisTablesParentCont = $('.tab-frame'
            + '[tab_class="' + reqVars['tab_class'] + '"]' 
            + '[tab_model="' + reqVars['tab_model'] + '"]'
          ).find(' .tab-table-cont')
          loadTabTable(reqVars, thisTablesParentCont);
        }
      ) 
    }
  );
}


/* the only function
 * for tab refresh phase
 */


function refreshThisTab(theButton) {
  const theTabFrame = theButton.closest('.tab-frame');
  // remove old tab's table part
  $(theTabFrame).find('.tab-table-cont').children().remove();
  // load new tab table
  loadTabTable({
      'tab_class': $(theTabFrame).attr('tab_class'),
      'tab_model': $(theTabFrame).attr('tab_model'),
      //    hot_transaction: '', //$(this).attr('hot_transaction',
      'row_id': 0,
    }, $(theTabFrame).find('.tab-table-cont') 
  );
} 


/* 
 * close fuctions
 */


function closeTab(tabFrameToClose) {
  // remember bootstrap's tab header consists of
  // tab header's container(li) and child tab header's link(a)
  // which points to tab's body(tab frame in our case and terms)
  const tabHeaderToClose = $(
    '.tab-header-link[href="#' + $(tabFrameToClose).attr('id') + '"]'
  ).parent();
  const prevTabHeader = $(tabHeaderToClose).prev();
  const nextTabHeader = $(tabHeaderToClose).next();
  // find out who'll be the next
  let newTabHeader = '';
  if(prevTabHeader.attr('id')) {  // n.b. compare ids not whole objects
    newTabHeader = prevTabHeader;
  } else if(nextTabHeader.attr('id')) {
    newTabHeader = nextTabHeader;
  };
  // remove old
  $(tabHeaderToClose).remove();
  $(tabFrameToClose).remove();
  // show new
  if(newTabHeader){ 
    activeTabHeader = newTabHeader;
    $(newTabHeader).children('a').first().tab('show');
  };
}

// close button action
function closeThisTab(theButton) {
  const theTabFrame = theButton.closest('.tab-frame');
  closeTab(theTabFrame);
}


/* 
 * save functions
 */


function makeSaveDict(tabFrameToSave, bookAccPairs, goodslinesCont = '') {
  // fill reqVars-to-save with basic mand.fields
  const reqVars = {
    'tab_action' : 'save',
    'tab_class': $(tabFrameToSave).attr('tab_class') ,
    'tab_model': $(tabFrameToSave).attr('tab_model') ,
    'row_id' : $(tabFrameToSave).find(
      '.tab-table-cont *[row_id]').attr('row_id') ,
    // add current book-acc.pair
    'book_acc_pairs' : bookAccPairs ,
  };
  // add plain input's values of given container only! to reqVars
  $(tabFrameToSave).find('.save-val')
    .not(
      $(tabFrameToSave).find('[tab_action] [tab_action] .save-val')
    )
    .each( function() {
      reqVars[$(this).attr('field_var')] = getValOrText(this);
  });
  // add shadow values of given container only! to reqVars
  $(tabFrameToSave)
    .find('.save-shadow').not(
      $(tabFrameToSave).find('[tab_action] [tab_action] .save-shadow')
    )
    .each( function() {
    // special case for new human_id: 
    // don't bother with its shadow_id, it doesn't exist yet
    if(
      reqVars['row_id'] == '0' 
      && $(this).attr('field_var') == 'human_id'
    ){
      reqVars['human_id'] = $(this).text().trim();
    } else {
      // result depends on if the field is dropdown or static
      if($(this).hasClass('load-dropdown'))
        reqVars[$(this).attr('field_var')] = getIdFromDropdown($(this))
      else 
        reqVars[$(this).attr('field_var')] = $(this).attr('shadow_id')
      ;
    };
  });
  // and add to reqVars goodslines if exist
  if(!goodslinesCont || reqVars['has_goodsline'] == '0') return reqVars;
  reqVars['goodslines'] = [];
  $(goodslinesCont).find('[row_id]').not('.goodslines-dummy-row')
  .each( function(){
    const goodsline = {};
    // header id
    goodsline['row_id'] = $(this).attr('row_id');
    goodsline['hot_transaction'] = $(goodslinesCont)
      .children('[hot_transaction]').attr('hot_transaction');
    // plain inputs
    $(this).find('.save-val')
      .not('.goodslines-dummy-row .save-val')
    .each( function() {
      goodsline[$(this).attr('field_var')] = getValOrText(this);
    });
    // shadow_id inputs
    $(this).find('.save-shadow')
      .not('.goodslines-dummy-row .save-shadow')
    .each( function() {
      goodsline[$(this).attr('field_var')] = $(this).attr('shadow_id');
    });
    reqVars['goodslines'].push(goodsline);
  });
  return reqVars;
}

function saveTab(
  tabFrameToSave, 
  callback = () => {},
  bookAccPairs = [], 
  goodslinesCont ='',
){
  // check requir.fields
  let allReady = true;
  $(tabFrameToSave).find('.never-empty').each( function() {
    if(!$(this).val()) {
      $(this).focus();
      allReady = false;
    };
  });
  if(!allReady) return 'notReady';
  // now gather info inside target cont.(the main func's arg)
  const reqVars = makeSaveDict(tabFrameToSave, bookAccPairs, goodslinesCont);
  // add empty employee field for non-employee-only transaction
  if(
    (reqVars['tab_model'] == 'transaction' 
      || reqVars['tab_model'] == 'killed_transaction'
    ) && !reqVars['employee'] && reqVars['partner'] 
  )
    reqVars['employee'] = reqVars['partner'];
  // and now send reqVars to backend
  loadTabPart(
    reqVars, 
    $(tabFrameToSave).find('.tab-table-cont'), 
    callback 
  )
//  console.log('/ saving result');
}

// for transaction model
// there may be a few of deb/cred_account pairs for single transaction
function saveTransactionTab(tabFrameToSave, callback) {
  let bookAccPairs = []; // this will be [ [ deb_account, cred_account ] * n ]
  //main loop over deb/cred_account pairs to fill it's array
  $('.book-acc-set').each(function() {
    let debAccount  = getIdFromDropdown( 
      $(this).find('.save-shadow-special[field_var="deb_account"]') 
    );
    let credAccount = getIdFromDropdown( 
      $(this).find('.save-shadow-special[field_var="cred_account"]') 
    );
    // check if deb/cred_account pairs are unique
    // if not go to next given pair(row)
    if(debAccount == credAccount) return;
    for(const bookAccPair of bookAccPairs) {
      if(debAccount == bookAccPair[0] && credAccount == bookAccPair[1]) 
        return;
    };
    // make an item for array of unique deb/cred.pairs
    bookAccPairs.push( [debAccount, credAccount] );
  });
  // call ordinary save-tab function
  if(bookAccPairs) 
    saveTab(
      tabFrameToSave, 
      callback,
      bookAccPairs, 
      $(tabFrameToSave).find('[tab_action][tab_model="goodsline"').parent(),
    ) 
  else
    //notReady
    callback(); // close tab
  ;
}

// save button action
function saveThisTab(theButton) {
  // save function: std or transaction, they are different
  const saveTabFunction = 
    (theButton.closest('.tab-frame').find('*[tab_model]')
      .attr('tab_model') == 'transaction'
    ) ? saveTransactionTab : saveTab
  ;
  // call save function end close the tab on success
  saveTabFunction(
    theButton.closest('.tab-frame'),
    function(){
      closeThisTab(theButton);
    },
  );
} 


/* 
 * del functions
 */

function showYesNoScreen(callback, theButton = {}, alertMsg = ''){
  //
  function clearYesNoPage(){
    // hide yes/no dialog
    $('#tabs-cont').show();
    $('#yes-no-cont').hide();
    $('#yes-no-alert-msg').text('');
    // reset yes/no click actions
    $('#yes-button').off('click');
    $('#no-button').off('click');
  }
  //
  // set yes/no click actions
  $('#yes-button').on('click', function() {
    callback(theButton); 
    clearYesNoPage();
  });
  $('#no-button').on('click', function() {
    clearYesNoPage();
  });
  // show yes/no dialog
  if(alertMsg){
    $('#yes-no-alert-msg').text(alertMsg);
  };
  $('#tabs-cont').hide();
  $('#yes-no-cont').show();
};

function delTab(tabFrameToDel) {
  // make simple reqVars to save
  const reqVars = {
    'tab_action'  : 'kill',
    'tab_class'   : $(tabFrameToDel).attr('tab_class') ,
    'tab_model'   : $(tabFrameToDel).attr('tab_model') ,
    'row_id' : $(tabFrameToDel).find('.tab-table-cont *[row_id]')
      .attr('row_id')
    ,
    'human_id'    : $(tabFrameToDel)
      .find('.tab-table-cont *[field_var="human_id"]')
      .first().attr('shadow_id')
    ,
  };
  loadTabPart( reqVars, $(tabFrameToDel).find('.tab-table-cont') );
}

// del button action
function delThisTab(theButton) {
  if(!delTab( theButton.closest('.tab-frame') )) {
      closeThisTab(theButton)
  };
} 


/*
 *  misc.functions for previous phases
 */

// pensil buttons action
function editThisItem(theButton) { 
  // vals can be hardcoded in the button
  let reqVars;
  if(
      $(theButton).attr('btn_tab_class')
      && $(theButton).attr('btn_tab_model')
      && $(theButton).attr('btn_row_id')
      && $(theButton).attr('btn_hot_transaction')
  ){
    // trick: if the button leads to material's history
    // set sidebar material filter to current material
    if(
      $(theButton).attr('btn_tab_class') == 'material_history'
      && $(theButton).attr('btn_tab_model') == 'goodsline'
    ){
      const materialId = $(theButton).closest('tr')
        .find('td[field_var="material"]').text().trim();
      $('.sidebar-dropdown-select[field_var="material"]').val(materialId);
    }
    // the same trick for partner>transaction balances
    else if(
      $(theButton).attr('btn_tab_class') == 'partners_balance'
      && $(theButton).attr('btn_tab_model') == 'transaction'
    ){
      const partnerId = $(theButton).closest('tr')
        .find('td[field_var="name"]').text().trim();
      $('.sidebar-dropdown-select[field_var="partner"]').val(partnerId);
    };
    reqVars = {
      'tab_class'       : $(theButton).attr('btn_tab_class'),
      'tab_model'       : $(theButton).attr('btn_tab_model'),
      'row_id'          : $(theButton).attr('btn_row_id'),
      'hot_transaction' : $(theButton).attr('btn_hot_transaction'),
    }
  // or search them among the ancestors
  } else {
    reqVars = {
      'tab_class': 'edit',
      'tab_model': theButton.closest('.tab-frame').attr('tab_model'),
      'row_id' : theButton.closest('tr[row_id]').attr('row_id'),
      'hot_transaction' : theButton.closest('[hot_transaction]')
        .attr('hot_transaction'),
    }
  };
  loadFullTab(reqVars);
} 

function makeHumanId() {
  return (//'0000000000' + (
        +( new Date().getTime() 
          - new Date(Date.UTC(2021, 0, 1, 0, 0, 0, 0)).getTime()
        ) / 100
      ).toFixed()
  //).slice(-10,)
}
// fix numeric inputs
function fixNum(format, num) {
  let fixed;
  if(format == 'qty')
    fixed = parseFloat(
      num.toString().replace(',', '.')
      ).toFixed(3)
  else if(format == 'money')
    fixed = parseFloat(
      num.toString().replace(',', '.')
      ).toFixed(2);
  else if(format == 'price')
    fixed = parseFloat(
      num.toString().replace(',', '.')
      ).toFixed(4);
  ;
  if(isNaN(fixed))
    return +0
  else if(num < 0) 
    return -fixed
  else if(num) 
    return fixed
  else
    return +0
  ;
}


/*
 * goodsline table's functions
 */
function refreshTransactionMoney(btnOrParent) {
  const transactionMoneyField = $(btnOrParent).closest('.tab-table-cont')
      .find('*[field_var="money"]');
  const isShipping = ( $(btnOrParent).closest('.tab-table-cont')
      .find('*[shipping_hot_id]').attr('shipping_hot_id')
    == $(btnOrParent).closest('.tab-table-cont')
      .find('*[hot_transaction]').attr('hot_transaction')
  );
  // calc.both totals and set one of them to the field
  $(transactionMoneyField).text(
    () => {
      let sum = +0;
      let sumShip = +0;
      // iter.over goodsline dummy input row's neighbors
      $(btnOrParent).closest('.tab-table-cont')
        .find('.goodslines-dummy-row').parent()
        .find('[row_id]').not('.goodslines-dummy-row')
        .each(
      function(){
        sum += +$(this).find('*[field_var="total"]').text();
        sumShip += +$(this).find('*[field_var="ship_total"]').text();
      });
      return fixNum('money', isShipping ? sumShip : sum);
    }
  );
  // for ajax send
  $(transactionMoneyField).val( $(transactionMoneyField).text() );
}

function refreshGoodslineTotals(saveButton) {
  // total
  $(saveButton).closest('tr')
  .find('[field_var="total"]').text(
    fixNum(
      'money', 
      $(saveButton).closest('tr')
        .find('[field_var="qty"]').val()
      * $(saveButton).closest('tr')
        .find('[field_var="price"]').val()
    )
  );
  // ship_total
  $(saveButton).closest('tr')
  .find('[field_var="ship_total"]').text(
    fixNum(
      'money', 
      $(saveButton).closest('tr')
        .find('[field_var="qty"]').val() 
      * $(saveButton).closest('tr')
        .find('[field_var="ship_price"]').val()
    )
  );
}

// subfunction for del- and addGoodline
function fixQtyInDropdown(optionToFix, newQty){
  const delim0Pos = $(optionToFix).text()
    .indexOf( $('#consts-block').attr('left_bracket') );
  const delim1Pos = $(optionToFix).text()
    .indexOf( $('#consts-block').attr('delim1') );
  if((delim0Pos != -1) && (delim0Pos != -1)){
    $(optionToFix).text(
      $(optionToFix).text().slice(0, delim0Pos)
      + $('#consts-block').attr('left_bracket')
      + fixNum('qty', newQty)
      + $(optionToFix).text().slice(delim1Pos)
    );
  };
};

function delGoodsLine(delButton) {
  const goodslinesTbody = $(delButton).closest('tbody');
  const inputsRow = $(goodslinesTbody).find('.goodslines-inputs-row');
  // use btn's parent to call refresh-money func.
  // because the button itself will be del.right now
  const rowToDel = $(delButton).closest('tr')
  const rowParent = $(rowToDel).parent(); 
  // copy texts|vals from row-to-del. to input's row 
  $(rowToDel).find('.save-val').each( function(){
    const varName = $(this).attr('field_var');
    if($(this).text()) {
      if(varName == 'human_id') {
        $(inputsRow).find('[field_var="' + varName + '"]')
          .text(
              $(this).text()
          );
      } else {
        $(inputsRow).find('[field_var="' + varName + '"]')
          .val(
            $(this).text()
          );
      };
    };
  });
  // copy shadow_ids for fields except material(has own procedure)
  $(rowToDel).find('.save-shadow').each( function(){
    const varName = $(this).attr('field_var');
    if(varName == 'material') return;
    $(inputsRow).find('[field_var="' + varName + '"]').attr(
      'shadow_id', 
      $(this).attr('shadow_id')
    );
  });
  // deal with material
  const inputMaterialField = $(inputsRow).find('[field_var="material"');
  const hotTransaction = $(inputsRow).closest('.tab-frame')
    .find('[hot_transaction]').attr('hot_transaction');
  const matShadowId = $(rowToDel).find('[field_var="material"')
    .attr('shadow_id');
  //  2 diff.cases for wide|thin materail's dropdowns
  if(   hotTransaction == $('#consts-block').attr('goods_to_prod_hot_id')
     || hotTransaction == $('#consts-block').attr('shipping_hot_id')
  ){
    // wide dropdown case: key is purchase_human_id
    // 
    // find appropr.option inside input's dropdown 
    const purchaseHumanId = $(rowToDel).find('[field_var="purchase_human_id"')
      .text().trim();
    const approprOption = $(inputMaterialField)
      .find('option[human_id="' + purchaseHumanId + '"]');
    // if the option found ok
    let newQty;
    if(approprOption.length){
      // correct qty
      newQty = 1 * $(approprOption).attr('qty') 
        + 1 * $(rowToDel).find('[field_var="qty"]').text().trim();
      $(approprOption).attr('qty', newQty);     // as an attr
      fixQtyInDropdown(approprOption, newQty);  // inside dropdown
      // "select" option
      $(inputMaterialField).val( $(approprOption).val() );
      //
    } else {
      // if no such material in the dropdown then add it
      newQty = $(rowToDel).find('[field_var="qty"]').text().trim();
      $(inputMaterialField).append(
        '<option'
        + ' shadow_id="' + matShadowId + '"'
        + ' human_id="' + purchaseHumanId + '"'
        + ' qty="' + newQty + '"'
        + '>'
        + $(rowToDel).find('[field_var="material"]').text().trim() + ' '
        + $('#consts-block').attr('left_bracket') + newQty
        + $('#consts-block').attr('delim1') //' по '
        + $(rowToDel).find('[field_var="price"]').text().trim()
        + ' #'
        + $(rowToDel).find('[field_var="purchase_human_id"]').text().trim()
        + $('#consts-block').attr('right_bracket')
        + '</option>'
      );
      // "select" option
      $(inputMaterialField).val( 
        $(inputMaterialField)
          .find('option[human_id="' + purchaseHumanId + '"]').val() 
      );
    };
  } else {
    // thin dropdown case: key is shadow_id
    //
    // find appropr.option inside input's dropdown 
    const approprOption = $(inputMaterialField)
      .find('option[shadow_id="' + matShadowId + '"]');
    // "select" the option
    $(inputMaterialField).val( $(approprOption).val() );
  };
  // remove the line and refresh total
  $(rowToDel).remove();
  refreshGoodslineTotals(delButton);
  refreshTransactionMoney(rowParent); 
}

function saveNewGoodsLine(saveButton) {
  const goodslinesTbody = $(saveButton).closest('tbody');
  const inputsRow = $(saveButton).closest('.goodslines-inputs-row');
  const inputMaterialField = $(inputsRow).find('[field_var="material"]');
  const inputQtyField = $(inputsRow).find('[field_var="qty"]');
  let selOption, restQty, spentQty, newOptionVal;
  //
  refreshGoodslineTotals(saveButton);
  // check if mand. fields are filled
  for(const field of $(inputsRow).find('.goodslines-never-empty')
  ){
    if(!field.value || field.value == 0) {
      field.focus();
      return;
    };
  };
  // check if store|stock spending is correct
  //  find selected option
  for(const option of $(inputMaterialField).find('option')){
    if( $(option).val() == $(inputMaterialField).val() ){
      selOption = option;
      break;
    };
  };
  const inputMaterialHumanId = $(selOption).attr('human_id');
  const inputMaterialQty = $(selOption).attr('qty');
  //  total qty must not be negative
  restQty = inputMaterialQty - $(inputQtyField).val();
  if(restQty < 0) {
    $(inputQtyField).select();
    return;
  }; 
  //  show new in-store|in-stock qty inside dropdown
  $(selOption).attr('qty', restQty);
  fixQtyInDropdown(selOption, restQty);
  // clone empty line and fill it
  const clonedRow = $(goodslinesTbody).find('.goodslines-dummy-row')
    .clone(true);
  $(clonedRow).removeClass('goodslines-dummy-row');
  // generate in input row human_id if empty
  let humanId;
  if(
    ! $(inputsRow).find('[field_var="human_id"]').text().trim()
  )
    $(inputsRow).find('[field_var="human_id"]').text( makeHumanId() )
  ;
  // copy input's vals to the created row
  $(clonedRow).find('*[field_var]').each( function(){
    let srcVal;
    const varName = $(this).attr('field_var');
    const srcField = $(inputsRow).find('*[field_var="' + varName  +'"]');
    srcVal = getValOrText($(srcField));
    // extra trim for material in stock|store-state dropdown
    if(varName == 'material') {
      const brackPos = srcVal.indexOf( $('#consts-block').attr('left_bracket') );
      srcVal = (brackPos == -1) ? srcVal : srcVal.slice(0, brackPos);
    };
    if(srcVal) $(this).text(srcVal);
    // copy shadow_ids if nessesary
    if( $(this).hasClass('save-shadow') )
      $(this).attr(
        'shadow_id', 
        getIdFromDropdown( $(srcField) )
      )
    ;
    // and clear used input
    if(varName == 'human_id') 
      $(srcField).text('')
    else
      $(srcField).val('')
    ;
  });
  // get selected material's humand_id and put it 
  // to fresh row as purchase_human_id
  $(clonedRow).find('[field_var="purchase_human_id"]').text(
    $(selOption).attr('human_id')
  );
  // reset totals in input's row(it's text(), not val())
  $(inputsRow).find('[field_var="total"]').text('');
  $(inputsRow).find('[field_var="ship_total"]').text('');
  // make the new line visible
  clonedRow.removeAttr('hidden').addClass("saved-row");
  // set del action
  clonedRow.find('.goodslines-input-del').on(
    'click',
    function() { 
      delGoodsLine($(this));
    }
  );
  // calc.where to insert new row
  const newHumanId = $(clonedRow).find('[field_var="human_id"]').text();
  let rowAfter = $(goodslinesTbody).find('.goodslines-dummy-row');
  for(const row of $(goodslinesTbody).find('.row-id-able')
    .not('.goodslines-dummy-row')
  ){
    const thisHumanId = $(row).find('[field_var="human_id"]').text().trim();
    if(thisHumanId > newHumanId) {
      rowAfter = row;
      break;
    };
  };
  // show fresh row
  clonedRow.insertBefore(rowAfter);
  // and calc.fresh total in main transaction
  refreshTransactionMoney(saveButton);
}

// special sidebar item(s) click
function wipeTransactionClick(){
  let selDates = [];
  for(const i of [1, 2]){
    selDates[i - 1] = $('#datepicker' + i).val();
    if(!selDates[i - 1]){
      $('#datepicker' + i).focus();
      return;
    };
  };
  if(selDates[1] < selDates[0]){
    $('#datepicker1').focus();
    return;
  };
  showYesNoScreen(
    () => { 
      loadTabPart(
        {
        'tab_action': 'kill',
        'tab_class' : 'packet',
        'tab_model' : 'transaction',
        'hot_transaction' : 1,
        'row_id'    : "0", 
        'sidebar_date1': selDates[0],
        'sidebar_date2': selDates[1],
        }, $()  // empty jquery obj.to get responce to
      );
    }, 
    {}, 
    ( $('#consts-block').attr('wipe_tr_alert1') 
      + selDates[0]
      + $('#consts-block').attr('wipe_tr_alert2') 
      + selDates[1]
      + $('#consts-block').attr('wipe_tr_alert3') 
    )
  );
}
 

