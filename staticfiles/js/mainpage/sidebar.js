// sidebar.js


$(document).ready(function() {

  loadDropdowns($('#sidebar'));

  // set sidebar menu click events
  $('.sidebar-menu-item').click(function() {
    // special call(s)
    if( $(this).is('#wipe-transactions') ) {
      wipeTransactionClick();
    // standard calls
    } else {
      loadFullTab({
        tab_class: $(this).attr('tab_class'),
        tab_model: $(this).attr('tab_model'),
        hot_transaction: $(this).attr('hot_transaction'),
        row_id: "0", 
      });
    };
  });

  // set dropdown 'search/x' click events
  $('.reset-dropdown-btn').click(function() {
    const searchSign = '&#128270;';  // &#8981;
    const xSign = '&#215;';
    if($(this).attr('dropdown_filtered') == '0') {
      // this is really click on magn.glass
      $(this).attr('dropdown_filtered', '1');
      // show x instead of magn.glass
      $(this).html(xSign);
      // show search instead of dropdown 
      $(this).closest('.input-group').find('.sidebar-dropdown-itself')
        .attr('hidden', true)
      $(this).closest('.input-group').find('.sidebar-dropdown-search')
        .removeAttr('hidden')
    } else {
      // this is click on x
      $(this).attr('dropdown_filtered', '0');
      // show magn.glass instead of x 
      $(this).html(searchSign);
      // form full dropdown
      $(this).closest('.input-group').find('.custom-select option')
        .each( function() {
         $(this).removeAttr('hidden')
      });
      // show dropdown instead of search 
      $(this).closest('.input-group').find('.sidebar-dropdown-itself')
        .removeAttr('hidden')
      $(this).closest('.input-group').find('.sidebar-dropdown-search')
        .attr('hidden', true)
      // show empty field
      $(this).closest('.input-group').find('.custom-select').val('');
    };
  });

  $('.filter-dropdown-btn').click(function() {
    kwords = $(this).parent().find('.filter-dropdown-input').val()
      .split(' ');
    if(kwords[0]) {
      // loop over dropdown items and hide those
      // which does not include all keywords
      $(this).closest('.input-group').find('.custom-select option')
        .each( function(){
        let isIn = true;
        for(const kword of kwords){
          if(!$(this).val().toLowerCase().includes(kword.toLowerCase())) {
            isIn = false;
            break;
          };
        };
        if(isIn)
          $(this).removeAttr('hidden')
        else
          $(this).attr('hidden', true)
        ;
      });
    };
    // hide search stuff and show dropdown
    $(this).closest('.input-group').find('.sidebar-dropdown-itself')
      .removeAttr('hidden')
    $(this).closest('.input-group').find('.sidebar-dropdown-search')
      .attr('hidden', true)
    // show 1st not-empty field
    $(this).closest('.input-group').find('.custom-select').val(
      $(this).closest('.input-group').find('.custom-select option')
        .not('[hidden]').first().val()
    );
  });
                      

  // some dropdowns cleaning 
  $('.sidebar-dropdown-select option').each(function() {
    if($(this).val().trim() == 'empty') 
      $(this).remove()
    ;
  });

  // test click
  $('#test_link').click(function() {
    testClick();
  });

});

