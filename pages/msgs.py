# msgs.py

# locale's id
ENG = 0
lc_id = ENG
# msgs
MSGS = {
    'brand': (
        'BasicFur - production, inventories, stock', 
    ),
    # partner group names
    'partner_gr_nogroup': ('Beyond groups',  ),
    'partner_gr_employees': ('Employees',  ),
    # book account names
    'bacc_00':      ('Service', ),
    'bacc_05':      ('Inventories', ),
    'bacc_06':      ('Consumables', ),
    'bacc_20':      ('Production', ),
    'bacc_41':      ('Stock', ),
    'bacc_46':      ('Shipping', ),
    'bacc_51':      ('Bank account', ),
    'bacc_62':      ('Partners', ),
    'bacc_50/1':    ('Cash', ),
    'bacc_71':      ('Salaries', ),
    'bacc_72/1':    ('Petty cash', ),
    'bacc_80':      ('Profit', ),
    'bacc_80/1':    ('Owner1', ),
    # hot transaction names
    'hot_tr_service': ('Srv.transaction', ),
    'hot_tr_shipping': ('Shipping', ),
    'hot_tr_mat_to_prod': ('Mater.to production', ),
    'hot_tr_get_invoice': ('Get invoice',  ),
    'hot_tr_make_invoice': ('Make invoice',  ),
    'hot_tr_from_bank': ('Transf.from account',  ),
    'hot_tr_to_bank': ('Transf.to account',  ),
    'hot_tr_to_stock': ('Prod.to stock', ),
    'hot_tr_consumable_purchase': ('Purch.of consumable', ),
    'hot_tr_mat_purchase': ('Buy goods/svc', ),
    'hot_tr_pay_salary': ('Pay salary',  ),
    'hot_tr_calc_salary': ('Calc.salary', ),
    'hot_tr_accountable_cache_out': ('Accountable cache out', ),
    'hot_tr_accountable_cache_return': ('Accountable cache return', ),
    'hot_tr_accountable_cache_spent': ('Accountable cache spent', ),
    'hot_tr_cache_out': ('Cash out', ),
    'hot_tr_cache_in': ('Cash in', ),
    'hot_tr_empty': ('empty', ),
    # tab titles
    'title_partner__pivot': (
        ('Partners', ), # title itself
        'frame_pivot',                             # frame template name
    ),
    'title_partner__edit': (
        ('Partner', ),
        'frame_edit',
    ),
    'title_partner__new': (
        ('New partner', ),
        'frame_edit',
    ),
    'title_material__pivot': (
        ('Materials', ), 
        'frame_pivot',                                 
    ),
    'title_material__edit': (
        ('Material', ),
        'frame_edit',
    ),
    'title_material__new': (
        ('New material', ),
        'frame_edit',
    ),
    'title_transaction__pivot': (
        ('Transactions log',  ), 
        'frame_pivot',                                 
    ),
    'title_transaction__edit': (
        ('Transaction',  ),
        'frame_edit',
    ),
    'title_transaction__new': (
        ('New transaction',  ),
        'frame_edit',
    ),
    'title_killed_transaction__pivot': (
        ('Deleted transactions',  ), 
        'frame_pivot',                                 
    ),
    'title_killed_transaction__edit': (
        ('Deleted transaction',  ),
        'frame_edit',
    ),
    'title_goodsline__pivot': (
        ('', ), 
        'frame_edit',                                 
    ),
    'title_goodsline__material_history': (
        ('Material\'s history',  ), 
        'frame_pivot',                                 
    ),
    'title_goodsline__inventories': (
        ('Inventories',  ), 
        'frame_pivot',                                 
    ),
    'title_goodsline__in_stock': (
        ('In stock',  ), 
        'frame_pivot',                                 
    ),
    'title_goodsline__in_stock': (
        ('In stock',  ), 
        'frame_pivot',                                 
    ),
    'title_transaction__acc_sum_card': (
        ('Account\'s summary card',  ), 
        'frame_pivot',                                 
    ),
    'title_partner__partners_balance': (
        ('Balance by partners', ), 
        'frame_pivot',                                 
    ),
    'title_transaction__partners_balance': (
        ('Balance by partner',  ), 
        'frame_pivot',                                 
    ),
    'title_book_account__trial_balance': (
        ('Trial balance',  ), 
        'frame_pivot',                                 
    ),
    # yes-no page
    'yesno_sure_question': ('Are you sure?',  ),
    'yesno_no_answer': ('No, cansel',  ),
    'yesno_yes_answer': ('Yes, continue',  ),
    'wipe_tr_alert': (
        'Caution! This will completely wipe all transactions for selected period, including deleted!', 
    ),
    'wipe_tr_alert1': (
        'Caution! This will completely wipe all transactions from ', 
    ),
    'wipe_tr_alert2': (
        ' to ', 
    ),
    'wipe_tr_alert3': (
        ' including deleted!', 
    ),
    # common frame buttons
    'btn_f5': ('Reload',  ),
    'btn_add': ('Add',  ),
    'btn_close': ('Close',  ),
    'btn_close_no_save': ('Close w/o save',  ),
    'btn_delete': ('Delete', 'Удалить', ),
    'btn_save_close_tr': ('Save and close',  ),
    'btn_save_close': ('Save and close',  ),
    'btn_add_goodsline': ('Add',  ),
    'subtitle_add_goodsline': ('Add line:',  ),
    # sidebar items
    'sidebar_from_date': ('from',  ),
    'sidebar_to_date': ('to',  ),
    'sidebar_dropdown_hot_tr': ('Type',  ),
    'sidebar_dropdown_acc': ('Acc.',  ),
    'sidebar_dropdown_partner': ('Partn.',  ),
    'sidebar_dropdown_empl': ('Empl.',  ),
    'sidebar_dropdown_mat': ('Mater.',  ),
    'sidebar_search_comm': ('Cmnt',  ),
    'sidemenu_settings': ('Settings',  ),
    'sidemenu_analitics': ('Analitics',  ),
    'sidemenu_trading': ('Trading',  ),
    'sidemenu_production': ('Production', ),
    'sidemenu_finance': ('Finance',  ),
    'sidemenu_employees': ('Employees', ),
    'sidemenu_tr_log': ('Transactions log',  ),
    'sidemenu_partners_list': ('Parnters list',  ),
    'sidemenu_new_partner': ('New partner',  ),
    'sidemenu_mat_list': ('Materials list',  ),
    'sidemenu_new_mat': ('New material',  ),
    'sidemenu_killed_tr_log': ('Del.transations log', ),
    'sidemenu_acc_sum_card': ('Acc.summary card',  ),
    'sidemenu_inventories': ('Inventories',  ),
    'sidemenu_in_stock': ('In stock',  ),
    'sidemenu_partners_balance': ('Balance by partners',  ),
    'sidemenu_mat_history': ('Material\'s history',  ),
    'sidemenu_trial_balance': ('Trial balance',  ),
    'sidemenu_admin': ('Admin.tasks',  ),
    'sidemenu_wipe_tr': ('Wipe transactions',  ),
    # pivot and pivot-like table headers
    'pivot_parter_name1': ('Name', ),
    'pivot_parter_name2': ('Name2', ),
    'pivot_parter_group': ('In group', ),
    'pivot_mat_name': ('Name', ),
    'pivot_tr_human_id': ('ID', ),
    'pivot_tr_date': ('Op.date', ),            
    'pivot_tr_partner': ('Partner', ),        
    'pivot_tr_hot_transaction': ('Trans.type', ), 
    'pivot_tr_deb_account': ('DebAcc', ),  
    'pivot_tr_cred_account': ('CredAcc', ),
    'pivot_tr_money': ('Sum', ),          
    'pivot_tr_comment': ('Comment', ),       
    'pivot_killed_tr_killdate': ('Del.date', ),       
    'pivot_goodsln_human_id': ('ID', ),       
    'pivot_goodsln_name': ('Name', ),
    'pivot_goodsln_comment': ('Comment', ),       
    'pivot_goodsln_qty': ('Quantity', ),       
    'pivot_goodsln_price': ('Price', ),       
    'pivot_goodsln_total': ('Cost', ),       
    'pivot_goodsln_ship_price': ('Sell.price', ),       
    'pivot_goodsln_ship_total': ('Sell.cost', ),       
    'partners_balance_partner_name': ('Name', ),
    'partners_balance_partner_balance': ('Balance', ),
    'partners_balance_partner_deb_sum': ('Debit', ),
    'partners_balance_partner_cred_sum': ('Credit', ),
    'partners_balance_partner_debtors': ('Debtors', ),
    'partners_balance_partner_creditors': ('Creditors', ),
    'partners_balance_partner_all': ('All', ),
    'partners_balance_tr_partner': ('Partner', ),        
    'partners_balance_tr_human_id': ('ID', ),        
    'partners_balance_tr_date': ('Op.date', ),            
    'partners_balance_tr_deb_sum': ('Debit', ),
    'partners_balance_tr_cred_sum': ('Credit', ),
    'partners_balance_tr_hot_tr': ('Trans.type', ), 
    'mat_hist_mat': ('Material', ),        
    'mat_hist_root_human_id': ('ID', ),        
    'mat_hist_date': ('Op.date', ),            
    'mat_hist_partner': ('Partner', ),        
    'mat_hist_hot_tr': ('Trans.type', ), 
    'mat_hist_comment': ('Comment', ),       
    'mat_hist_qty': ('Quantity', ),       
    'mat_hist_price': ('Price', ),       
    'mat_hist_human_id': ('Detail ID', ),        
    'inventories_mat': ('Material', ),        
    'inventories_qty': ('Quantity', ),       
    'inventories_price': ('Price', ),       
    'trial_balance_name': ('Account', ), 
    'trial_balance_deb_sum': ('Debit', ),
    'trial_balance_cred_sum': ('Credit', ),
    'trial_balance_date_range': ('Date range: ', ),
    'trial_balance_balance_before': ('Balance before:', ),
    'trial_balance_balance_during': ('Balance during:', ),
    'trial_balance_balance_after': ('Balance after:', ),
    'trial_balance_total': ('Total', ),
    'acc_sum_card_human_id': ('ID', ),        
    'acc_sum_card_date': ('Op.date', ),            
    'acc_sum_card_partner': ('Partner', ),        
    'acc_sum_card_hot_tr': ('Trans.type', ), 
    'acc_sum_card_comment': ('Comment', ),       
    'acc_sum_card_deb_sum': ('Debit', ),
    'acc_sum_card_cred_sum': ('Credit', ),
    'acc_sum_card_balance': ('Balance', ),
    'acc_sum_card_acc_header': ('Account:', ),
    'acc_sum_card_start_bal_header': ('Start balance:', ),
    'acc_sum_card_total': ('Total:', ),
    'dropdown_goodsline_by': (' by ', ),     
    # edit and edit-like table headers
    'edit_partner_name': ('Name', ),        
    'edit_partner_name2': ('Name2', ),        
    'edit_partner_in_group': ('Is in group', ),        
    'edit_mat_name': ('Name', ),        
    'edit_tr_human_id': ('ID:', ),
    'edit_tr_date': ('Date:', ),            
    'edit_tr_partner': ('Partner:', ),        
    'edit_tr_hot_transaction': ('Trans.type:', ), 
    'edit_tr_money': ('Sum:', ),          
    'edit_tr_comment': ('Comment:', ),       
    'edit_tr_deb_account': ('Deb.Accnt.:', ),  
    'edit_tr_cred_account': ('Cred.Accnt.:', ),
    'edit_tr_has_goodslines': ('Cont.goods', ),   
    'edit_tr_create_date': ('Chng.date', ),     
    'edit_tr_created_by': ('Chng.by', ),     
    'edit_tr_employee': ('Employee:', ),     
    'edit_tr_details': ('Details...', ),     
    'edit_tr_add_acc': ('Add acc.', ),     
    'edit_tr_kill_date': ('Del.date', ),     
    'edit_tr_killed_by': ('Del.by', ),     
    # dk_prefix
    'deb_prefix': ('D', ),     
    'cred_prefix': ('C', ),     
}

