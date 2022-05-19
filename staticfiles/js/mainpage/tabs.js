// tabs.js

'use strict';

/*
 * set upper and bottom buttons actions
 */
jsFuncs['set_button_clicks'] = function(parentCont) {
  // close
  $(parentCont).find(' .close-btn')
    .on('click', '', function() {
      closeThisTab($(this));
    });
  // refresh
  $(parentCont).find(' .refresh-btn')
    .on('click', '', function() {
      refreshThisTab($(this));
    });
  // save
  $(parentCont).find(' .save-btn')
    .on('click', '', function() {
      saveThisTab($(this));
  });
  // del
  $(parentCont).find(' .del-btn')
    .on('click', '', function() {
      showYesNoScreen(delThisTab, $(this));
  });
}

/*
 * tab table specific actions
 *
 * set pensil button actions (click for jump to edit)
 */
jsFuncs['set_pensil_clicks'] = function(parentCont) {
  $(parentCont).find(' .is-pensil')
    .on('click', '', function() {
     editThisItem($(this));
  });
}
// or similar for x button in goodsline pivot table
// (in this case s/pensil/x/ )
jsFuncs['set_x_clicks'] = function(parentCont) {
  $(parentCont).find(' .is-pensil')
    .on('click', '', function() {
      delGoodsLine($(this));
  });
}
// correction for balance fields(d|k prefixes)
jsFuncs['dk_prefix'] = function(parentCont) {
  $(parentCont).find('.dk-prefix')
    .each(function() {
      const debPrefix = $('#consts-block').attr('deb_prefix');
      const credPrefix = $('#consts-block').attr('cred_prefix');
      const num = $(this).text().trim();
      $(this).text(
        (num == 0) ? fixNum( 'money', 0) : (
          (num < 0) ? ( 
            credPrefix + '  ' + fixNum( 'money', (-1) * num) 
          ) : (
            debPrefix + '  ' + num
          )
        )
      );
  });
}
// set clicks to filter partners by their balance value
jsFuncs['partners_filter_buttons'] = function(parentCont) {
  const trsToFilter = $(parentCont).closest('.tab-frame')
    .find('.tab-table tbody tr');
  $(parentCont).closest('.tab-frame').find('.partners-filter-btn')
    .on('click', '', function() {
      // for 'debitors'
      if($(this).hasClass('partners-filter-deb')){
      // show all the rows with balance > 0 and hide everything else
        $(trsToFilter).each(function(){
          if($(this).find('.balance-for-filter').text().trim() > 0) {
            if($(this).attr('hidden')) $(this).removeAttr('hidden');
          } else {
            $(this).attr('hidden', 'true')
          };
        });
      // for 'creditors'
      } else if($(this).hasClass('partners-filter-cred')){
      // show all the rows with balance < 0 and hide everything else
        $(trsToFilter).each(function(){
          if($(this).find('.balance-for-filter').text().trim() < 0) {
            if($(this).attr('hidden')) $(this).removeAttr('hidden');
          } else {
            $(this).attr('hidden', 'true')
          };
        });
      // show everything for 'all'
      } else {
        $(trsToFilter).each(function(){
          if($(this).attr('hidden')) $(this).removeAttr('hidden');
        });
      };
    }
  );
}

/*
 * set check and correction actions for quantity and money inputs
 */
jsFuncs['set_input_checks'] = function(parentCont) {
  // quantities
  $(parentCont).find('.qty-field')
    .on('change', '', function() {
      $(this).val(
        fixNum( 'qty', $(this).val() )
      );
  });
  // money
  $(parentCont).find('.money-field')
    .on('change', '', function() {
      $(this).val(
        fixNum( 'money', $(this).val() )
      );
  });
  // price
  $(parentCont).find('.price-field')
    .on('change', '', function() {
      $(this).val(
        fixNum( 'price', $(this).val() )
      );
  });
}

/*
 * set add extra-book-accounts-pair button action
 */
jsFuncs['set_add_acc_pair'] = function(parentCont) {
  // for transaction__edit add extra book accounts
  const tabName = $(parentCont).closest('*[tab_name]').attr('tab_name');
  $(parentCont).find('#add-extra-transaction')
    .on('click', function() {
      const clonedRow = $('#' + tabName +'-collapseme').clone(true);
      $(clonedRow).removeAttr('id');
      clonedRow.insertBefore('#' + tabName +'-collapse-rows-tail');
  });
}

/*
 * dropdown's postprocessing
 */
jsFuncs['del_dropdown_duplicates'] = function(parentCont) {
  // in dropdown's case parentCont is not really parent 
  // but span next to options, so we need to add parent()
  const selectedId = $(parentCont).parent().find('option[selected]')
    .attr('shadow_id');
  if(selectedId) { 
    $(parentCont).parent().find('option')
      .not('option[selected]').each( function() {
         if( $(this).attr('shadow_id') == selectedId )
            $(this).remove();
    });
  };
}

/*
 * set no_del_btn_if_new
 */
jsFuncs['no_del_btn_if_new'] = function(parentCont) {
  if($(parentCont).parent().find('*[row_id]').first().attr('row_id') == '0')
    $(parentCont).parents('.tab-frame').find('.del-btn').remove();
}

/*
 * set no_edit_btns_if_killed
 */
jsFuncs['no_edit_btns_if_killed'] = function(parentCont) {
  // if killed
  if($(parentCont).parent().find('*[tab_model]').first()
      .attr('tab_model') == 'killed_transaction'
  ) {
    $(parentCont).parents('.tab-frame').find('.del-btn,.save-btn').remove();
  };
}

/*
 * goodsline table's controls
 */
jsFuncs['goodslines_table_controls'] = function(parentCont) {
  //      init page with goodlines
  // make transaction total field grey instead of input
  const transactionMoneyField = $(parentCont).closest('.tab-table-cont')
    .find('*[field_var="money"]');
  const transactionMoneyParent = transactionMoneyField.parent()
  $(transactionMoneyField).remove();
  $(transactionMoneyParent).append(
    '<a href="#"'
    + ' class="money-field save-val never-empty"'
    + ' field_var="money"'
    + '>0</a>'
  );
  // calc.total from just added goodslines
  refreshTransactionMoney(transactionMoneyParent);
  //      end of init page with goodlines.
  // set copy price on any material dropdown's change
  $(parentCont).closest('.tab-table-cont')
      .find('.goodslines-inputs-row [field_var="material"]')
  .on('change', function() {
      //
      const leftDelim = $('#consts-block').attr('delim1');
      const rightDelim = $('#consts-block').attr('delim2');
      //
      const val = $(this).val();
      if(val){
        const startPos = val.indexOf(leftDelim);
        const endPos = val.indexOf(rightDelim);
        const price = (startPos == -1) ? '' : val.slice(
          startPos + leftDelim.length, endPos
        );
        if(price)
          $(parentCont).closest('.tab-table-cont')
            .find('.goodslines-inputs-row [field_var="price"]')
          .val(price)
        ;
      };
    }
  );

  // set compute total on any input field's change
  $(parentCont).closest('.tab-table-cont')
    .find('.goodslines-input')
  .on('change', function() {
      refreshGoodslineTotals($(this));
    }
  );

  // set reset inputs on click
  $(parentCont).closest('.tab-table-cont')
    .find('.goodslines-inputs-row [field_var="human_id"]')
  .on('click', function() {
      // reset all neighbor(input) elements
      $(parentCont).closest('.tab-table-cont')
        .find('.goodslines-inputs-row [field_var]')
      .each(function() {
        if( $(this).attr('field_var') == 'material' )
          $(this).val(
            $(this).find('option[html=""]')
          )
        else if( $(this).text() )
          $(this).text('')
        else
          $(this).val('')
        ;
      });
  });

  // set save btn action for new material line
  $(parentCont).closest('.tab-table-cont')
    .find('.goodslines-inputs-row .goodslines-inputs-save')
  .on('click', function() {
     saveNewGoodsLine($(this)); 
    }
  );

}

