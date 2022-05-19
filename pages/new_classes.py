#new_classes.py

import re, time, datetime, decimal, copy
from decimal import Decimal
from datetime import date, datetime
from django.utils import timezone

from django.shortcuts import render 

from django.apps import AppConfig
from django.apps import apps

from django.db.models import Q, Sum
from django.db.models import Window, F
from django.db.models.functions import Lead

from django.views.generic import ListView
from django.views.generic import TemplateView 

from django.http import JsonResponse, Http404, HttpResponse, HttpRequest
from django.template.loader import render_to_string

from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator

from users.models import CustomUser
from .models import *
from pages.msgs import *

# for debug
import logging
import json
#from django.views.decorators.http import require_POST

## cross-visible view parts
from .mainpage  import *    # for some consts

#current_tz = timezone.get_current_timezone()

# some globals

TABS_TEMPLATES_DIR = 'mainpage/tabs'
HEADER_TEMPLATE_FILENAME = 'header.html'

OK_EMPTY_RESPONSE = ''
OK_SAVE_RESPONSE = 'done'

# check default model obj's set
for cls in ( 
    CustomUser, BookAccount, HotTransaction, PartnerGroup, Partner
):
    cls.check_defaults()

# consts
EMPLOYEES_GROUP = PartnerGroup.objects.get(name_id='partner_gr_employees')
GOODS_TO_PROD_HOT_ID = HotTransaction.objects.get(
    name_id='hot_tr_mat_to_prod').id
SHIPPING_HOT_ID = HotTransaction.objects.get(name_id='hot_tr_shipping').id
EMPTY_HOT_ID = HotTransaction.objects.get(name_id='hot_tr_empty').id
SHIPPING_ACC_PAIR_OBJS = []
SHIPPING_ACC_PAIR_NAMES = [] 
SHIPPING_ACC_PAIR_IDS = []
for short_names_pair in ( 
    ('62', '46'), ('46', '41'), ('46', '80'), 
):
    SHIPPING_ACC_PAIR_OBJS.append([
        BookAccount.objects.get(short_name=short_names_pair[0]),
        BookAccount.objects.get(short_name=short_names_pair[1]),
    ])
    SHIPPING_ACC_PAIR_NAMES.append([
        BookAccount.objects.get(short_name=short_names_pair[0]).name,
        BookAccount.objects.get(short_name=short_names_pair[1]).name,
    ])
    SHIPPING_ACC_PAIR_IDS.append([
        str(BookAccount.objects.get(short_name=short_names_pair[0]).id),
        str(BookAccount.objects.get(short_name=short_names_pair[1]).id),
    ])
SHIPPING_ACC_PAIRS_ZIP=zip(SHIPPING_ACC_PAIR_OBJS, SHIPPING_ACC_PAIR_IDS)
INVENTORIES_ACCOUNT = BookAccount.objects.get(short_name='05')
STOCK_ACCOUNT = BookAccount.objects.get(short_name='41')
STOCK_SISTER_ACCOUNT = BookAccount.objects.get(short_name='46')
PARTNERS_ACCOUNT = BookAccount.objects.get(short_name='62')

# prefix for deleted-objs model
killed_model_prefix = 'Killed'


################################################################

"""
Some subsidiary functions
"""

def arr_x_masks(arr, *mask_arrs):
    empty_val = ''  # rewrite if ness.
    res = arr
    for mask_arr in mask_arrs:
        res = [
            i if mask else empty_val for i, mask in zip(res, mask_arr)
        ]
    res = set(res)
    res.discard(empty_val)
    return list(res)
                                
def anything_to_decimal(n):
    return Decimal(
        n if n else 0
    )

def check_ajax_request(request):
    if request.is_ajax() and request.method == 'POST':
        return True
    else:
        raise Http404
        return None

def make_int_human_id():
    return int( (
                    datetime.now().timestamp()
                    - datetime(2021,1,1,0,0).timestamp() 
                ) * 10
    )
        #('0000000000' + str(
        #))[-10:]

def val_is_pk(model_inst, var_name):
    return True if (
            str(
                model_inst.__class__._meta.get_field(var_name).__class__
            ).rsplit('.')[-1].rsplit("'")[0]
         == 'ForeignKey'
    ) else False

def db_get_val_or_shadow(model_inst, var_name):
    if val_is_pk(model_inst, var_name):
        res = getattr(model_inst, var_name).id 
    else: 
        res = getattr(model_inst, var_name)
    # ship_price field: '' for show and 0 for save
    if (var_name == 'ship_price' and not res): res = ''
    return str(res)

def db_put_val_or_shadow(model_inst, var_name, val):
    if val_is_pk(model_inst, var_name):
        setattr(model_inst, var_name, 
            model_inst.__class__._meta.get_field(var_name
            ).related_model.objects.get(id=str(val))
        ) 
    # ship_price field: '' for show and 0 for save
    elif var_name == 'ship_price' and val == '':
        setattr(model_inst, var_name, Decimal(0.00))
    elif var_name == 'date':
        # correct date by upper|lower limit
        if datetime.strptime(val, '%Y-%m-%d').date() > datetime.now().date():
            val = datetime.now().strftime("%Y-%m-%d")
        elif datetime.strptime(val, '%Y-%m-%d').date() < datetime(
            2021, 1, 1
        ).date(): 
            val = datetime(2021, 1, 1).strftime("%Y-%m-%d")
        setattr(model_inst, 'date', val)
    else:
        setattr(model_inst, var_name, val)

def get_tab_title(tab_class, tab_model):
    try:
        return MSGS['title_' + tab_model + '__' + tab_class][0][lc_id]
    except:
        return '' 

def get_frame_template_name(tab_class, tab_model):
    try:
        return MSGS['title_' + tab_model + '__' + tab_class][1]
    except:
        return '' 

def fix_employee_val(tab_obj):
    # special check for employee's field 
    # (for example for not employees-only transaction it's empty by default)
    #   if employee's not selected set it's same as partner
    try:
        employee = tab_obj.req_post['employee']
    except:
        employee = ''
    if not employee: 
        # and now for employees-only transaction.
        # if employee's not in their group then return false
        if (
            HotTransaction.objects.get(id=tab_obj.req_post['hot_transaction'])
                .is_employees_action != 0 
            and
            Partner.objects.get(id=tab_obj.req_post['partner'])
                .partner_group != EMPLOYEES_GROUP 
        ):
            return False
    return True


################################################################

#### Classes ####

#@method_decorator(never_cache, name='as_view')
class AsViewContainer(object):

    def req_to_db(self):
        pass

    def make_context(self, **kwargs):
        pass

    def context_to_html(self):
        return render_to_string(self.template, self.context)

    # extra args will be mand.on goodsline's creation
    def make_html_resp(self, request, req_post_apart = '', root_transaction = ''):
        self.request = request
        self.req_post = req_post_apart if req_post_apart else self.request.POST
        self.root_transaction = root_transaction
        self.context = {}
        self.req_to_db()
        self.make_context()
        return self.context_to_html()

    def make_json_resp(self, request):
        if check_ajax_request(request) is None:
            return ''
        return JsonResponse({
            'html_in_json': 
            self.make_html_resp(request)
        })

    @classmethod
    def as_view(cls):
        tab_piece =cls()
        return tab_piece.make_json_resp

    @classmethod
    def as_html(cls):
        tab_piece = cls()
        return tab_piece.make_html_resp


# Base for building any tab part
#
class TabBase(object):

    def make_context(self, **kwargs):
        # start context with some very common fields important for any tab part 
        for var_name in (
            'tab_action',
            'tab_class',
            'tab_model',
            'hot_transaction',
            'root_transaction',
        ):
            val = self.request.POST.get(var_name)
            self.context.update({
                var_name: val if val else ''
            })
        self.context['tab_name'] = ( self.context['tab_class']
            + '__' + self.context['tab_model']
        )
        self.context['tab_title'] = get_tab_title(
            self.context['tab_class'], self.context['tab_model']
        )
        # js to run after the tab's loading, set empty by default
        self.context['run_on_load'] = ''


# frame and header
#
class ShownFrame(TabBase, AsViewContainer):

    def __init__(self):
        super().__init__()
        
    def make_context(self, **kwargs):
        # make basic context
        TabBase.make_context(self, **kwargs)
        # add frame-level vals
        self.context['run_on_load'] += ' set_button_clicks'
        # localized names
        for btn_id in (
            'btn_f5',
            'btn_add',
            'btn_close',
            'btn_delete',
            'btn_save_close_tr',
            'btn_save_close',
            'btn_close_no_save',
        ):
            self.context[btn_id] = MSGS[btn_id][lc_id]
        # not in init because of context's tab_class usage
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + get_frame_template_name(
                self.context['tab_class'], self.context['tab_model']
            ) + '.html'
        )

    def context_to_html(self):
        return render_to_string(self.template, self.context)


class ShownHeader(TabBase, AsViewContainer):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/header.html'

    def make_context(self, **kwargs):
        # make basic context
        TabBase.make_context(self, **kwargs)

    def context_to_html(self):
        return render_to_string(self.template, self.context)


# for showing table parts

# cell-family classes
#
class Cell(object):

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_std.html'

    def make_context(self, **kwargs):
        # as it's not tab-level class make context without tab-base-vars
        self.context = {}
        # parse cell-level kwargs pairs
        for var_name, val in kwargs.items():
            self.context.update({ var_name: val })

    def calc_val_and_shadow(self):
        if not self.context['var_name']:
            val = ''
        # for correct localized names in dropdowns
        elif (self.context['var_name'] == 'name'
            and (   self.context['row_inst'].__class__ == HotTransaction
                or  self.context['row_inst'].__class__ == BookAccount
                or  self.context['row_inst'].__class__ == PartnerGroup
            )
        ):
            val = self.context['row_inst']
        else:
            val = getattr(
                self.context['row_inst'], self.context['var_name']
            ) 
        if val:
            # N.B. rewrite dates(for picker default and others)
            if self.context['var_name'] == 'date':
                val = val.strftime("%Y-%m-%d")
            elif (
                    self.context['var_name'] == 'create_date'
                or  self.context['var_name'] == 'kill_date'
            ):
                val = val.strftime("%d %b %H:%M")
            # add shadow id where it's nessesary
            if self.context['show_shadow_flag']:
                if val_is_pk(
                        self.context['row_inst'], self.context['var_name']
                ):
                    self.context['shadow_id'] = val.id 
                else:
                    # inside dropdown
                    self.context['shadow_id'] = getattr(
                        self.context['row_inst'], 'id'
                    )
        self.context['val'] = val

    def context_to_html(self):
        self.calc_val_and_shadow()
        return render_to_string(self.template, self.context)


class CellPivotGoodsline(Cell):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_pivot_goodsline.html'


class CellPivotGoodslineDummy(CellPivotGoodsline):

    def __init__(self):
        super().__init__()
    
    # make all cell vals empty for dummy row
    def calc_val_and_shadow(self):
        val = ''
        self.context['val'] = val


class CellPivotMovesGoodsline(Cell):

    def __init__(self):
        super().__init__()
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + 'cell_material_history_goodsline.html'
        )

    def calc_val_and_shadow(self):
        # catch special vars(transaction-related, not goodsmove-)
        if self.context['var_name'] == 'root_human_id':
            self.context['val'] = self.context[
                'row_inst'
            ].root_transaction.human_id
        elif self.context['var_name'] == 'date':
            self.context['val'] = self.context[
                'row_inst'
            ].root_transaction.date.strftime("%Y-%m-%d") 
        elif self.context['var_name'] in (
            'partner', 'hot_transaction', 'comment',
        ):
            self.context['val'] = getattr(
                self.context['row_inst'].root_transaction,
                self.context['var_name']
            )
        # or use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)
        # special extra attr.for pensil to goto root transaction
        if self.context['var_name'] == '':
            self.context['root_transaction_id'] = self.context[
                'row_inst'
            ].root_transaction.id
            self.context['root_hot_transaction_id'] = self.context[
                'row_inst'
            ].root_transaction.hot_transaction.id


class CellPivotStoreGoodsline(Cell):

    def __init__(self):
        super().__init__()
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + 'cell_inventories_goodsline.html'
        )

    def calc_val_and_shadow(self):
        # catch special row-level vars
        if self.context['var_name'] == 'qty':
            self.context['val'] = self.context['line_qty']
        elif self.context['var_name'] in ('date', 'partner', 'human_id'):
            self.context['val'] = getattr(
                self.context['row_inst'].root_transaction,
                self.context['var_name'] 
            )
        # or use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)


class CellPivotAccSummary(Cell):

    def __init__(self):
        super().__init__()

    def calc_val_and_shadow(self):
        # if it's money field in deb|cred column
        if self.context['var_name'] in (
            'deb_money', 'cred_money', 'balance'
#           'hot_transaction', 'deb_money', 'cred_money', 'balance'
        ):
            self.context['val'] = str(self.context[
                self.context['var_name']
            ])
        # else use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)


class CellPivotBalancesPartner(Cell):

    def __init__(self):
        super().__init__()
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + 'cell_partners_balance_partner.html'
        )

    def calc_val_and_shadow(self):
        if self.context['var_name'] in (
            'deb_money', 'cred_money', 'balance'
        ):
            self.context['val'] = str(self.context[
                self.context['var_name']
            ])
        # else use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)


class CellPivotBalancesTransaction(Cell):

    def __init__(self):
        super().__init__()

    def calc_val_and_shadow(self):
        if self.context['var_name'] == 'deb_money':
            if self.context['row_inst'].deb_account == PARTNERS_ACCOUNT:
                self.context['val'] = str(self.context['row_inst'].money)
            else:
                self.context['val'] = ''
        elif self.context['var_name'] == 'cred_money':
            if self.context['row_inst'].cred_account == PARTNERS_ACCOUNT:
                self.context['val'] = str(self.context['row_inst'].money)
            else:
                self.context['val'] = ''
        # else use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)


class CellTrialBalanceBookAccount(Cell):

    def __init__(self):
        super().__init__()

    def calc_val_and_shadow(self):
        if self.context['var_name'] in ('name', '', ):
            Cell.calc_val_and_shadow(self)
            return
        val = Decimal(0.00)
        if self.context['var_name'] == 'deb_before':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_before'
                        ].filter(deb_account=self.context['row_inst']
                    )
            ])
        elif self.context['var_name'] == 'cred_before':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_before'
                        ].filter(cred_account=self.context['row_inst']
                    )
            ])
        elif self.context['var_name'] == 'deb_during':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_during'
                        ].filter(deb_account=self.context['row_inst']
                    )
            ])
        elif self.context['var_name'] == 'cred_during':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_during'
                        ].filter(cred_account=self.context['row_inst']
                    )
            ])
        elif self.context['var_name'] == 'deb_to_date':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_to_date'
                        ].filter(deb_account=self.context['row_inst']
                    )
            ])
        elif self.context['var_name'] == 'cred_to_date':
            self.context['val']= sum([ 
                    transaction.money 
                    for transaction in self.context[
                            'transactions_to_date'
                        ].filter(cred_account=self.context['row_inst']
                    )
            ])


class CellDropdownStoreGoodsline(CellPivotStoreGoodsline):

    def __init__(self):
        super().__init__()
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + 'cell_dropdown_store_goodsline.html'
        )


    def calc_val_and_shadow(self):
        # add to context an extra localized word
        self.context['delim1'] = MSGS['dropdown_goodsline_by'][lc_id] 
        # catch special row-level vars
        if self.context['var_name'] == 'qty':
            self.context['val'] = self.context['line_qty']
#       elif self.context['var_name'] in ('date', 'partner', 'human_id'):
        elif self.context['var_name'] in ('date', 'partner'):
            self.context['val'] = getattr(
                self.context['row_inst'].root_transaction,
                self.context['var_name'] 
            )
        # or use regular goodsmove's vars
        else:
            Cell.calc_val_and_shadow(self)


class CellEdit(Cell):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_edit_std.html'


class CellEditTransaction(Cell):

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_edit_transaction.html'


class CellNew(CellEdit):

    def __init__(self):
        super().__init__()

    def calc_val_and_shadow(self):
        # catch special var(s)
        if self.context['var_name'] == 'partner_group':
            self.context['val'] = MSGS['partner_gr_nogroup'][lc_id]
            self.context['shadow_id'] = PartnerGroup.objects.get(
                name_id='partner_gr_nogroup').id
        else:
            Cell.calc_val_and_shadow(self)


class CellNewTransaction(CellNew):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_edit_transaction.html'

    def calc_val_and_shadow(self):
        self.context['val'] = ''
        self.context['shadow_id'] = ''
        # set default vals where it can be done
        if self.context['var_name'] == 'date':
            # generate date from current
            self.context['val'] = datetime.now().strftime("%Y-%m-%d")
        elif self.context['var_name'] == 'human_id':
            # generate human_id
            self.context['val'] = make_int_human_id()
        elif self.context['var_name'] == 'hot_transaction':
            hot_trans = HotTransaction.objects.get(
                id=self.context['hot_transaction']
            )
            self.context['val'] = hot_trans
            self.context['shadow_id'] = hot_trans.id
        elif self.context['var_name'] == 'has_goodslines':
            self.context['val'] = HotTransaction.objects.get(
                id=self.context['hot_transaction']
            ).has_goodslines
        # book accounts in new transaction case should be set 
        # from db defaults depending on hot transaction
        elif self.context['var_name'] in (
                'deb_account', 
                'cred_account',
        ):
            book_acc = BookAccount.objects.get(
                id=getattr( 
                    HotTransaction.objects.get(
                        id=self.context['hot_transaction']
                    ),
                    self.context['var_name']
                ).id
            )
            # get value and shadow_id
            self.context['val'] = book_acc
            self.context['shadow_id'] = book_acc.id


class CellNewGoodsline(CellNew):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_new_goodsline.html'

    def calc_val_and_shadow(self):
        self.context['val'] = ''
        self.context['shadow_id'] = ''
        self.context['btn_add_goodsline']= MSGS[
            'btn_add_goodsline'
        ][lc_id]


class CellDropdown(Cell):               # slightly diff.

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'cell_dropdown.html'


# row-family classes
#
class Row(object):

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_std.html'

    def make_context(self, **kwargs):
        # as it's not tab-level class make context without tab-base-vars
        self.context = {}
        # parse kwargs pairs
        for var_name, val in kwargs.items():
            self.context.update({ var_name: val })
        # class to make cell obj., to rewrite in some cases
        self.context['cell_making_class'] = Cell

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        return True

    # extra in-context_to_html method
    def extra_context_upd(self):
        pass

    def context_to_html(self):
        # make array of individual cell's htmls
        self.context['cells_arr'] = []
        # iterate over cells
        for idx_arr in zip(
            self.context['var_names'],
            self.context['extra_classes'],
            self.context['is_pensil_flags'],
            self.context['is_input_flags'],
            self.context['show_shadow_flags'],
            self.context['is_short_val_flags'],
        ):
            # make kwargs dict for current cell obj.
            kwargs = {}
            # add cell-level var:vals 
            for var_name, idx_item in zip(
                (   'var_name', 
                    'extra_class', 
                    'is_pensil_flag', 
                    'is_input_flag', 
                    'show_shadow_flag', 
                    'is_short_val_flag',
                ), idx_arr
            ):
                kwargs.update({ var_name: idx_item })
            # row-level var:val(s) needed for every cell
            kwargs.update({ 'row_inst': self.context['row_inst'] })
            # extra in-context_to_html method
            # skip context_to_html if not result(line_qty=0 for ex.)
            if not self.extra_upd_kwargs(kwargs): return OK_EMPTY_RESPONSE
            # create the cell's obj.and render the cell's html
            cell_obj = self.context['cell_making_class']()
            cell_obj.make_context(**kwargs)
            self.context['cells_arr'].append( 
                cell_obj.context_to_html()
            )
        # extra in-context_to_html method
        self.extra_context_upd()
        # join cell's htmls inside row html and return the result
        return render_to_string(self.template, self.context)


class RowPivotGoodsline(Row): 

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        # class to make cell obj., to rewrite in some cases
        self.context['cell_making_class'] = CellPivotGoodsline


class RowPivotGoodslineDummy(RowPivotGoodsline):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_pivot_goodsline_dummy.html'

    def make_context(self, **kwargs):
        RowPivotGoodsline.make_context(self, **kwargs)
        # class to make cell obj., to rewrite in some cases
        self.context['cell_making_class'] = CellPivotGoodslineDummy


class RowPivotMovesGoodsline(Row): 

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellPivotMovesGoodsline


class RowPivotStoreGoodsline(Row): 

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellPivotStoreGoodsline

    # part of context_to_html()
    def extra_upd_kwargs(self, kwargs):
        line_qty = Decimal(0.00)
        goodslines = Goodsline.objects.filter(
            material=self.context['row_inst'].material,
            purchase_human_id=self.context['row_inst'].purchase_human_id,
        )
        deb_qty = sum([
            goodsline.qty
            if goodsline.root_transaction.deb_account 
                == self.context['store_stock_acc'] else Decimal(0.000)
            for goodsline in goodslines
        ])
        cred_qty = sum([
            goodsline.qty
            if goodsline.root_transaction.cred_account 
                    == self.context['store_stock_acc']
            else Decimal(0.000)
            for goodsline in goodslines
        ])
        line_qty = deb_qty - cred_qty
        kwargs.update({ 'line_qty': line_qty })
        #
        # N.B. update qty value for row-level
        self.context['qty'] = line_qty
        #
        return True if line_qty else False


class RowPivotAccSummary(Row):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellPivotAccSummary

    # part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        # pass some extras to cell level
        for var_name in (
            'hot_transaction', 'deb_money', 'cred_money', 'balance'
        ):
            kwargs.update({ var_name: self.context[var_name] })
        return True


class RowPivotBalancesPartner(Row):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellPivotBalancesPartner

    # part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        # pass some extras to cell level
        for var_name in (
            'deb_money', 'cred_money', 'balance'
        ):
            kwargs.update({ var_name: self.context[var_name] })
        return True


class RowPivotBalancesTransaction(Row):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellPivotBalancesTransaction


class RowTrialBalanceBookAccount(Row):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellTrialBalanceBookAccount

    # part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        # pass some extras to cell level
        for var_name in (
            'start_date', 'end_date', 'transactions_before',
            'transactions_during', 'transactions_to_date',
        ):
            kwargs.update({ var_name: self.context[var_name] })
        return True



class RowEdit(Row):  # virtical row for edit tables

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_edit_std.html'

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        # class to make cell obj., to rewrite in transaction case
        self.context['cell_making_class'] = CellEdit

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'tab_action': self.context['tab_action'] })
        kwargs.update({ 'tab_class': self.context['tab_class'] })
        kwargs.update({ 'tab_model': self.context['tab_model'] })
        return True

    # extra in-make_context method
    def extra_context_upd(self):
        self.context.update({
            'headers_cells_zip':
            zip( self.context['header_titles'], self.context['cells_arr'], )
        })


class RowEditTransaction(RowEdit): 

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_edit_transaction.html'

    def make_context(self, **kwargs):
        RowEdit.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellEditTransaction
        #
        for kword in ('edit_tr_details', 'edit_tr_add_acc'):
            self.context[kword] = MSGS[kword][lc_id]

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'tab_action': self.context['tab_action'] })
        kwargs.update({ 'tab_class': self.context['tab_class'] })
        kwargs.update({ 'tab_model': self.context['tab_model'] })
        kwargs.update({ 'hot_transaction': self.context['hot_transaction'] })
        return True 


class RowEditShipping(RowEditTransaction): 

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_edit_shipping.html'


class RowEditKilledTransaction(RowEdit): 

    def __init__(self):
        self.template = (
            TABS_TEMPLATES_DIR + '/' + 'row_edit_killed_transaction.html'
        )

    def make_context(self, **kwargs):
        RowEdit.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellEditTransaction


class RowNew(RowEdit): 

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        RowEdit.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellNew


class RowNewTransaction(RowEdit): 

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_edit_transaction.html'

    def make_context(self, **kwargs):
        RowEdit.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellNewTransaction
        #
        for kword in ('edit_tr_details', 'edit_tr_add_acc'):
            self.context[kword] = MSGS[kword][lc_id]

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'tab_action': self.context['tab_action'] })
        kwargs.update({ 'tab_class': self.context['tab_class'] })
        kwargs.update({ 'tab_model': self.context['tab_model'] })
        kwargs.update({ 'hot_transaction': self.context['hot_transaction'] })
        return True


class RowNewGoodsline(RowEdit): 

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_new_goodsline.html'

    def make_context(self, **kwargs):
        RowEdit.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellNewGoodsline
        self.context['subtitle_add_goodsline']= MSGS[
            'subtitle_add_goodsline'
        ][lc_id]

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'tab_action': self.context['tab_action'] })
        kwargs.update({ 'tab_class': self.context['tab_class'] })
        kwargs.update({ 'tab_model': self.context['tab_model'] })
        return True 


class RowDropdown(Row): 

    def __init__(self):
        self.template = TABS_TEMPLATES_DIR + '/' + 'row_dropdown.html'

    def make_context(self, **kwargs):
        Row.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellDropdown


class RowDropdownStoreGoodsline(RowPivotStoreGoodsline): 

    def __init__(self):
        super().__init__()
        self.template = ( TABS_TEMPLATES_DIR + '/' 
            + 'row_dropdown_store_goodsline.html'
        )

    def make_context(self, **kwargs):
        RowPivotStoreGoodsline.make_context(self, **kwargs)
        self.context['cell_making_class'] = CellDropdownStoreGoodsline
        self.context['shadow_id'] = self.context['row_inst'].material.id
        self.context['human_id'] = self.context['row_inst'].human_id
        self.context['qty'] = self.context['row_inst'].qty


# Table-family classes
 
# common table class
#
class ShownTableStd(TabBase, AsViewContainer):

    def __init__(self):
        super().__init__()
        # set others
        self.template = ''
        # dflt.sort by id
        self.sort_filters = ()
        self.filter_date1 = ''
        self.filter_date2 = ''

    def get_sidebar_dates(self):
        try:
            self.sidebar_dates = (
                self.request.POST['sidebar_date1'] 
                    if self.request.POST['sidebar_date1'] 
                else '2021-01-01',
                self.request.POST['sidebar_date2'] 
                    if self.request.POST['sidebar_date2'] 
                else datetime.now().strftime('%Y-%m-%d')
            )
        except:
            self.sidebar_dates = (
                '2021-01-01',
                datetime.now().strftime('%Y-%m-%d')
            )

    def get_sidebar_filters_data(self):
        try:
            self.sidebar_filters_data = json.loads(
                self.request.POST['sidebar_filters_data'] 
            )
        except:
            self.sidebar_filters_data = {}
        self.sidebar_filters_checked = {}
        for var_name in self.sidebar_may_filter_by:
            try:
                val = self.sidebar_filters_data[var_name]
            except:
                val = ''
            self.sidebar_filters_checked.update(
                { var_name: val }
            )
            
    def make_context(self, **kwargs):
        # make basic context
        TabBase.make_context(self, **kwargs)
        # default classes to make row and cell instances
        # will be rewritten in edit and transaction cases
        self.context['row_making_class'] = Row
        # set directly table-level var:val's
        self.context['header_titles']       = ()
        self.context['header_widths']       = ()
        self.context['header_classes']      = ()
        # row-level var:val's
        self.context['row_model']           = ''
        self.context['row_id']              = ''
        self.context['row_extra_class']     = ''
        # cell-level var:val's
        self.context['var_names']           = ()
        self.context['extra_classes']       = ()
        self.context['is_pensil_flags']     = ()
        self.context['is_input_flags']      = ()
        self.context['show_shadow_flags']   = ()
        self.context['is_short_val_flags']  = ()
        self.context['row_inst']          = ''
        self.context['run_on_load']         += ''

    # method to find model instance(s)
    def get_model_insts(self):
        return ''
    
    # parts of context_to_html()
    def extra_pre_calcs(self):
        pass

    def extra_upd_kwargs(self, kwargs):
        return True

    def extra_post_calcs(self):
        pass

    def context_to_html(self):
        self.context['headers_zip'] = zip(
            self.context['header_titles'],
            self.context['header_widths'],
            self.context['header_classes'],
        )
        self.extra_pre_calcs()
        # make array of row's htmls
        self.context['rows_arr'] = []
        # iterate over rows
        for model_inst in self.get_model_insts():
            # start to make kwargs dict for current row obj.
            kwargs = {}
            # cell-level var:val's
            for var_name in (
                'var_names',
                'extra_classes',
                'is_pensil_flags',
                'is_input_flags',      
                'show_shadow_flags',    
                'is_short_val_flags',
            ):
                kwargs.update({ var_name: self.context[var_name] })
            ##
            kwargs.update({ 'tab_inst': self })
            kwargs.update({ 'row_inst': model_inst })
            # row-level var:val's
            kwargs.update({ 'row_model': self.context['row_model'] })
            kwargs.update({ 'row_extra_class': self.context['row_extra_class'] })
            # actual for all but new cases, will be overriden there
            kwargs.update({ 'row_id': getattr(model_inst, 'id') })
            # (for transaction (only) here should be hot_transaction as well
            #  so add it later in extra_upd_kwargs() )
            # main pairs to kwargs
            kwargs.update({ 'tab_action': self.context['tab_action'] })
            kwargs.update({ 'tab_class': self.context['tab_class'] })
            kwargs.update({ 'tab_model': self.context['tab_model'] })
            kwargs.update({ 'tab_name': self.context['tab_name'] })
            # extra in-context_to_html method
            self.current_model_inst = model_inst
            self.extra_upd_kwargs(kwargs)
            # make row obj., render it's html and append to common result
            row_obj = self.context['row_making_class']()
            row_obj.make_context(**kwargs)
            self.context['rows_arr'].append( 
                row_obj.context_to_html()
            )
 
        self.extra_post_calcs()
        # join row's htmls inside table html and return the result
        return render_to_string(self.template, self.context)


#
# pivot table's classes
#
class ShownPivotStd(ShownTableStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_pivot_std.html'
        # result filters
        self.sidebar_may_filter_by = {}

    def req_to_db(self):
        # get sidebar info
        self.get_sidebar_dates()
        self.get_sidebar_filters_data()

    def make_context(self, **kwargs):
        # make basic context
        ShownTableStd.make_context(self, **kwargs)
        self.context['row_extra_class']     = 'table-sm row-id-able'
        self.context['run_on_load'] += ' set_pensil_clicks'

    # part of get_model_insts
    # by default no dates in a model
    def filter_sidebar_dates(self, objs):
        return objs

    # part of get_model_insts
    def apply_sidebar_filters(self, objs):
        for var_name in self.sidebar_may_filter_by:
            if self.sidebar_filters_checked[var_name]:
                # apply filter with current model
                # unwrap book_account special case
                if var_name == 'book_account':
                    objs = objs.filter(
                        Q(
                            deb_account=BookAccount.objects.get(
                                id=self.sidebar_filters_checked[var_name]
                            )
                        ) | Q(
                            cred_account=BookAccount.objects.get(
                                id=self.sidebar_filters_checked[var_name]
                            )
                        )
                    )
                # check simple sidebar input's values
                elif var_name == 'comment':
                    lower_ids = [ obj.id
                        for obj in objs 
                        if (self.sidebar_filters_checked[var_name] 
                            in obj.comment.lower() 
                        )
                    ]
                    objs = objs.filter(id__in=lower_ids)
                #
                elif (
                    self.request.POST['tab_class'] == 'partners_balance'
                    and self.request.POST['tab_model'] == 'partner'
                    and var_name == 'partner' 
                ):
                    objs = objs.filter(
                        id=self.sidebar_filters_checked[var_name]
                    )
                else:
                    objs = objs.filter(**{
                        var_name: 
                        self.sidebar_may_filter_by[var_name].objects.get(
                            id=self.sidebar_filters_checked[var_name]
                        )
                    })
        return objs

    # by default pivot finds _all_ model instances
    def get_model_insts(self):
        model_insts = self.context['row_model'].objects.all().order_by(
            *self.sort_filters
        )
        model_insts = self.apply_sidebar_filters(model_insts)
        model_insts = self.filter_sidebar_dates(model_insts)
        return model_insts
    

class ShownPivotPartner(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ('name',)

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['header_titles']       = ( 
           MSGS['pivot_parter_name1'][lc_id], 
           MSGS['pivot_parter_name2'][lc_id], 
           MSGS['pivot_parter_group'][lc_id], 
           '', 
        )
        self.context['header_widths']       = ( 5, 4, 2, 1, )
        self.context['header_classes']      = ('', '', '', ' text-center', )
        # row-level args
        self.context['row_model']           = Partner
        # cell-level args
        self.context['var_names'] = ('name', 'last_name', 'partner_group', '', )
        self.context['extra_classes']       = ('', '', '', ' text-center', )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, )
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, )


class ShownPivotMaterial(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ('name',)

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['header_titles']       = ( 
            MSGS['pivot_mat_name'][lc_id], '', '', 
        )
        self.context['header_widths']       = ( 6, 1, 5, )
        self.context['header_classes']      = ('', ' text-center', '', )
        # row-level args
        self.context['row_model']           = Material
        # cell-level args
        self.context['var_names']           = ('name', '', '', )
        self.context['extra_classes']       = ('', ' text-center', '', )
        self.context['is_pensil_flags']     = ( 0, 1, 0, )
        self.context['is_input_flags']      = ( 0, 0, 0, )
        self.context['show_shadow_flags']   = ( 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, )


class ShownPivotTransaction(ShownPivotStd):

    def __init__(self):
        super().__init__()
        # result filters
        self.sort_filters = ('date', 'human_id', 'id', )
        self.sidebar_may_filter_by = {
            'hot_transaction': HotTransaction,
            'book_account': BookAccount,
            'partner': Partner,
            'employee': Partner,
            'comment': 0,
        }

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['header_titles']       = ( 
            MSGS['pivot_tr_human_id'][lc_id],
            MSGS['pivot_tr_date'][lc_id],
            MSGS['pivot_tr_partner'][lc_id],
            MSGS['pivot_tr_hot_transaction'][lc_id],
            MSGS['pivot_tr_deb_account'][lc_id],
            MSGS['pivot_tr_cred_account'][lc_id],
            MSGS['pivot_tr_money'][lc_id],
            MSGS['pivot_tr_comment'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 1, 1, 2, 1, 1, 1, 1, 3, 1, )
        self.context['header_classes']      = (
            '', 
            ' text-right', 
            '',  
            '', 
            ' text-center', 
            ' text-center', 
            ' text-right', 
            '', 
            ' text-center', 
        )
        # row-level args
        self.context['row_model']           = Transaction
        # cell-level args
        self.context['var_names']           = (
            'human_id',
            'date',
            'partner',
            'hot_transaction',
            'deb_account',
            'cred_account',
            'money',
            'comment',
            '', # pensil
        )
        self.context['extra_classes']       = (
            '', 
            ' text-right', 
            '',  
            '', 
            ' text-center', 
            ' text-center', 
            ' text-right', 
            '', 
            ' text-center', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 1, 1, 0, 0, 0, )

    # part of get_model_insts
    def filter_sidebar_dates(self, objs):
        return objs.filter(
            date__range=[ self.sidebar_dates[0], self.sidebar_dates[1] ]
        ) 

    # part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        # add hot_transaction from-db val
        kwargs.update({ 'hot_transaction': 
            getattr(self.current_model_inst, 'hot_transaction').id
        })
        return True


class ShownPivotKilledTransaction(ShownPivotTransaction):

    def __init__(self):
        super().__init__()
        self.sort_filters = ('kill_date', 'human_id' )

    def make_context(self, **kwargs):
        ShownPivotTransaction.make_context(self, **kwargs)
        self.context['row_model'] = KilledTransaction
        self.context['header_titles']       = ( 
            MSGS['pivot_tr_human_id'][lc_id],
            MSGS['pivot_tr_date'][lc_id],
            MSGS['pivot_tr_partner'][lc_id],
            MSGS['pivot_tr_hot_transaction'][lc_id],
            MSGS['pivot_tr_deb_account'][lc_id],
            MSGS['pivot_tr_cred_account'][lc_id],
            MSGS['pivot_tr_money'][lc_id],
            MSGS['pivot_tr_comment'][lc_id],
            MSGS['pivot_killed_tr_killdate'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, )
        self.context['header_classes']      = (
            '', 
            ' text-right', 
            '',  
            '', 
            ' text-center', 
            ' text-center', 
            ' text-right', 
            '', 
            ' text-center', 
            ' text-center', 
        )
        # cell-level args
        self.context['var_names']           = (
            'human_id',
            'date',
            'partner',
            'hot_transaction',
            'deb_account',
            'cred_account',
            'money',
            'comment',
            'kill_date',
            '', # pensil
        )
        self.context['extra_classes']       = (
            '', 
            ' text-right', 
            '',  
            '', 
            ' text-center', 
            ' text-center', 
            ' text-right', 
            '', 
            ' text-right', 
            ' text-center', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, )


class ShownPivotGoodsline(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_pivot_goodsline.html'
        self.sort_filters = ( 'human_id', 'id', )

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowPivotGoodsline
        # rewrite table-level args
        self.context['header_titles']       = ( 
            '',     # purchase_human_id
            MSGS['pivot_goodsln_human_id'][lc_id],
            MSGS['pivot_goodsln_name'][lc_id],
            MSGS['pivot_goodsln_comment'][lc_id],
            MSGS['pivot_goodsln_qty'][lc_id],
            MSGS['pivot_goodsln_price'][lc_id],
            MSGS['pivot_goodsln_total'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 0, 1, 3, 2, 1, 1, 1, 1, )
        self.context['header_classes']      = (
            '', 
            '', 
            '', 
            '', 
            'text-center', 
            'text-right', 
            'text-right', 
            'text-center', 
        )
        # row-level args
        self.context['row_model']           = Goodsline
        # cell-level args
        self.context['var_names']           = (
            'purchase_human_id',
            'human_id',
            'material',
            'comment',
            'qty',
            'price',
            'total',
            '', # (pensil)x
        )
        self.context['extra_classes']       = (
            ' save-val', 
            ' save-val', 
            ' save-shadow', 
            ' save-val', 
            ' save-val text-center', 
            ' save-val text-right', 
            ' text-right', 
            ' text-center goodslines-input-del', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 1, 1, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, )
        # call render of goodslines-dummy and new-goodsline tables right here
        if self.__class__.__name__ == 'ShownPivotGoodsline':
            self.context['dummy_row'] = ShownPivotGoodslineDummy.as_html()(
                self.request
            )
            self.context['input_goodsline_row'] = ShownNewGoodsline.as_html()(
                self.request
            )
        #
        self.context['run_on_load'] = (
            ' set_x_clicks set_input_checks'
            + ' goodslines_table_controls'
        )

    # get not all goodlines but linked to the transaction only
    def get_model_insts(self):
        if ( self.context['root_transaction'] != '0' 
            and self.context['root_transaction'] 
        ): 
            # for shipping subst.called root_transaction with major ship.transact.
            if self.request.POST['hot_transaction'] == str(SHIPPING_HOT_ID):
                curr_root_transaction_id = str(
                    Transaction.objects.get(
                        human_id=Transaction.objects.get(
                                id=self.context['root_transaction']
                            ).human_id,
                        deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                        cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
                    ).id
                )
            else:
                curr_root_transaction_id = self.context['root_transaction'] 
            return Goodsline.objects.filter(
                root_transaction=curr_root_transaction_id
            ) 
        else:
            return ()

    # rewrite the pIvot as_view's subfunction 
    # to show shipping-goodsmoves table if nessesary
    def make_html_resp(self, request):
        if (request.POST['hot_transaction'] == str(SHIPPING_HOT_ID)
            and self.__class__.__name__ == 'ShownPivotGoodsline'
        ):
            return ShownPivotShippedGoodsline().make_html_resp(request)
        else:
            return ShownPivotStd.make_html_resp(self, request)


class ShownPivotKilledGoodsline(ShownPivotGoodsline):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownPivotGoodsline.make_context(self, **kwargs)
        self.context['row_model'] = KilledGoodsline
        self.context['run_on_load'] = ''

    # get not all goodlines but linked to the transaction only
    def get_model_insts(self):
        if self.context['root_transaction']: 
            return KilledGoodsline.objects.filter(
                root_transaction=KilledTransaction.objects.get(
                    id=self.context['root_transaction']
                ) 
            ).order_by(*self.sort_filters)
        else:
            return ()

    # rewrite the pIvot as_view's subfunction 
    # to show shipping-goodsmoves table if nessesary
    def make_html_resp(self, request):
        if (request.POST['hot_transaction'] == str(SHIPPING_HOT_ID)
            and self.__class__.__name__ == 'ShownPivotKilledGoodsline'
        ):
            return ShownPivotShippedKilledGoodsline().make_html_resp(request)
        else:
            return ShownPivotStd.make_html_resp(self, request)


# this will be called inside backend procedure not from front
class ShownPivotGoodslineDummy(ShownPivotGoodsline):
 
    def __init__(self):
        super().__init__()
        self.template = (
            TABS_TEMPLATES_DIR + '/' + 'table_pivot_goodsline_dummy.html'
        )
        
    # create empty model instance
    def get_model_insts(self):
        return (
            ( self.context['row_model'](), )
        )

    def make_context(self, **kwargs):
       ShownPivotGoodsline.make_context(self, **kwargs)
       self.context['row_making_class'] = RowPivotGoodslineDummy


class ShownPivotShippedGoodsline(ShownPivotGoodsline): # diff.topogr.comp.to goodsline

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'human_id', 'id', )

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowPivotGoodsline
        # rewrite table-level args
        self.context['header_titles']       = ( 
            '',
            MSGS['pivot_goodsln_human_id'][lc_id],
            MSGS['pivot_goodsln_name'][lc_id],
            MSGS['pivot_goodsln_comment'][lc_id],
            MSGS['pivot_goodsln_qty'][lc_id],
            MSGS['pivot_goodsln_price'][lc_id],
            MSGS['pivot_goodsln_ship_price'][lc_id],
            MSGS['pivot_goodsln_total'][lc_id],
            MSGS['pivot_goodsln_ship_total'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 0, 1, 3, 2, 1, 1, 1, 1, 1, 1, )
        self.context['header_classes']      = (
            '', 
            '', 
            '', 
            '', 
            'text-center', 
            'text-right', 
            'text-right', 
            'text-right', 
            'text-right', 
            'text-center', 
        )
        # row-level args
        self.context['row_model']           = Goodsline
        # cell-level args
        self.context['var_names']           = (
            'purchase_human_id',
            'human_id',
            'material',
            'comment',
            'qty',
            'price',
            'ship_price',
            'total',
            'ship_total',
            '', # (pensil)x
        )
        self.context['extra_classes']       = (
            ' save-val', 
            ' save-val', 
            ' save-shadow', 
            ' save-val', 
            ' save-val text-center', 
            ' save-val text-right', 
            ' save-val text-right', 
            ' text-right', 
            ' text-right', 
            ' text-center goodslines-input-del', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        # call render of goodslines-dummy and new-goodsline tables right here
        if self.__class__.__name__ == 'ShownPivotShippedGoodsline':
            self.context[
                'dummy_row'
            ] = ShownPivotShippedGoodslineDummy.as_html()(self.request)
            self.context[
                'input_goodsline_row'
            ] = ShownNewShippedGoodsline.as_html()(self.request)
        #
        self.context['run_on_load'] = (
            ' set_x_clicks set_input_checks'
            + ' goodslines_table_controls'
        )

    # do not use hookish parent's method but use grandparent's instead
    def make_html_resp(self, request):
        return ShownPivotStd.make_html_resp(self, request)


class ShownPivotShippedKilledGoodsline(ShownPivotShippedGoodsline): 

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownPivotShippedGoodsline.make_context(self, **kwargs)
        self.context['row_model'] = KilledGoodsline
        self.context['run_on_load'] = ''

    # get not all goodlines but linked to the transaction only
    def get_model_insts(self):
        return ShownPivotKilledGoodsline.get_model_insts(self)


class ShownPivotShippedGoodslineDummy(ShownPivotShippedGoodsline):

    def __init__(self):
        super().__init__()
        self.template = (TABS_TEMPLATES_DIR + '/' 
                + 'table_pivot_goodsline_dummy.html'
        )

    # create empty model instance
    def get_model_insts(self):
        return (
            ( self.context['row_model'](), )
        )
        
    def make_context(self, **kwargs):
       ShownPivotShippedGoodsline.make_context(self, **kwargs)
       self.context['row_making_class'] = RowPivotGoodslineDummy


class ShownMaterialHistoryGoodsline(ShownPivotStd):

    def __init__(self):
        super().__init__()
        # result filters
        self.sort_filters = ( 'human_id', 'id', )
        self.sidebar_may_filter_by = {
            'material': Material,
        }

    # rewrite to get filtered material data only
    def apply_sidebar_filters(self, objs):
        material_id = self.sidebar_filters_checked['material']
        # apply material filter if exist
        if material_id:
            objs = objs.filter(
                material=Material.objects.get(
                    id=material_id
                )
            )
        # if no material selected return empty set
        else:
            objs = Goodsline.objects.none()
        return objs

    # get standard pivot set of transacions and leave
    # the only related to store and stock accs
    def get_model_insts(self):
        return ShownPivotStd.get_model_insts(self).filter(
            Q(
                root_transaction__deb_account=INVENTORIES_ACCOUNT
            ) | Q(
                root_transaction__cred_account=INVENTORIES_ACCOUNT
            ) | Q(
                root_transaction__deb_account=STOCK_ACCOUNT
            ) | Q(
                root_transaction__cred_account=STOCK_SISTER_ACCOUNT
            )
        )

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['row_making_class'] = RowPivotMovesGoodsline
        self.context['header_titles']       = ( 
            MSGS['mat_hist_mat'][lc_id],
            MSGS['mat_hist_root_human_id'][lc_id],
            MSGS['mat_hist_date'][lc_id],
            MSGS['mat_hist_partner'][lc_id],
            MSGS['mat_hist_hot_tr'][lc_id],
            MSGS['mat_hist_comment'][lc_id],
            MSGS['mat_hist_qty'][lc_id],
            MSGS['mat_hist_price'][lc_id],
            MSGS['mat_hist_human_id'][lc_id],
            '', 
        )
        self.context['header_widths']       = ( 1, 1, 1, 1, 1, 3, 1, 1, 1, 1, )
        self.context['header_classes']      = (
            '', 
            '', 
            ' text-right', 
            '',  
            '', 
            '', 
            ' text-center', 
            ' text-center', 
            ' text-right', 
            ' text-center', 
        )
        # row-level args
        self.context['row_model']           = Goodsline
        # cell-level args
        self.context['var_names']           = (
            'material',
            # some artificial vars from root_transaction, needs special Cell()
            'root_human_id',
            'date',
            'partner',
            'hot_transaction',
            'comment',
            # regular goodsmove's vars again
            'qty',
            'price',
            'human_id',
            '', # pensil
        )
        self.context['extra_classes'] = self.context['header_classes']
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )


class ShownInventoriesGoodsline(ShownPivotStd):

    def __init__(self):
        super().__init__()
        # result filters
        self.sort_filters = ('material', 'price',)
        # filter nothing, show all items
        self.sidebar_may_filter_by = {}
        self.store_stock_acc = INVENTORIES_ACCOUNT

    def apply_sidebar_filters(self, objs):
        return objs

    # get models removing price duplicates
    def get_model_insts(self):

        # get goodslines related to store book accs.only
        all_goodsline_insts = Goodsline.objects.filter(
            Q(
                root_transaction__deb_account=self.store_stock_acc
            ) | Q(
                root_transaction__cred_account=self.store_stock_acc
            )
        )
        # extra filter by purchases
        ids = []
        materials = list(set(
            [ goodsline_inst.material for goodsline_inst in all_goodsline_insts ]
        ))
        for material in materials:
            purchase_human_ids = list(set(
                [ goodsline_inst.purchase_human_id for goodsline_inst 
                    in Goodsline.objects.filter(material=material)
                ]
            ))
            for purchase_human_id in purchase_human_ids:
                ids.append(
                    Goodsline.objects.filter(
                        Q(material=material) 
                        & Q(purchase_human_id=purchase_human_id)
                    ).first().id
                )
        model_insts = Goodsline.objects.filter(id__in=ids)
        return model_insts.order_by(
            *self.sort_filters
        )

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['row_making_class']    = RowPivotStoreGoodsline
        self.context['header_titles']       = ( 
            MSGS['inventories_mat'][lc_id],
            MSGS['inventories_qty'][lc_id],
            MSGS['inventories_price'][lc_id],
            '', # pensil
            '',
        )
        self.context['header_widths']       = ( 4, 1, 1, 1, 5, )
        self.context['header_classes']      = (
            '', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            '', 
        )
        # row-level args
        self.context['row_model']           = Goodsline
        # cell-level args
        self.context['var_names']           = (
            'material',
            'qty',
            'price',
            '', # pensil
            '',
        )
        self.context['extra_classes'] = self.context['header_classes']
        self.context['is_pensil_flags']     = ( 0, 0, 0, 1, 0, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, )
        self.context['show_shadow_flags']   = ( 1, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, )

    def extra_upd_kwargs(self, kwargs):
        # pass to row level const to calc.line_qty
        kwargs.update({ 'store_stock_acc': self.store_stock_acc })
        return True


class ShownInStockGoodsline(ShownInventoriesGoodsline):

    def __init__(self):
        super().__init__()
        self.store_stock_acc = STOCK_ACCOUNT


class ShownPivotAccSumCard(ShownPivotTransaction):

    def __init__(self):
        super().__init__()
        self.template = (TABS_TEMPLATES_DIR + '/' 
                + 'table_acc_sum_card.html'
        )
        self.sort_filters = ( 'date', 'human_id', 'id', )
        self.sidebar_may_filter_by = {
            'hot_transaction': HotTransaction,
            'book_account': BookAccount,
            'partner': Partner,
            'employee': Partner,
        }

    # part of get_model_insts
    def apply_sidebar_filters(self, objs):
        # show nothing if no acc.selected in sidebar
        if not self.sidebar_filters_checked['book_account']:
            return Transaction.objects.none()
        else:
            return ShownPivotTransaction.apply_sidebar_filters(self, objs)

    def make_context(self, **kwargs):
        ShownPivotTransaction.make_context(self, **kwargs)
        # rewrite table-level args
        self.context['row_making_class']    = RowPivotAccSummary
        self.context['header_titles']       = ( 
            MSGS['acc_sum_card_human_id'][lc_id],
            MSGS['acc_sum_card_date'][lc_id],
            MSGS['acc_sum_card_partner'][lc_id],
            MSGS['acc_sum_card_hot_tr'][lc_id],
            MSGS['acc_sum_card_comment'][lc_id],
            MSGS['acc_sum_card_deb_sum'][lc_id],
            MSGS['acc_sum_card_cred_sum'][lc_id],
            MSGS['acc_sum_card_balance'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 1, 1, 1, 1, 4, 1, 1, 1, 1, )
        self.context['header_classes']      = (
            '', 
            ' text-right', 
            '',  
            '',  
            '', 
            ' text-right', 
            ' text-right', 
            ' text-right', 
            ' text-center', 
        )
        # cell-level args
        self.context['var_names']           = (
            'human_id',
            'date',
            'partner',
            'hot_transaction',
            'comment',
            'deb_money',
            'cred_money',
            'balance',
            '', # pensil
        )
        self.context['extra_classes'] =     (
            '', 
            ' text-right', 
            '',  
            '',  
            '', 
            ' text-right', 
            ' text-right', 
            ' text-right dk-prefix', 
            ' text-center', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 0, 0, 1, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        # localiz.
        for kword in (
            'acc_sum_card_acc_header', 
            'acc_sum_card_start_bal_header',
            'acc_sum_card_total',
        ):
            self.context[kword] = MSGS[kword][lc_id]
        # add correction for balance fields(d|k prefixes)
        self.context['run_on_load'] += ' dk_prefix'

    # part of context_to_html()
    def extra_pre_calcs(self):
        self.curr_balance = self.curr_deb = self.curr_cred = Decimal(0.00)
        self.deb_before = self.cred_before = Decimal(0.00)
        transactions = Transaction.objects.all()
        for sidebar_var in ('partner', 'hot_transaction'):
            sidebar_val = self.sidebar_filters_checked[sidebar_var]
            if sidebar_val:
                transactions = transactions.filter(
                    **{sidebar_var: sidebar_val}
                )
        sidebar_book_acc = self.sidebar_filters_checked['book_account']
        if sidebar_book_acc:
            transactions = transactions.filter(
                    date__lt=datetime.strptime(
                        self.sidebar_dates[0], '%Y-%m-%d'
                    ).date()
                ).filter(
                    Q(
                        deb_account=BookAccount.objects.get(id=sidebar_book_acc) 
                    ) | Q(
                        cred_account=BookAccount.objects.get(id=sidebar_book_acc)
                    )
            )
            self.deb_before = sum([
                transaction.money if str(transaction.deb_account.id) 
                    == sidebar_book_acc else Decimal(0.00)
                for transaction in transactions
            ])
            self.cred_before = sum([
                transaction.money if str(transaction.cred_account.id) 
                    == sidebar_book_acc else Decimal(0.00)
                for transaction in transactions
            ])
        # global(for row-levels); this is init.value
        self.curr_balance = self.deb_before - self.cred_before
        # upd.context to show this in template beyond the table rows
        self.context['shown_book_acc'] = BookAccount.objects.get(
            id=sidebar_book_acc
        ) if sidebar_book_acc else ''
        self.context['shown_init_balance'] = str(self.curr_balance)

    # row-level part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'hot_transaction': 
            kwargs['row_inst'].hot_transaction.id
        })
        # pass to cell level some extra vars
        if ( str(kwargs['row_inst'].deb_account.id)
            == self.sidebar_filters_checked['book_account']
        ):
            kwargs.update({ 'deb_money': kwargs['row_inst'].money })
            kwargs.update({ 'cred_money': Decimal(0.00) })
        elif ( str(kwargs['row_inst'].cred_account.id)
            == self.sidebar_filters_checked['book_account']
        ):
            kwargs.update({ 'deb_money': Decimal(0.00) })
            kwargs.update({ 'cred_money': kwargs['row_inst'].money })
        # if no selected sidebar accs.
        else:
            return
        # calc balance val.for current line
        prev_balance = self.curr_balance
        self.curr_balance = (
            prev_balance + kwargs['deb_money'] - kwargs['cred_money']
        )
        kwargs.update({ 'balance': self.curr_balance })
        # calc current deb.and cred.money for the period
        self.curr_deb += kwargs['deb_money']
        self.curr_cred += kwargs['cred_money']
        return True

    # part of context_to_html()
    def extra_post_calcs(self):
        self.context['shown_final_deb'] = str(self.curr_deb)
        self.context['shown_final_cred'] = str(self.curr_cred)
        self.context['shown_final_balance'] = str(self.curr_balance)


class ShownPartnersBalancePartner(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.template = (
            TABS_TEMPLATES_DIR + '/' + 'table_partners_balance_partner.html'
        )
        self.sort_filters = ('name',)
        self.sidebar_may_filter_by = {
            'partner': Partner
        }

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowPivotBalancesPartner
        # rewrite table-level args
        self.context['header_titles']       = ( 
            MSGS['partners_balance_partner_name'][lc_id],
            MSGS['partners_balance_partner_balance'][lc_id],
            MSGS['partners_balance_partner_deb_sum'][lc_id],
            MSGS['partners_balance_partner_cred_sum'][lc_id],
            '', 
        )
        self.context['header_widths']       = ( 5, 2, 2, 2, 1, )
        self.context['header_classes']      = (
            '', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
        )
        # row-level args
        self.context['row_model']           = Partner
        # cell-level args
        self.context['var_names']           = (
            'name', 'balance', 'deb_money', 'cred_money', '', 
        )
        self.context['extra_classes']       = (
                '', 
                ' text-right balance-for-filter',
                ' text-right',
                ' text-right',
                ' text-center', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, )
        self.context['show_shadow_flags']   = ( 1, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, )
        # add balance-filtering button's clicks
        self.context['run_on_load'] += ' partners_filter_buttons'
        # extra text(button) fields
        for word in ( 'debtors', 'creditors', 'all' ):
            self.context[word + '_name'] = MSGS[
                'partners_balance_partner_' + word
            ][lc_id]

    # row-level part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        deb_money = 0
        for transaction in Transaction.objects.filter(
            deb_account=PARTNERS_ACCOUNT,
            partner__id=kwargs['row_inst'].id
        ):
            deb_money += transaction.money 
        cred_money = 0
        for transaction in Transaction.objects.filter(
            cred_account=PARTNERS_ACCOUNT,
            partner__id=kwargs['row_inst'].id
        ):
            cred_money += transaction.money 
        balance = deb_money - cred_money
        kwargs.update({ 'deb_money': deb_money })
        kwargs.update({ 'cred_money': cred_money })
        kwargs.update({ 'balance': balance })


class ShownPartnersBalanceTransaction(ShownPivotTransaction):

    def __init__(self):
        super().__init__()
        self.sidebar_may_filter_by = {
            'partner': Partner
        }

    def make_context(self, **kwargs):
        ShownPivotTransaction.make_context(self, **kwargs)
        self.context['row_making_class'] = RowPivotBalancesTransaction
        # rewrite table-level args
        self.context['header_titles']       = ( 
            MSGS['partners_balance_tr_partner'][lc_id],
            MSGS['partners_balance_tr_human_id'][lc_id],
            MSGS['partners_balance_tr_date'][lc_id],
            MSGS['partners_balance_tr_deb_sum'][lc_id],
            MSGS['partners_balance_tr_cred_sum'][lc_id],
            MSGS['partners_balance_tr_hot_tr'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 2, 1, 2, 2, 2, 2, 1, )
        self.context['header_classes']      = (
            '', 
            '', 
            '',  
            ' text-center', 
            ' text-center', 
            '', 
            ' text-center', 
        )
        # cell-level args
        self.context['var_names']           = (
            'partner',
            'human_id',
            'date',
            'deb_money',
            'cred_money',
            'hot_transaction',
            '', # pensil
        )
        self.context['extra_classes']       = (
            '', 
            '', 
            '',  
            ' text-right', 
            ' text-right', 
            '', 
            ' text-center', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, )

    def get_model_insts(self):
        model_insts = Transaction.objects.filter(
            Q(
                deb_account=PARTNERS_ACCOUNT
            ) | Q(
                cred_account=PARTNERS_ACCOUNT
            )
        ).order_by( *self.sort_filters )
        model_insts = self.apply_sidebar_filters(model_insts)
#       model_insts = self.filter_sidebar_dates(model_insts)
        return model_insts


class ShownTrialBalanceBookAccount(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.template = (TABS_TEMPLATES_DIR + '/' 
            + 'table_trial_balance_book_account.html'
        )
        self.sort_filters = ('name',)

    def make_context(self, **kwargs):
        ShownPivotStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowTrialBalanceBookAccount
        # rewrite table-level args
        self.context['header_titles']       = ( 
            MSGS['trial_balance_name'][lc_id],
            MSGS['trial_balance_deb_sum'][lc_id],
            MSGS['trial_balance_cred_sum'][lc_id],
            MSGS['trial_balance_deb_sum'][lc_id],
            MSGS['trial_balance_cred_sum'][lc_id],
            MSGS['trial_balance_deb_sum'][lc_id],
            MSGS['trial_balance_cred_sum'][lc_id],
            '',
        )
        self.context['header_widths']       = ( 4, 1, 1, 1, 1, 1, 1, 2, )
        self.context['header_classes']      = (
            '', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            ' text-center', 
            '', 
        )
        # row-level args
        self.context['row_model']           = BookAccount
        # cell-level args
        self.context['var_names']           = (
            'name',
            'deb_before',
            'cred_before',
            'deb_during',
            'cred_during',
            'deb_to_date',
            'cred_to_date',
            '',
        )
        self.context['extra_classes']       = (
            '', 
            ' text-right', 
            ' text-right', 
            ' text-right', 
            ' text-right', 
            ' text-right', 
            ' text-right', 
            '',
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_input_flags']      = ( 0, 0, 0, 0, 0, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, )
        # show in template on table level
        self.context['start_date'] = self.sidebar_dates[0] 
        self.context['end_date'] = self.sidebar_dates[1] 
        # lazy transaction sets
        self.context['transactions_before'] = Transaction.objects.filter(
            date__lt=datetime.strptime(
                self.sidebar_dates[0], '%Y-%m-%d'
            ).date()
        )
        self.context['transactions_during'] = Transaction.objects.filter(
            date__range=[
                datetime.strptime(
                    self.sidebar_dates[0], '%Y-%m-%d'
                ).date(),
                datetime.strptime(
                    self.sidebar_dates[1], '%Y-%m-%d'
                ).date(),
            ]
        )
        self.context['transactions_to_date'] = Transaction.objects.filter(
            date__lte=datetime.strptime(
                self.sidebar_dates[1], '%Y-%m-%d'
            ).date()
        )
        # calc totals
        self.context['deb_total_before'] = sum([ 
            sum([ 
                transaction.money if transaction.deb_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_before']
            ])
            for acc in BookAccount.objects.all() 
        ])
        self.context['cred_total_before'] = sum([ 
            sum([ 
                transaction.money if transaction.cred_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_before']
            ])
            for acc in BookAccount.objects.all() 
        ])
        self.context['deb_total_during'] = sum([ 
            sum([ 
                transaction.money if transaction.deb_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_during']
            ])
            for acc in BookAccount.objects.all() 
        ])
        self.context['cred_total_during'] = sum([ 
            sum([ 
                transaction.money if transaction.cred_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_during']
            ])
            for acc in BookAccount.objects.all() 
        ])
        self.context['deb_total_to_date'] = sum([ 
            sum([ 
                transaction.money if transaction.deb_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_to_date']
            ])
            for acc in BookAccount.objects.all() 
        ])
        self.context['cred_total_to_date'] = sum([ 
            sum([ 
                transaction.money if transaction.cred_account == acc 
                    else Decimal(0.00)  
                for transaction in self.context['transactions_to_date']
            ])
            for acc in BookAccount.objects.all() 
        ])
        # extra text fields
        for word in (
            'date_range',
            'balance_before',
            'balance_during',
            'balance_after',
            'total',
        ):
            self.context[word + '_name'] = MSGS[
                'trial_balance_' + word
            ][lc_id]

    # part of context_to_html
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'start_date': self.sidebar_dates[0] })
        kwargs.update({ 'end_date': self.sidebar_dates[1] })
        kwargs.update({ 
            'transactions_before': self.context['transactions_before']
        })
        kwargs.update({ 
            'transactions_during': self.context['transactions_during']
        })
        kwargs.update({ 
            'transactions_to_date': self.context['transactions_to_date']
        })


#
# edit table's classes
#
class ShownEditStd(ShownTableStd):

    def __init__(self):
        # set others
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_edit_std.html'

    # will be overriden in shipping case(req_post instead of topmost request.POST)
    def make_row_id_for_context(self):
        return self.request.POST['row_id']

    def make_context(self, **kwargs):
        # make basic context
        ShownTableStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowEdit
        # single mand.std row-level var
        self.context['row_id'] = self.make_row_id_for_context()
        self.context['row_extra_class']     = 'table-sm row-id-able'
        self.context['run_on_load'] += ' set_input_checks'

    # find the only model instance
    def get_model_insts(self):
        return (
            self.context['row_model'].objects.get(id=self.context['row_id']),
        )

    def extra_upd_kwargs(self, kwargs):
    # extra in-context_to_html method
   
        kwargs.update({ 'header_titles': self.context['header_titles'] })
        return True


class ShownEditPartner(ShownEditStd):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownEditStd.make_context(self, **kwargs)
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_partner_name'][lc_id],         
            MSGS['edit_partner_name2'][lc_id],         
            MSGS['edit_partner_in_group'][lc_id],         
        )
        self.context['row_model']           = Partner
        # cell-level args
        self.context['var_names'] = ( 'name', 'last_name', 'partner_group' )
        self.context['extra_classes']       = ( 
            ' save-val', 
            ' save-val', 
            ' save-shadow load-dropdown',
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, )
        self.context['is_input_flags']      = ( 1, 1, 1, )
        self.context['show_shadow_flags']   = ( 0, 0, 1, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, )


class ShownEditMaterial(ShownEditStd):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownEditStd.make_context(self, **kwargs)
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_mat_name'][lc_id],         
        )
        self.context['row_model']           = Material
        # cell-level args
        self.context['var_names']           = ( 'name', )
        self.context['extra_classes']       = ( ' save-val', )
        self.context['is_pensil_flags']     = ( 0, )
        self.context['is_input_flags']      = ( 1, )
        self.context['show_shadow_flags']   = ( 0, )
        self.context['is_short_val_flags']  = ( 0, )


class ShownEditTransaction(ShownEditStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_edit_transaction.html'

    def make_context(self, **kwargs):
        ShownEditStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowEditTransaction
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_tr_human_id'][lc_id],         
            MSGS['edit_tr_date'][lc_id],            
            MSGS['edit_tr_partner'][lc_id],        
            MSGS['edit_tr_hot_transaction'][lc_id], 
            MSGS['edit_tr_money'][lc_id],          
            MSGS['edit_tr_comment'][lc_id],       
            MSGS['edit_tr_deb_account'][lc_id],  
            MSGS['edit_tr_cred_account'][lc_id],
            MSGS['edit_tr_has_goodslines'][lc_id],   
            MSGS['edit_tr_create_date'][lc_id],     
            MSGS['edit_tr_created_by'][lc_id],     
            MSGS['edit_tr_employee'][lc_id],     
        )
        self.context['row_model']           = Transaction
        # cell-level args
        self.context['var_names']           = (
            'human_id',         # 0
            'date',             # 1
            'partner',          # 2
            'hot_transaction',  # 3
            'money',            # 4
            'comment',          # 5
            'deb_account',      # 6
            'cred_account',     # 7
            'has_goodslines',   # 8 - really invisible
            'create_date',      # 9
            'created_by',       # 10
            'employee',         # 11
        )
        self.context['extra_classes']       = (
            ' save-shadow', 
            ' save-val never-empty', 
            ' save-shadow load-dropdown never-empty',  
            ' save-shadow',  
            ' money-field save-val never-empty', 
            ' save-val', 
            # book accounts will have special save-shadow procedure on frontend
            # to make a few saves with diff.book accounts for single transaction
            ' save-shadow-special load-dropdown never-empty',  
            ' save-shadow-special load-dropdown never-empty',  
            ' save-val', 
            '', 
            '', 
            ' save-shadow load-dropdown never-empty',  
        )
        self.context['is_pensil_flags']     = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 
        )
        self.context['is_input_flags']      = ( 
            0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1 
        )
        self.context['show_shadow_flags']   = ( 
            1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1 
        )
        self.context['is_short_val_flags']  = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 
        )

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'header_titles': self.context['header_titles'] })
        # transfer to row-level
        kwargs.update({ 'hot_transaction': self.context['hot_transaction'] })
        # goodslines-containing flag
        kwargs.update({ 'has_goodslines': HotTransaction.objects.get(
            id=self.context['hot_transaction']).has_goodslines
        })
        kwargs.update({ 'is_employees_action': HotTransaction.objects.get(
            id=self.context['hot_transaction']).is_employees_action
        })
        # add shipping hot transaction's consts
        kwargs.update({ 'SHIPPING_HOT_ID': SHIPPING_HOT_ID })
        kwargs.update({ 'shipping_pairs_zip': SHIPPING_ACC_PAIRS_ZIP })
        return True


    # for shipping rewrite the pIvot as_view's subfunction 
    def make_html_resp(self, request, received_req_post = ''):
        # on (any)shipping transaction 
        if (request.POST['hot_transaction'] == str(SHIPPING_HOT_ID)
            and self.__class__.__name__ == 'ShownEditTransaction'
        ):
            # show major shipping table
            human_id = Transaction.objects.get(
                    id=request.POST['row_id']
                ).human_id
            cloned_req_post = dict.copy(request.POST)
            # subst.transaction id with major shipping's id
            cloned_req_post['row_id'] = str(
                Transaction.objects.get(
                    human_id=human_id,
                    deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                    cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
                ).id
            )
            return ShownEditShipping0().make_html_resp(request, cloned_req_post)
        # else process request with transaction data as usually
        else:
            return ShownEditStd.make_html_resp(self, request, received_req_post)


class ShownEditShipping0(ShownEditTransaction):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownEditTransaction.make_context(self, **kwargs)
        self.context['row_making_class'] = RowEditShipping

    # subst.topmost request.POST with req_post
    def make_row_id_for_context(self):
        return self.req_post['row_id']


class ShownEditKilledTransaction(ShownEditTransaction):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        ShownEditTransaction.make_context(self, **kwargs)
        self.context['row_making_class'] = RowEditKilledTransaction
        # row-level args
        self.context['header_titles']       = (
            'Код',
            'Дата:',
            'КАгент:',
            'Тип:',
            'Сумма:',
            'Прим.:',
            'СчетДебет:',
            'СчетКредит:',
            'Матер.пров.',
            'Дата изм.',
            'Изм.кем',
            'Дата удал.',
            'Удал.кем',
            'Сотр.',
        )
        self.context['row_model'] = KilledTransaction
        # cell-level args
        self.context['var_names']           = (
            'human_id',         # 0
            'date',             # 1
            'partner',          # 2
            'hot_transaction',  # 3
            'money',            # 4
            'comment',          # 5
            'deb_account',      # 6
            'cred_account',     # 7
            'has_goodslines',   # 8
            'create_date',      # 9
            'created_by',       # 10
            'kill_date',        # 11
            'killed_by',        # 12
            'employee',         # 13
        )
        self.context['extra_classes']       = (
            ' save-shadow', 
            ' save-val never-empty', 
            ' save-shadow load-dropdown never-empty',  
            ' save-shadow',  
            ' money-field save-val never-empty', 
            '  save-val', 
            # book accounts will have special save-shadow procedure on frontend
            # to make a few saves with diff.book accounts for single transaction
            ' save-shadow-special load-dropdown never-empty',  
            ' save-shadow-special load-dropdown never-empty',  
            ' save-val', 
            '', 
            '', 
            '', 
            '', 
            ' save-shadow load-dropdown never-empty',  
        )
        self.context['is_pensil_flags']     = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_input_flags']      = (
            0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, )
        self.context['show_shadow_flags']   = ( 
            1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 1, )
        self.context['is_short_val_flags']  = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        self.context['run_on_load'] += ' no_edit_btns_if_killed'


# new table's classes
#
class ShownNewStd(ShownEditStd):

    def __init__(self):
        super().__init__()

    # create model instance
    def get_model_insts(self):
        return ( self.context['row_model'](), )

    def make_context(self, **kwargs):
        # make basic context
        ShownEditStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowNew

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'header_titles': self.context['header_titles'] })
        kwargs.update({ 'row_id': self.context['row_id'] })
        kwargs.update({ 'hot_transaction': self.context['hot_transaction'] })
        # add shipping hot transaction's const
        kwargs.update({ 'SHIPPING_HOT_ID': SHIPPING_HOT_ID })
        kwargs.update({ 'shipping_pairs_zip': SHIPPING_ACC_PAIRS_ZIP })
        return True


class ShownNewPartner(ShownNewStd):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        # first take row-level and cell-level args from sister detail's class 
        ShownNewStd.make_context(self, **kwargs)
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_partner_name'][lc_id],         
            MSGS['edit_partner_name2'][lc_id],         
            MSGS['edit_partner_in_group'][lc_id],         
        )
        self.context['row_model']           = Partner
        # cell-level args
        self.context['var_names'] = ( 'name', 'last_name', 'partner_group' )
        self.context['extra_classes']       = ( 
            ' save-val', 
            ' save-val', 
            ' save-shadow load-dropdown',
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, )
        self.context['is_input_flags']      = ( 1, 1, 1, )
        self.context['show_shadow_flags']   = ( 0, 0, 1, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, )


class ShownNewMaterial(ShownNewStd):

    def __init__(self):
        super().__init__()

    def make_context(self, **kwargs):
        # first take row-level and cell-level args from sister detail's class 
        ShownNewStd.make_context(self, **kwargs)
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_mat_name'][lc_id],         
        )
        self.context['row_model']           = Material
        # cell-level args
        self.context['var_names']           = ( 'name', )
        self.context['extra_classes']       = ( ' save-val', )
        self.context['is_pensil_flags']     = ( 0, )
        self.context['is_input_flags']      = ( 1, )
        self.context['show_shadow_flags']   = ( 0, )
        self.context['is_short_val_flags']  = ( 0, )


class ShownNewTransaction(ShownNewStd, ShownEditTransaction):

    def __init__(self):
        super().__init__()
        # take non-standard template from sisterclass 
        ShownEditTransaction.__init__(self)

    def make_context(self, **kwargs):
        ShownNewStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowNewTransaction
        # row-level args
        self.context['header_titles']       = (
            MSGS['edit_tr_human_id'][lc_id],         
            MSGS['edit_tr_date'][lc_id],            
            MSGS['edit_tr_partner'][lc_id],        
            MSGS['edit_tr_hot_transaction'][lc_id], 
            MSGS['edit_tr_money'][lc_id],          
            MSGS['edit_tr_comment'][lc_id],       
            MSGS['edit_tr_deb_account'][lc_id],  
            MSGS['edit_tr_cred_account'][lc_id],
            MSGS['edit_tr_has_goodslines'][lc_id],   
            MSGS['edit_tr_create_date'][lc_id],     
            MSGS['edit_tr_created_by'][lc_id],     
            MSGS['edit_tr_employee'][lc_id],     
        )
        self.context['row_model']           = Transaction
        # cell-level args
        self.context['var_names']           = (
            'human_id',         # 0
            'date',             # 1
            'partner',          # 2
            'hot_transaction',  # 3
            'money',            # 4
            'comment',          # 5
            'deb_account',      # 6
            'cred_account',     # 7
            'has_goodslines',         # 8 - really invisible
            'create_date',      # 9
            'created_by',       # 10
            'employee',         # 11
        )
        self.context['extra_classes']       = (
            ' save-shadow', 
            ' save-val never-empty', 
            ' save-shadow load-dropdown never-empty',  
            ' save-shadow',  
            ' money-field save-val never-empty', 
            '  save-val', 
            # book accounts will have special save-shadow procedure on frontend
            # to make a few saves with diff.book accounts for single transaction
            ' save-shadow-special load-dropdown never-empty',  
            ' save-shadow-special load-dropdown never-empty',  
            ' save-val', 
            '', 
            '', 
            ' save-shadow load-dropdown never-empty',  
        )
        self.context['is_pensil_flags']     = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 
        )
        self.context['is_input_flags']      = ( 
            0, 1, 1, 0, 1, 1, 1, 1, 1, 0, 0, 1 
        )
        self.context['show_shadow_flags']   = ( 
            1, 0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1 
        )
        self.context['is_short_val_flags']  = ( 
            0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 
        )
        self.context['run_on_load']  += ' no_del_btn_if_new set_add_acc_pair'

    # extra in-context_to_html method
    def extra_upd_kwargs(self, kwargs):
        kwargs.update({ 'header_titles': self.context['header_titles'] })
        # transfer to row-level
        kwargs.update({ 'row_id': self.context['row_id'] })
        kwargs.update({ 'hot_transaction': self.context['hot_transaction'] })
        # goodslines-containing flag
        kwargs.update({ 'has_goodslines': HotTransaction.objects.get(
            id=self.context['hot_transaction']).has_goodslines
        })
        kwargs.update({ 'is_employees_action': HotTransaction.objects.get(
            id=self.context['hot_transaction']).is_employees_action
        })
        # add shipping hot transaction's consts
        kwargs.update({ 'SHIPPING_HOT_ID': SHIPPING_HOT_ID })
        kwargs.update({ 'shipping_pairs_zip': SHIPPING_ACC_PAIRS_ZIP })
        return True


class ShownNewGoodsline(ShownNewStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_new_goodsline.html'

    def make_context(self, **kwargs):
        ShownNewStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowNewGoodsline
        # row-level args
        self.context['row_model']           = Goodsline
        self.context['header_titles'] = ( '', '', '', '', '', '', '', '', ) 
        self.context['header_widths'] = ( 0, 0, 0, 0, 0, 0, 0, 0, )
        # cell-level args
        self.context['var_names']           = (
            'purchase_human_id',
            'human_id',
            'material',
            'comment',
            'qty',
            'price',
            'total',
            '', # (pensil)x
        )
        self.context['extra_classes']       = (
            ' save-val', 
            ' save-val', 
            ' save-shadow load-dropdown goodslines-never-empty', 
            ' save-val', 
            ' save-val qty-field goodslines-input goodslines-never-empty', 
            ' save-val price-field goodslines-input goodslines-never-empty', 
            ' money-field', 
            ' goodslines-inputs-save', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 1, 1, 1, 1, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 1, 1, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, )



class ShownNewShippedGoodsline(ShownNewStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'table_new_goodsline.html'

    def make_context(self, **kwargs):
        ShownNewStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowNewGoodsline
        # row-level args
        self.context['row_model']           = Goodsline
        self.context['header_titles'] = ( 
            '', '', '', '', '', '', '', '',  '', '', ) 
        self.context['header_widths'] = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )
        # cell-level args
        self.context['var_names']           = (
            'purchase_human_id',
            'human_id',
            'material',
            'comment',
            'qty',
            'price',
            'ship_price',
            'total',
            'ship_total',
            '', # (pensil)x
        )
        self.context['extra_classes']       = (
            ' save-val', 
            ' save-val', 
            ' save-shadow load-dropdown goodslines-never-empty', 
            ' save-val', 
            ' save-val qty-field goodslines-input goodslines-never-empty', 
            ' save-val money-field goodslines-input goodslines-never-empty', 
            ' save-val money-field goodslines-input goodslines-never-empty', 
            ' money-field', 
            ' money-field', 
            ' goodslines-inputs-save', 
        )
        self.context['is_pensil_flags']     = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, )
        self.context['is_input_flags']      = ( 0, 0, 1, 1, 1, 1, 1, 0, 0, 0, ) 
        self.context['show_shadow_flags']   = ( 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, )
        self.context['is_short_val_flags']  = ( 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, )




# dropdown classes
#
class ShownDropdownStd(ShownPivotStd):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'dropdown_list.html'

    def make_context(self, **kwargs):
        # make basic context
        ShownPivotStd.make_context(self, **kwargs)
        self.context['row_making_class'] = RowDropdown
        # cell-level args
        self.context['var_names']           = ('name', )
        self.context['extra_classes']       = ('', )
        self.context['is_pensil_flags']     = ( 0, )
        self.context['is_input_flags']      = ( 0, )
        self.context['show_shadow_flags']   = ( 1, )
        self.context['is_short_val_flags']  = ( 0, )
        self.context['row_extra_class']     = 'row-id-able'
        self.context['run_on_load'] = ' del_dropdown_duplicates'


class ShownDropdownPartner(ShownDropdownStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownStd.make_context(self, **kwargs)
        self.context['row_model']           = Partner


class ShownDropdownPartnerGroup(ShownDropdownStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownStd.make_context(self, **kwargs)
        self.context['row_model']           = PartnerGroup 


class ShownDropdownEmployee(ShownDropdownPartner):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownPartner.make_context(self, **kwargs)

    def get_model_insts(self):
        return ShownDropdownPartner.get_model_insts(self).filter(
            partner_group=EMPLOYEES_GROUP 
        )

class ShownDropdownMaterial(ShownDropdownStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownStd.make_context(self, **kwargs)
        self.context['row_model']           = Material 


class ShownDropdownBookAccount(ShownDropdownStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownStd.make_context(self, **kwargs)
        self.context['row_model']           = BookAccount


class ShownDropdownHotTransaction(ShownDropdownStd):

    def __init__(self):
        super().__init__()
        self.sort_filters = ( 'name', )

    def make_context(self, **kwargs):
        ShownDropdownStd.make_context(self, **kwargs)
        self.context['row_model']           = HotTransaction

    # rewrite to exclude empty
    def get_model_insts(self):
        return ShownDropdownStd.get_model_insts(self).filter(
            ~Q(id=EMPTY_HOT_ID)
        )


# non-standard 'material' dropdowns for goods-to-prod. and shipping
class ShownDropdownStoreGoodsline(ShownInventoriesGoodsline):

    def __init__(self):
        super().__init__()
        self.template = TABS_TEMPLATES_DIR + '/' + 'dropdown_list.html'
        self.sort_filters = ('material', )

    def make_context(self, **kwargs):
        # make basic context
        ShownInventoriesGoodsline.make_context(self, **kwargs)
        self.context['row_making_class']    = RowDropdownStoreGoodsline
        self.context['header_titles']       = ( 
            '', '', '', '', '', '', 
        )
        self.context['header_widths']       = ( 0, 0, 0, 0, 0, 0, )
        self.context['header_classes']      = ( '', '', '', '', '', '', ) 
        self.context['var_names']           = (
            'material',
            'qty',
            'price',
            # root's
            'date',
            'partner',
            'human_id',
            '',
        )
        self.context['extra_classes'] = self.context['header_classes']
        self.context[
            'is_pensil_flags'
        ] = self.context[
            'is_input_flags'
        ] = self.context[
            'show_shadow_flags'
        ] = self.context[
            'is_short_val_flags'
        ] = ( 0, 0, 0, 0, 0, 0, 0, )


class ShownDropdownStockGoodsline(ShownDropdownStoreGoodsline):

    def __init__(self):
        super().__init__()
        self.store_stock_acc = STOCK_ACCOUNT

#
# Classes for save-values actions
#

# typical request for 'save' case is
#
#   'tab_action': ['save'], 
#   'tab_class': ['edit'], 
#   'tab_model': ['transaction'], 
#   'table_id': ['0'], 
#   'has_goodslines': ['1'], 
#   'date': ['2021-10-19'], 
#   'money': ['8050.00'], 
#   'comment': ['dfhdkhfd'], 
#   'human_id': ['251691798'], 

#   'hot_transaction': ['9'], 
#   'partner': ['31'], 
#
#   'book_acc_pairs': [
#       '[
#           ["4","2"]
#       ]',
#   ], 
#
#   'goodslines': [
#       '[  {
#               "row_id":"0",
#               "human_id":"251692031",
#               "comment":"c31",
#               "qty":"2",
#               "price":"4000.00",
#               "material":"1"
#           },
#           {
#               "row_id":"0",
#               "human_id":"251692212",
#               "comment":"c32",
#               "qty":"200",
#               "price":"0.25",
#               "material":"2"
#           }
#       ]'
#   ]


# common 'save' data-only containing classes 
# for both 'new' and 'edit'(edit) cases
#
class SavedCommonPartner():

    def __init__(self):
        self.names_to_save += [
           'name', 
           'last_name', 
           'partner_group', 
        ]
        self.save_val_flags     += [ 1, 1, 0, ]
        self.save_shadow_flags  += [ 0, 0, 1, ]
        self.row_model = Partner


class SavedCommonMaterial():

    def __init__(self):
        self.names_to_save += [
           'name', 
        ]
        self.save_val_flags     += [ 1, ]
        self.save_shadow_flags  += [ 0, ]
        self.row_model = Material


class SavedCommonTransaction():

    def __init__(self):
        self.names_to_save += [
            'human_id',         # 0
            'date',             # 1
            'partner',          # 2
            'hot_transaction',  # 3
            'money',            # 4
            'comment',          # 5
            'deb_account',      # 6
            'cred_account',     # 7
            'has_goodslines',   # 8
            'create_date',      # 9
            'created_by',       # 10
            'employee',         # 11
        ]
        self.save_val_flags     += [ 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, ]
        # human_id and acc.pairs are not set here, will be added manually
        self.save_shadow_flags  += [ 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, ] 
        self.row_model = Transaction


class SavedCommonGoodsline():

    def __init__(self):
        self.names_to_save += [
            'purchase_human_id',
            'human_id',
            'material',
            'comment',
            'qty',
            'price',
            'ship_price',
            'total',
            'ship_total',
        ]
        self.save_val_flags     += [ 1, 0, 0, 1, 1, 1, 1, 0, 0, ]
        # human_id not set here, will be added manually
        self.save_shadow_flags  += [ 0, 0, 1, 0, 0, 0, 0, 0, 0, ] 
        self.row_model = Goodsline


#
# common class(es) for all 'save' cases
#
class SavedStd(TabBase, AsViewContainer):

    def __init__(self):
        inst_to_write = ''
        self.names_to_save = [
           'tab_action', 
           'tab_class', 
           'tab_model', 
           'row_id', 
        ]
        self.save_val_flags     = [ 0, 0, 0, 0, ]
        self.save_shadow_flags  = [ 0, 0, 0, 0, ]
    
    def creation_info_to_db(self):
        self.inst_to_write.create_date = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        self.inst_to_write.created_by = CustomUser.objects.get(
            id=self.request.user.id
        )

    # for transactions
    def recalc_money_field(self):
        money = Decimal(0.00)
        for goodsline in Goodsline.objects.filter(
            root_transaction=self.inst_to_write
        ):
            money += goodsline.qty * goodsline.price 
        self.inst_to_write.money = money

    # for goodslines
    def recalc_total_fields(self):
        self.inst_to_write.total = ( 
            Decimal(self.inst_to_write.qty) 
            * Decimal(self.inst_to_write.price)
        )
        self.inst_to_write.ship_total = ( 
            Decimal(self.inst_to_write.qty) 
            * Decimal(self.inst_to_write.ship_price)
        )

    # will be diff.for any child classes
    #def req_to_db(self):   

    # generally no need for any context in save case
    #def make_context(self):

    def context_to_html(self):
        return OK_SAVE_RESPONSE


#
# classes for 'save' 'new' cases
#
class SavedNewStd(SavedStd):

    def __init__(self):
        super().__init__()

    def req_to_db(self):   
        self.inst_to_write = self.row_model()
        # loop to get vals|shadow_ids over request or it's part
        for var_name in (
                arr_x_masks(self.names_to_save, self.save_val_flags)
                + arr_x_masks(self.names_to_save, self.save_shadow_flags)
        ):
            try:
                val = self.req_post[var_name] if self.req_post[var_name] else '' 
            except:
                val = ''
            db_put_val_or_shadow(self.inst_to_write, var_name, val)
        # add manually
        self.creation_info_to_db()
        # N.B. save() must be set in child not here
        ####   self.inst_to_write.save()


class SavedNewPartner(SavedNewStd, SavedCommonPartner):

    def __init__(self):
        SavedNewStd.__init__(self)
        SavedCommonPartner.__init__(self)

    # save() must be here
    def req_to_db(self):
        super().req_to_db()
        self.inst_to_write.save()


class SavedNewMaterial(SavedNewStd, SavedCommonMaterial):

    def __init__(self):
        SavedNewStd.__init__(self)
        SavedCommonMaterial.__init__(self)

    # save() must be here
    def req_to_db(self):
        super().req_to_db()
        self.inst_to_write.save()


class SavedNewTransaction(SavedNewStd, SavedCommonTransaction):

    def __init__(self):
        SavedNewStd.__init__(self)
        SavedCommonTransaction.__init__(self)

    # for all but shipping transactions get bookacc.pairs from request
    # for shipping it will be overwritten
    def set_bookacc_pairs(self):
        self.book_acc_pairs = json.loads(self.req_post['book_acc_pairs'])

    # for all but shipping minor transactions get goodlines from request
    # for shipping minor acc.pairs it will be overwritten with empty array
    def set_goodslines(self):
        self.goodslines = json.loads(self.req_post['goodslines'])

    # make new human_id by default or find existing one if minor shipping
    def make_human_id(self):
        human_id_inst = HumanId()
        human_id_inst.num = self.req_post['human_id'] 
        return human_id_inst

    # override the method(transaction has extra fields to set manually)
    # save() must be in the method
    def req_to_db(self):
        # special check for employee's field 
        if not fix_employee_val(self): return
        # make human_id inst.and set its value manually
        human_id_inst = self.make_human_id()
        # loop over book-acc.pairs
        # every iter.=independent transaction
        self.set_bookacc_pairs()
        for book_acc_pair in self.book_acc_pairs:
            if not book_acc_pair[0] or not book_acc_pair[1]: continue
            # add to db std values
            super().req_to_db()
            # add manually
            db_put_val_or_shadow(
                self.inst_to_write, 'deb_account', book_acc_pair[0]
            )
            db_put_val_or_shadow(
                self.inst_to_write, 'cred_account', book_acc_pair[1]
            )
            self.inst_to_write.has_goodslines = HotTransaction.objects.get(
                    id=self.req_post['hot_transaction']
            ).has_goodslines
            self.inst_to_write.human_id = human_id_inst 
            # save human_id inst.inside the loop only(=not empty book-acc.pair) 
            human_id_inst.save()
            # wait until it really saves
            while not HumanId.objects.get(id=human_id_inst.id):
                pass
            self.inst_to_write.save()
            # now to goodslines
            # if it's goodslines-containing transaction 
            if self.inst_to_write.has_goodslines:
                self.set_goodslines()
                for goodsline_branch in self.goodslines:
                    req_post_apart = dict.copy(self.request.POST)
                    req_post_apart.update(goodsline_branch)
                    # N.B. use all 3 args
                    SavedNewGoodsline.as_html()(
                        self.request, req_post_apart, self.inst_to_write
                    )
                # recalc.transaction's money field manually
                self.recalc_money_field()
                self.inst_to_write.save()

    # for shipping rewrite the pIvot as_view's subfunction 
    def make_html_resp(self, request):
        # if shipping ignore book-accs.array and make special savings
        if (request.POST['hot_transaction'] == str(SHIPPING_HOT_ID)
            and self.__class__.__name__ == 'SavedNewTransaction'
        ):
            # save major shipping transaction
            SavedNewShipping0().make_html_resp(request)
            # save minor shipping transactions
            SavedNewShipping1().make_html_resp(request)
            return SavedNewShipping2().make_html_resp(request)
        # else process request with transaction data as usually
        else:
            return SavedNewStd.make_html_resp(self, request)


class SavedNewShipping0(SavedNewTransaction):

    def __init__(self):
        SavedNewTransaction.__init__(self)

    # override bookacc.pairs
    def set_bookacc_pairs(self):
        self.book_acc_pairs = [ SHIPPING_ACC_PAIR_IDS[0], ]

    def recalc_money_field(self):
        ship_total = Decimal(0.00)
        for goodsline in Goodsline.objects.filter(
            root_transaction=self.inst_to_write
        ):
            ship_total += Decimal(goodsline.ship_price * goodsline.qty)
        self.inst_to_write.money = ship_total


class SavedNewShipping1(SavedNewTransaction):

    def __init__(self):
        SavedNewTransaction.__init__(self)

    # override bookacc.pairs
    def set_bookacc_pairs(self):
        self.book_acc_pairs = [ SHIPPING_ACC_PAIR_IDS[1], ]

    def recalc_money_field(self):
        total = Decimal(0.00)
        # N.B. on creation human_id from frontend = value, not id
        for goodsline in Goodsline.objects.filter(
            # reference to major shipping transaction identified by 3 items
            root_transaction = Transaction.objects.get(
                human_id=HumanId.objects.get(
                    num=self.request.POST['human_id']
                ),
                deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
            )
        ):
            total += Decimal(goodsline.price * goodsline.qty)
        self.inst_to_write.money = total

    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            num=self.req_post['human_id']
        )


class SavedNewShipping2(SavedNewTransaction):

    def __init__(self):
        SavedNewTransaction.__init__(self)

    # override bookacc.pairs
    def set_bookacc_pairs(self):
        self.book_acc_pairs = [ SHIPPING_ACC_PAIR_IDS[2], ]

    # N.B. on creation human_id from frontend = value, not id
    def recalc_money_field(self):
        total = ship_total = Decimal(0.00)
        for goodsline in Goodsline.objects.filter(
            # reference to major shipping transaction identified by 3 items
            root_transaction = Transaction.objects.get(
                human_id=HumanId.objects.get(
                    num=self.request.POST['human_id']
                ),
                deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
            )
        ):
            total += Decimal(goodsline.price * goodsline.qty)
            ship_total += Decimal(goodsline.ship_price * goodsline.qty)
        self.inst_to_write.money = ship_total - total
    
    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            num=self.req_post['human_id']
        )


class SavedNewGoodsline(SavedNewStd, SavedCommonGoodsline):

    def __init__(self):
        SavedNewStd.__init__(self)
        SavedCommonGoodsline.__init__(self)

    # overriding the method
    # save() must be in the method
    def req_to_db(self):
        # make human_id inst.and set its value manually
        human_id_inst = HumanId()
        human_id_inst.num = self.req_post['human_id'] 
        # add to db std values
        super().req_to_db()
        # add manually
        self.inst_to_write.root_transaction = self.root_transaction
        self.inst_to_write.human_id = human_id_inst 
        # transform purchase field if empty
        purchase_human_id = self.req_post['purchase_human_id'] 
        self.inst_to_write.purchase_human_id = human_id_inst.num if (
            not purchase_human_id
        ) else purchase_human_id
        # recalc.manually
        self.recalc_total_fields()
        # 
        human_id_inst.save()
        self.inst_to_write.save()


#
# classes for 'save' 'edit' cases
#
class SavedEditStd(SavedStd):

    # table values to (re)write
    def __init__(self):
        super().__init__()
        # for make_killed_copy
        self.extra_vars_to_kill = []
        # to make root_transaction for killed-goodsline
        self.killed_model_inst = '' 
    
    # part of req_to_db
    def get_model_insts(self):
        return self.row_model.objects.get(
            id=self.req_post['row_id']
        )

    # part of req_to_db
    def make_killed_copy(self, inst_to_write):  # returns killed-copy inst.
        killed_model_inst = globals()[
            killed_model_prefix + inst_to_write.__class__.__name__
        ]()
        #set some fields manually, not from old inst.
        killed_model_inst.created_by = inst_to_write.created_by
        killed_model_inst.create_date = inst_to_write.create_date
        #set current killer and date
        killed_model_inst.killed_by = CustomUser.objects.get(
            id=self.request.user.id
        )
        killed_model_inst.kill_date = datetime.now().strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        # copy old data to new "killed" instance
        for var_name in (
                arr_x_masks(self.names_to_save, self.save_val_flags)
                + arr_x_masks(self.names_to_save, self.save_shadow_flags)
                # added manually
                + self.extra_vars_to_kill
        ):
            db_put_val_or_shadow(
                killed_model_inst, 
                var_name,
                db_get_val_or_shadow(inst_to_write, var_name)
            )
        killed_model_inst.save()
        return killed_model_inst

    # part of req_to_db
    def check_if_new(self):
        data_is_new = False
        for var_name in (
                arr_x_masks(self.names_to_save, self.save_val_flags)
                + arr_x_masks(self.names_to_save, self.save_shadow_flags)
        ):
            try:
                val = self.req_post[var_name] if self.req_post[var_name] else '' 
            except:
                val = ''
            if db_get_val_or_shadow(self.inst_to_write, var_name) == val:
                continue
            else:
                data_is_new = True
        return data_is_new

    # part of req_to_db
    def save_vals_from_list(self):
        for var_name in (
                arr_x_masks(self.names_to_save, self.save_val_flags)
                + arr_x_masks(self.names_to_save, self.save_shadow_flags)
        ):
            try:
                val = self.req_post[var_name] if self.req_post[var_name] else '' 
            except:
                val = ''
            db_put_val_or_shadow(self.inst_to_write, var_name, val)

    # here in not-new case will be extra check if data is really new
    def req_to_db(self): # this time it must return data_is_new flag
        self.inst_to_write = self.get_model_insts()
        # 1at loop to check if req's vals|shadow_ids are really new
        data_is_new = self.check_if_new()
        # if nothing's new exit
        if not data_is_new: 
            return data_is_new
        # make killed copy for current model instance and save result
        self.killed_model_inst = self.make_killed_copy(self.inst_to_write)
        # 2nd loop to save req's vals|shadow_ids to db
        self.save_vals_from_list()
        # add manually
        self.creation_info_to_db()
        # N.B. save() must be set in child not here
        return data_is_new


class SavedEditPartner(SavedEditStd, SavedCommonPartner):

    def __init__(self):
        SavedEditStd.__init__(self)
        SavedCommonPartner.__init__(self)

    # no killed copies for the class
    def make_killed_copy(self, inst_to_write):
        return ''

    # save() must be here
    def req_to_db(self):
        # save if data_is_new
        was_data_saved = super().req_to_db()
        if was_data_saved:
            self.inst_to_write.save()


class SavedEditMaterial(SavedEditStd, SavedCommonMaterial):

    def __init__(self):
        SavedEditStd.__init__(self)
        SavedCommonMaterial.__init__(self)

    # no killed copies for the class
    def make_killed_copy(self, inst_to_write):
        return ''

    # save() must be here
    def req_to_db(self):
        was_data_saved = super().req_to_db()
        if was_data_saved:
            self.inst_to_write.save()


class SavedEditTransaction(SavedEditStd, SavedCommonTransaction):

    def __init__(self):
        SavedEditStd.__init__(self)
        SavedCommonTransaction.__init__(self)
        # new field, will be nessesary for goodlines-containing transaction
        self.killed_goodslines = ()
        # for make_killed_copy
        self.extra_vars_to_kill = [ 
            'deb_account', 'cred_account', 'has_goodslines', 'human_id', 
        ]

    # rewrite the part of req_to_db: check if linked goodslines are new as well
    def check_if_new(self):
        # call std check for new vals first
        data_is_new = SavedEditStd.check_if_new(self)
        if (not data_is_new     # and no goodslines
            and not json.loads(self.req_post['goodslines'])
        ): 
            return data_is_new
        # compare the lists of linked goodlines, for that
        # get from db 
        db_goodslines = Goodsline.objects.filter(
            root_transaction=Transaction.objects.get(id=self.inst_to_write.id)
        )
        self.db_goodslines_ids = [ str(i.id) for i in db_goodslines ]
        # get from frontend
        req_goodslines_ids = [ 
            goodsline_dict['row_id']
            for goodsline_dict in json.loads(self.req_post['goodslines'])
        ]
        # and compare
        if set(self.db_goodslines_ids) != set(req_goodslines_ids): 
            data_is_new = True
        # for data_is_new calc.killed goodslines tuple
        if data_is_new:
            self.killed_goodslines_ids = tuple(
                set(self.db_goodslines_ids).difference( set(req_goodslines_ids) )
            )
            self.left_goodslines_ids = tuple(
                set(self.db_goodslines_ids).intersection( set(req_goodslines_ids) )
            )
        return data_is_new

    def make_goodslines_kill_copies(self):
        for killed_id in self.killed_goodslines_ids:
            # then make killed_copy
            req_post_apart = dict.copy(self.request.POST)
            req_post_apart.update({'row_id': killed_id })
            # add manually root_transaction var(=just created killed-trans.)
            req_post_apart.update({
                'root_transaction': str(self.killed_model_inst.id)
            })
            KilledEditGoodsline.as_html()(
                self.request, req_post_apart,
                Goodsline.objects.get(id=killed_id)
            )
        # edit-only(not killed) part of the method
        for killed_id in self.left_goodslines_ids:
            # then make killed_copy
            req_post_apart = dict.copy(self.request.POST)
            req_post_apart.update({'row_id': killed_id })
            # add manually root_transaction var(=just created killed-trans.)
            req_post_apart.update({
                'root_transaction': str(self.killed_model_inst.id)
            })
            NotKilledEditGoodsline.as_html()(
                self.request, req_post_apart,
                Goodsline.objects.get(id=killed_id)
            )

    # rewrite the part of req_to_db
    def save_vals_from_list(self):
        # call std save(for no goodslines)
        SavedEditStd.save_vals_from_list(self)
        # if it's goodslines-containing transaction 
        if self.inst_to_write.has_goodslines:
            # now to goodslines
            # add new goodslines
            for goodsline_branch in json.loads(
                    self.req_post['goodslines']
            ):
                req_post_apart = dict.copy(self.request.POST)
                req_post_apart.update(goodsline_branch)
                # if this branch's row_id=0 then add new goodsline
                if goodsline_branch['row_id'] == '0':
                    # N.B. use all 3 args
                    SavedNewGoodsline.as_html()(
                        self.request, req_post_apart, self.inst_to_write
                    )
            # del killed-goodslines
            self.make_goodslines_kill_copies()
            # recalc.transaction's money field manually
            self.recalc_money_field()

    # save() must be here
    def req_to_db(self):
        # special check for employees-only transaction
        if not fix_employee_val(self): return
        was_data_saved = SavedEditStd.req_to_db(self)
        # special check-and-save for book_acc_pairs
        book_acc_pairs = json.loads(self.req_post['book_acc_pairs'])
        new_deb_acc = BookAccount.objects.get(id=book_acc_pairs[0][0])
        new_cred_acc = BookAccount.objects.get(id=book_acc_pairs[0][1])
        if ( new_deb_acc != self.inst_to_write.deb_account
            or new_cred_acc != self.inst_to_write.cred_account
        ):
            # if the flag not set yet make killedcopy
            if not was_data_saved:
                SavedEditStd.make_killed_copy(self, self.inst_to_write)
            # and set it anyway and set new values
            was_data_saved = True
            self.inst_to_write.deb_account = new_deb_acc
            self.inst_to_write.cred_account = new_cred_acc
        #
        if was_data_saved:
            self.inst_to_write.save()

    # for shipping rewrite the pIvot as_view's subfunction 
    def make_html_resp(self, request):
        # if shipping ignore book-accs.array and make special savings
        if (request.POST['hot_transaction'] == str(SHIPPING_HOT_ID)
            and self.__class__.__name__ == 'SavedEditTransaction'
        ):
            # save major shipping transaction
            SavedEditShipping0().make_html_resp(request)
            # save minor shipping transactions
            SavedEditShipping1().make_html_resp(request)
            SavedEditShipping2().make_html_resp(request)
            return OK_SAVE_RESPONSE
        # else process request with transaction data as usually
        else:
            return SavedEditStd.make_html_resp(self, request)


class SavedEditShipping0(SavedEditTransaction):

    def __init__(self):
        SavedEditTransaction.__init__(self)

    # take the following methods from 'new' sisterclass
    def set_bookacc_pairs(self):
        SavedNewShipping0.set_bookacc_pairs(self)

    def recalc_money_field(self):
        SavedNewShipping0.recalc_money_field(self)


class SavedEditShipping1(SavedEditTransaction):

    def __init__(self):
        SavedEditTransaction.__init__(self)

    # override bookacc.pairs
    def set_bookacc_pairs(self):
        self.book_acc_pairs = [ SHIPPING_ACC_PAIR_IDS[1], ]

    # the model inst.is not as for major shipping
    def get_model_insts(self):
        return Transaction.objects.get(
            human_id=HumanId.objects.get(
                id=self.request.POST['human_id']
            ),
            deb_account=SHIPPING_ACC_PAIR_OBJS[1][0],
            cred_account=SHIPPING_ACC_PAIR_OBJS[1][1]
        )

    def recalc_money_field(self):
        total = Decimal(0.00)
        for goodsline in Goodsline.objects.filter(
            # reference to major shipping transaction identified by 3 items
            root_transaction = Transaction.objects.get(
                human_id=HumanId.objects.get(
                    id=self.request.POST['human_id']
                ),
                deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
            )
        ):
            total += Decimal(goodsline.price * goodsline.qty)
        self.inst_to_write.money = total

    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            num=self.req_post['human_id']
        )


class SavedEditShipping2(SavedEditTransaction):

    def __init__(self):
        SavedEditTransaction.__init__(self)

    # override bookacc.pairs
    def set_bookacc_pairs(self):
        self.book_acc_pairs = [ SHIPPING_ACC_PAIR_IDS[2], ]

    # the model inst.is not as for major shipping
    def get_model_insts(self):
        return Transaction.objects.get(
            human_id=HumanId.objects.get(
                id=self.request.POST['human_id']
            ),
            deb_account=SHIPPING_ACC_PAIR_OBJS[2][0],
            cred_account=SHIPPING_ACC_PAIR_OBJS[2][1]
        )

    # N.B. on creation human_id from frontend = value, not id
    def recalc_money_field(self):
        total = ship_total = Decimal(0.00)
        for goodsline in Goodsline.objects.filter(
            # reference to major shipping transaction identified by 3 items
            root_transaction = Transaction.objects.get(
                human_id=HumanId.objects.get(
                    id=self.request.POST['human_id']
                ),
                deb_account=SHIPPING_ACC_PAIR_OBJS[0][0],
                cred_account=SHIPPING_ACC_PAIR_OBJS[0][1]
            )
        ):
            total += Decimal(goodsline.price * goodsline.qty)
            ship_total += Decimal(goodsline.ship_price * goodsline.qty)
        self.inst_to_write.money = ship_total - total
    
    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            id=self.req_post['human_id']
        )


#
# classes for 'killed' 'edit' cases
#
class KilledEditStd(SavedEditStd):

    # table values to (re)write
    def __init__(self):
        super().__init__()
            
    def make_killed_copy(self, inst_to_write):  # returns killed-copy inst.
        return SavedEditStd.make_killed_copy(self, inst_to_write)

    def get_model_inst(self):
        return self.row_model.objects.get(
            id=self.req_post['row_id']
        )

    # main part of make_context() for "kill" case
    def req_to_db(self):
        self.inst_to_write = self.get_model_inst()
        # make killed copy for current model instance
        self.killed_model_inst = self.make_killed_copy(self.inst_to_write)
        # N.B. delete() must be set in child not here


class KilledEditPartner(KilledEditStd, SavedCommonPartner):

    def __init__(self):
        KilledEditStd.__init__(self)
        SavedCommonPartner.__init__(self)

    # no killed copies for the class
    def make_killed_copy(self, inst_to_write):
        return ''

    # delete() must be here
    def req_to_db(self):
        # save if data_is_new
        super().req_to_db()
        self.inst_to_write.delete()


class KilledEditMaterial(KilledEditStd, SavedCommonPartner):

    def __init__(self):
        KilledEditStd.__init__(self)
        SavedCommonMaterial.__init__(self)

    # no killed copies for the class
    def make_killed_copy(self, inst_to_write):
        return ''

    # delete() must be here
    def req_to_db(self):
        # save if data_is_new
        super().req_to_db()
        self.inst_to_write.delete()


class KilledEditTransaction(KilledEditStd, SavedCommonTransaction):

    def __init__(self):
        KilledEditStd.__init__(self)
        SavedCommonTransaction.__init__(self)
        # for make_killed_copy
        self.extra_vars_to_kill = [ 
            'deb_account', 'cred_account', 'has_goodslines', 'human_id', 
        ]

    def make_killed_copy(self, inst_to_write):
        # take the method from 'save' case
        return SavedEditTransaction.make_killed_copy(
            self, self.inst_to_write
        )

    def make_goodslines_kill_copies(self):
        for killed_id in self.killed_goodslines_ids:
            # then make killed_copy
            req_post_apart = dict.copy(self.request.POST)
            req_post_apart.update({'row_id': killed_id })
            # add manually root_transaction var(=just created killed-trans.)
            req_post_apart.update({
                'root_transaction': str(self.killed_model_inst.id)
            })
            KilledEditGoodsline.as_html()(
                self.request, req_post_apart,
                Goodsline.objects.get(id=killed_id)
            )

    # delete() must be here
    def req_to_db(self):
        # save if data_is_new
        super().req_to_db()
        # for goodlines-containing transactions
        if self.inst_to_write.has_goodslines:
            # make killed-copies for all linked (in db) goodslines
            self.killed_goodslines_ids = [
                goodsline.id
                for goodsline in Goodsline.objects.filter(
                    root_transaction=self.inst_to_write
                )
            ]
            self.make_goodslines_kill_copies()
        # delete transaction itself
        self.inst_to_write.delete()
    
    # for shipping rewrite the pIvot as_view's subfunction 
    def make_html_resp(self, request):
        if ( self.__class__.__name__ == 'KilledEditTransaction'
            and str(
                Transaction.objects.get(
                    id=request.POST['row_id']
                ).hot_transaction.id
            ) == str(SHIPPING_HOT_ID)
        ):
            # kill minor shipping transactions
            KilledEditShipping1().make_html_resp(request)
            KilledEditShipping2().make_html_resp(request)
            # kill major shipping transaction
            KilledEditShipping0().make_html_resp(request)
            return OK_SAVE_RESPONSE
        # else process request with transaction data as usually
        else:
            return KilledEditStd.make_html_resp(self, request)


class KilledEditShipping0(KilledEditTransaction):

    def __init__(self):
        KilledEditTransaction.__init__(self)


class KilledEditShipping1(KilledEditTransaction):

    def __init__(self):
        KilledEditTransaction.__init__(self)

    # the model inst.is not as for major shipping
    def get_model_inst(self):
        return Transaction.objects.get(
            human_id=HumanId.objects.get(
                id=self.request.POST['human_id']
            ),
            deb_account=SHIPPING_ACC_PAIR_OBJS[1][0],
            cred_account=SHIPPING_ACC_PAIR_OBJS[1][1]
        )

    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            num=self.req_post['human_id']
        )


class KilledEditShipping2(KilledEditTransaction):

    def __init__(self):
        KilledEditTransaction.__init__(self)

    # the model inst.is not as for major shipping
    def get_model_inst(self):
        return Transaction.objects.get(
            human_id=HumanId.objects.get(
                id=self.request.POST['human_id']
            ),
            deb_account=SHIPPING_ACC_PAIR_OBJS[2][0],
            cred_account=SHIPPING_ACC_PAIR_OBJS[2][1]
        )

    def set_goodslines(self):
        self.goodslines = []

    # find existing human_id
    def make_human_id(self):
        return HumanId.objects.get(
            id=self.req_post['human_id']
        )


class KilledEditGoodsline(KilledEditStd, SavedCommonGoodsline):

    def __init__(self):
        KilledEditStd.__init__(self)
        SavedCommonGoodsline.__init__(self)
        # for make_killed_copy
        self.extra_vars_to_kill = [ 'human_id', ]

    def make_killed_copy(self, inst_to_write):
        # call std-edit's method first
        killed_model_inst = SavedEditStd.make_killed_copy(
            self, self.inst_to_write
        )
        # add root_transaction
        killed_model_inst.root_transaction = KilledTransaction.objects.get(
            id=self.req_post['root_transaction']
        )
        killed_model_inst.save()
        return killed_model_inst

    # delete() must be here
    def req_to_db(self):
        # save if data_is_new
        super().req_to_db()
        self.inst_to_write.delete()


class NotKilledEditGoodsline(KilledEditGoodsline):

    def __init__(self):
        KilledEditGoodsline.__init__(self)

    # no delete()
    def req_to_db(self):
        self.inst_to_write = self.get_model_insts()
        # make killed copy for current model instance and save result
        self.killed_model_inst = self.make_killed_copy(self.inst_to_write)
        # recalc.total fields
        self.killed_model_inst.total = ( 
            Decimal(self.killed_model_inst.qty) 
            * Decimal(self.killed_model_inst.price)
        )
        self.killed_model_inst.ship_total = ( 
            Decimal(self.killed_model_inst.qty) 
            * Decimal(self.killed_model_inst.ship_price)
        )
        self.killed_model_inst.save()


class KilledPacketTransaction(SavedNewStd):

    def __init__(self):
        super().__init__()

        self.names_to_save += [
           'sidebar_date1', 
           'sidebar_date2', 
        ]
        self.save_val_flags     += [ 0, 0, 0, ]
        self.save_shadow_flags  += [ 0, 0, 0, ]
    
    def req_to_db(self):   
        # get correct dates from request
        try:
            sidebar_date1 = self.req_post[
                'sidebar_date1'] if self.req_post['sidebar_date1'] else '' 
            sidebar_date2 = self.req_post[
                'sidebar_date2'] if self.req_post['sidebar_date2'] else '' 
        except:
            return
        if sidebar_date2 < sidebar_date1: return
        # find killed tr-ns(i.e.human_ids) by time interval 
        killed_transactions = KilledTransaction.objects.filter(
            Q( date__gte=datetime.strptime(sidebar_date1, '%Y-%m-%d').date() )
            & 
            Q( date__lte=datetime.strptime(sidebar_date2, '%Y-%m-%d').date() )
        )
        killed_human_ids = list(set(
            [ tr.human_id for tr in killed_transactions ]
        ))
        # same for killed goodslines
        killed_goodslines = KilledGoodsline.objects.filter(
            root_transaction__in=killed_transactions
        )
        killed_goodslines_human_ids = list(set(
            [ goodsline.human_id for goodsline in killed_goodslines ]
        ))
        # same for transactions
        transactions = Transaction.objects.filter(
            Q( date__gte=datetime.strptime(sidebar_date1, '%Y-%m-%d').date() )
            & 
            Q( date__lte=datetime.strptime(sidebar_date2, '%Y-%m-%d').date() )
        )
        tr_human_ids = list(set(
            [ tr.human_id for tr in transactions ]
        ))
        # same for goodslines
        goodslines = Goodsline.objects.filter(
            root_transaction__in=transactions
        )
        goodslines_human_ids = list(set(
            [ goodsline.human_id for goodsline in goodslines ]
        ))



