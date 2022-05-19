# mainpage.py 

import re, time, datetime, decimal
from decimal import Decimal

from django.shortcuts import render 

from django.apps import AppConfig
from django.apps import apps

from django.db.models import Q, Sum

from django.db.models import Window, F
from django.db.models.functions import Lead

from django.views.generic import ListView
from django.views.generic import TemplateView 

from django.http import JsonResponse, Http404, HttpResponse
from django.template.loader import render_to_string

from .models import *
from .msgs import *
from .new_classes import *

import logging

class MainPage(ListView):
    template_name = 'mainpage/mainpage.html'
    queryset = ()

    def add_hot(self, args):
        res = list(args)
        return res

    def get_context_data(self, **kwargs):
        context = super(MainPage, self).get_context_data(**kwargs)
        for kword in (
            'brand',
            # yesno stuff
            'yesno_sure_question', 'yesno_no_answer', 'yesno_yes_answer',
            # sidebat stuff - begin
            'sidebar_from_date', 'sidebar_to_date',
        ):
            context[kword] = MSGS[kword][lc_id]
        # sidebar dropdown filters
        context['sidebar_dropdowns_zip'] = zip(
            (
                MSGS['sidebar_dropdown_hot_tr'][lc_id],
                MSGS['sidebar_dropdown_acc'][lc_id],
                MSGS['sidebar_dropdown_partner'][lc_id],
                MSGS['sidebar_dropdown_empl'][lc_id],
                MSGS['sidebar_dropdown_mat'][lc_id],
            ),
            ('hot_transaction', 'book_account', 'partner', 'employee', 'material')
        )
        # sidebar input filters
        context['sidebar_inputs_zip'] = zip(
            ( MSGS['sidebar_search_comm'][lc_id], ),
            ('comment',)
        )
        # sidebar (collaps.)menus
        sidemenu_level0 = (
            ('sidemenu_settings', '' ),
            ('sidemenu_analitics', '' ),
            ('sidemenu_trading', '' ), 
            ('sidemenu_production', '' ), 
            ('sidemenu_finance', '' ), 
            ('sidemenu_employees', '' ), 
            ('sidemenu_admin', 'b3admin' ), 
        )
        sidemenu_level1 = (
        (
            # HotTransaction, tab_model, tab_class, text, id
            ('hot_tr_service', 'transaction', 'new', '', ''), 
            ('', 'transaction', 'pivot', 'sidemenu_tr_log', ''), 
            ('', 'partner', 'pivot', 'sidemenu_partners_list', ''), 
            ('', 'partner', 'new', 'sidemenu_new_partner', ''), 
            ('', 'material', 'pivot', 'sidemenu_mat_list', ''), 
            ('', 'material', 'new', 'sidemenu_new_mat', ''), 
            ('', 'killed_transaction', 'pivot', 
                'sidemenu_killed_tr_log', ''
            ), 
        ),
        (
            ('', 'transaction', 'acc_sum_card', 
                'sidemenu_acc_sum_card', ''), 
            ('', 'goodsline', 'inventories', 'sidemenu_inventories', ''), 
            ('', 'goodsline', 'in_stock', 'sidemenu_in_stock', ''), 
            ('', 'partner', 'partners_balance', 
                'sidemenu_partners_balance', ''), 
            ('', 'goodsline', 'material_history', 
                'sidemenu_mat_history', ''
            ), 
            ('', 'book_account', 'trial_balance', 
                'sidemenu_trial_balance', ''
            ), 
        ),
        (
            ('hot_tr_shipping', 'transaction', 'new', '', ''),
            ('hot_tr_make_invoice', 'transaction', 'new', '', ''),
            ('hot_tr_get_invoice', 'transaction', 'new', '', ''),
        ),
        (
            ('hot_tr_mat_purchase', 'transaction', 'new', '', ''),
            ('hot_tr_mat_to_prod', 'transaction', 'new', '', ''),
            ('hot_tr_consumable_purchase', 'transaction', 'new', '', ''),
            ('hot_tr_to_stock', 'transaction', 'new', '', ''),
        ),
        (
            ('hot_tr_cache_in', 'transaction', 'new', '', ''),
            ('hot_tr_cache_out', 'transaction', 'new', '', ''),
            ('hot_tr_to_bank', 'transaction', 'new', '', ''),
            ('hot_tr_from_bank', 'transaction', 'new', '', ''),
        ),
        (
            ('hot_tr_calc_salary', 'transaction', 'new', '', ''),
            ('hot_tr_pay_salary', 'transaction', 'new', '', ''),
            ('hot_tr_accountable_cache_out', 'transaction', 'new', '', ''),
            ('hot_tr_accountable_cache_return', 'transaction', 'new', '', ''),
            ('hot_tr_accountable_cache_spent', 'transaction', 'new', '', ''),
        ),
        (
            ('', '', '', 'sidemenu_wipe_tr', 'wipe-transactions'),
        ),
        )
        #
        context['sidebar_collmenus'] = []
        for lvl0_pair, lvl1_lines in zip(sidemenu_level0, sidemenu_level1):
            # check if current user is allowed to see the item
            try:
                if lvl0_pair[1] and lvl0_pair[1] != str(
                        CustomUser.objects.get(id=self.request.user.id)
                ):
                    continue
            except:
                continue
            lvl1_fixed_lines = []
            for line in lvl1_lines:
                lvl1_fixed_lines.append(
                    [
                        MSGS[line[0]][lc_id],   # name
                        line[1],                # tab_model 
                        line[2],                # tab_class 
                        HotTransaction.objects.get(name_id=line[0]).id, # h.tr.
                        line[4],                # id
                    ] if line[0] else [
                        MSGS[line[3]][lc_id],
                        line[1], 
                        line[2], 
                        1,
                        line[4],
                    ]
                )
            context['sidebar_collmenus'].append([
                # [ symb.id, name ]
                [ lvl0_pair[0], MSGS[lvl0_pair[0]][lc_id], ],   
                lvl1_fixed_lines    
            ])
        #  const.'s block 
        context['consts'] = (
            ('goods_to_prod_hot_id', GOODS_TO_PROD_HOT_ID ), 
            ('shipping_hot_id', SHIPPING_HOT_ID ), 
            ('left_bracket', '[' ), 
            ('right_bracket', ']' ),
            ('delim1', MSGS['dropdown_goodsline_by'][lc_id] ),
            ('delim2', ':' ),
            ('wipe_tr_alert1', MSGS['wipe_tr_alert1'][lc_id] ),
            ('wipe_tr_alert2', MSGS['wipe_tr_alert2'][lc_id] ),
            ('wipe_tr_alert3', MSGS['wipe_tr_alert3'][lc_id] ),
            ('deb_prefix', MSGS['deb_prefix'][lc_id] ),
            ('cred_prefix', MSGS['cred_prefix'][lc_id] ),
        )
        #
        return context


