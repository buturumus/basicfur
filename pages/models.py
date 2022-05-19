from django.db import models

from datetime import date, datetime
import logging
#from builtins import True
#from treebeard.al_tree import AL_Node

from pages.msgs import *

# Create your models here.
from users.models import CustomUser

ATTEMPTS=10

# consts
for attempt in range(ATTEMPTS):
    try:
        NOBODY_USER = CustomUser.objects.get(username='nobody')
        NOBODY_USER_ID = CustomUser.objects.get(username='nobody').id
        break
    except:
        # some primitive garbage for pre-migration state
        NOBODY_USER = ''
        NOBODY_USER_ID = 1
        # and attepmt to init with normal vals
        CustomUser.default_init()


# model classes 

class HumanId(models.Model):
    id = models.AutoField(primary_key=True)
    num = models.IntegerField(default = 0)
    
    def __str__(self):
        return str(self.num)
    

class BookAccount(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    short_name = models.CharField(max_length=32, default = '')
    is_passive = models.SmallIntegerField(default=0)

    def __str__(self):
        return self.short_name + ' - ' + MSGS['bacc_' + self.short_name][lc_id]

    @staticmethod
    def get_default_set():
        return (
            '00', '05', '06', '20', '41', '46', '50/1', '51', 
            '62', '71', '72/1', '80', '80/1',
        )

    @classmethod
    def default_init(cls):
        for short_name in cls.get_default_set():
            book_acc = cls()
            book_acc.name = 'bacc_' + short_name
            book_acc.short_name = short_name
            book_acc.save()

    @classmethod
    def check_defaults(cls):
        try:
            for name in cls.get_default_set():
                obj = cls.objects.get(short_name=name)
        except:
            cls.objects.all().delete()
            cls.default_init()

class HotTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, default = '_')
    name_id = models.CharField(max_length=128, default = '_')
    deb_account = models.ForeignKey(BookAccount, 
        related_name = 'hot_transaction_deb',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    cred_account = models.ForeignKey(BookAccount, 
        related_name = 'hot_transaction_cred',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    has_goodslines = models.SmallIntegerField(default=0)
    is_employees_action = models.IntegerField(default = 0)

    def __str__(self):
        return str(
            MSGS[self.name_id][lc_id]
        )

    @staticmethod
    def get_default_set():
        return (
            # name_id, deb_account, cred_account, has_goodln., is_empl.
            ('hot_tr_service',              '00', '00', 0, 0 ), 
            ('hot_tr_shipping',             '62', '46', 1, 0 ), 
            ('hot_tr_mat_to_prod',          '20', '05', 1, 0 ),
            ('hot_tr_get_invoice',          '80', '62', 0, 0 ),
            ('hot_tr_make_invoice',         '62', '80', 0, 0 ),
            ('hot_tr_from_bank',            '62', '51', 0, 0 ), 
            ('hot_tr_to_bank',              '51', '62', 0, 0 ), 
            ('hot_tr_to_stock',             '41', '20', 1, 0 ), 
            ('hot_tr_consumable_purchase',  '06', '62', 1, 0 ),
            ('hot_tr_mat_purchase',         '05', '62', 1, 0 ),
            ('hot_tr_pay_salary',           '71', '50/1', 0, 1 ), 
            ('hot_tr_calc_salary',          '80', '71', 0, 1 ),
            ('hot_tr_accountable_cache_out',    '72/1', '50/1', 0, 1 ),
            ('hot_tr_accountable_cache_return', '50/1', '72/1', 0, 1 ), 
            ('hot_tr_accountable_cache_spent',  '62', '72/1', 0, 1 ),
            ('hot_tr_cache_out',            '62', '50/1', 0, 0 ),
            ('hot_tr_cache_in',             '50/1', '62', 0, 0 ),
            ('hot_tr_empty',                '00', '00', 0, 0 ),
        )
    
    @classmethod
    def default_init(cls):
        for hot_tr_fields in cls.get_default_set():
            hot_transaction = cls()
            hot_transaction.name_id = hot_tr_fields[0]
            hot_transaction.deb_account = BookAccount.objects.get(
                short_name=hot_tr_fields[1]
            )
            hot_transaction.cred_account = BookAccount.objects.get(
                short_name=hot_tr_fields[2]
            )
            hot_transaction.has_goodslines = hot_tr_fields[3]
            hot_transaction.is_employees_action = hot_tr_fields[4]
            hot_transaction.save()

    @classmethod
    def check_defaults(cls):
        try:
            for hot_tr_fields in cls.get_default_set():
                hot_tr = cls.objects.get(name_id=hot_tr_fields[0])
        except:
            cls.objects.all().delete()
            cls.default_init()


class PartnerGroup(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, default = '_')
    name_id = models.CharField(max_length=50, default = '_')

    def __str__(self):
        return MSGS[self.name_id][lc_id]

    @staticmethod
    def get_default_set():
        return (
            'partner_gr_nogroup', 'partner_gr_employees',
        )

    @classmethod
    def default_init(cls):
        for name_id in cls.get_default_set():
            # ignore in in pre-migration state
            try:
                partner_group = cls()
                partner_group.name_id = name_id
                partner_group.save()
            except:
                return

    @classmethod
    def check_defaults(cls):
        try:
            for name in cls.get_default_set():
                obj = cls.objects.get(name_id=name)
        except:
            cls.objects.all().delete()
            cls.default_init()


# consts
for attempt in range(ATTEMPTS):
    try:
        NOGROUP_GROUP = PartnerGroup.objects.get(name_id='partner_gr_nogroup')
        NOGROUP_GROUP_ID = NOGROUP_GROUP.id
        break
    except:
        # some primitive garbage for pre-migration state
        NOGROUP_GROUP = ''
        NOGROUP_GROUP_ID = 1
        # and attepmt to init with normal vals
        PartnerGroup.default_init()


class Partner(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, blank = True)
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    partner_group = models.ForeignKey(
        PartnerGroup,
        related_name = 'partner_group',
        default = NOGROUP_GROUP_ID,
        on_delete=models.CASCADE
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'partner_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    @staticmethod
    def get_default_set():
        return (
        )

    @classmethod
    def default_init(cls):
        for name in cls.get_default_set():
            partner = cls()
            partner.name = name
            partner.save()

    @classmethod
    def check_defaults(cls):
        try:
            for name in cls.get_default_set():
                obj = cls.objects.get(name_id=name)
        except:
            cls.objects.all().delete()
            cls.default_init()
            

class Material(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256) 
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'material_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Transaction(models.Model):
    id = models.AutoField(primary_key=True)
    human_id = models.ForeignKey(HumanId,
        related_name = 'transaction_human_id',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    money = models.DecimalField(max_digits=15, decimal_places = 2, default = 0.0)
    has_goodslines = models.SmallIntegerField(default=0)
    hot_transaction = models.ForeignKey(HotTransaction,
        related_name = 'transaction_hot_transactions',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    date = models.DateField()
    partner = models.ForeignKey(Partner,
        related_name = 'transaction_partner',
        on_delete=models.CASCADE)
    employee = models.ForeignKey(Partner,
        related_name = 'transaction_employee',
        default = 1,
        on_delete=models.CASCADE)
    deb_account = models.ForeignKey(BookAccount, 
        related_name = 'transaction_debs',
        on_delete=models.CASCADE)
    cred_account = models.ForeignKey(BookAccount, 
        related_name = 'transaction_creds',
        on_delete=models.CASCADE)
    comment = models.CharField(max_length=256, blank = True)
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'transaction_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)

    def __str__(self):
        return self.comment


class KilledTransaction(models.Model):
    id = models.AutoField(primary_key=True)
    human_id = models.ForeignKey(HumanId,
        related_name = 'killed_transaction_human_id',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    money = models.DecimalField(max_digits=15, decimal_places = 2, default = 0.0)
    has_goodslines = models.SmallIntegerField(default=0)
    hot_transaction = models.ForeignKey(HotTransaction,
        related_name = 'killed_transaction_hot_transactions',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    date = models.DateField()
    partner = models.ForeignKey(Partner,
        related_name = 'killed_transaction_partner',
        on_delete=models.CASCADE)
    employee = models.ForeignKey(Partner,
        related_name = 'killed_transaction_employee',
        default = 1,
        on_delete=models.CASCADE)
    deb_account = models.ForeignKey(BookAccount, 
        related_name = 'killed_transaction_debs',
        on_delete=models.CASCADE)
    cred_account = models.ForeignKey(BookAccount, 
        related_name = 'killed_transaction_creds',
        on_delete=models.CASCADE)
    comment = models.CharField(max_length=256, blank = True)
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'killed_transaction_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)
    kill_date = models.DateTimeField(default = '1970-01-01')
    killed_by = models.ForeignKey('users.CustomUser',
        related_name = 'killed_transaction_killed_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)
    
    def __str__(self):
        return self.comment


class Goodsline(models.Model):
    id = models.AutoField(primary_key=True)
    root_transaction = models.ForeignKey(Transaction,
        related_name = 'goodsline_root_transaction',
        null = True,
        blank = True,
        on_delete=models.CASCADE
    )
    human_id = models.ForeignKey(HumanId,
        related_name = 'goodsline_human_id',
        null = True,
        blank = True,
        on_delete=models.CASCADE
    )
    purchase_human_id = models.CharField(max_length=32, blank = True, default='')
    material = models.ForeignKey(Material,
        related_name = 'goodsline_material',
        default = 1,
        on_delete=models.CASCADE
    )
    comment = models.CharField(max_length=256, blank = True)
    qty = models.DecimalField(max_digits=15, decimal_places = 3, default = 0)
    price = models.DecimalField(max_digits=15, decimal_places = 4, default = 0.00)
    ship_price = models.DecimalField( 
        max_digits=15, decimal_places = 2, default = 0.00
    )
    total = models.DecimalField(max_digits=15, decimal_places = 2, default = 0.00)
    ship_total = models.DecimalField(
        max_digits=15, decimal_places = 2, default = 0.00
    )
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'goodsline_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return str(self.human_id)


class GoodslinesSummable(models.Model):
    total = Goodsline.total
    ship_total = Goodsline.ship_total

    def __str__(self):
        return str(self.total)


class KilledGoodsline(models.Model):
    id = models.AutoField(primary_key=True)
    root_transaction = models.ForeignKey(KilledTransaction,
        related_name = 'killed_goodsline_root_transaction',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    human_id = models.ForeignKey(HumanId,
        related_name = 'killed_goodsline_human_id',
        null = True,
        blank = True,
        on_delete=models.CASCADE)
    purchase_human_id = models.CharField(max_length=32, blank = True, default='')
    material = models.ForeignKey(Material,
        related_name = 'killed_goodsline_material',
        default = 1,
        on_delete=models.CASCADE)
    comment = models.CharField(max_length=256, blank = True)
    qty = models.DecimalField(max_digits=15, decimal_places = 3, default = 0)
    price = models.DecimalField(max_digits=15, decimal_places = 2, default = 0.0)
    ship_price = models.DecimalField(
        max_digits=15, decimal_places = 2, default = 0.0
    )
    total = models.DecimalField(max_digits=15, decimal_places = 2, default = 0.0)
    ship_total = models.DecimalField(
        max_digits=15, decimal_places = 2, default = 0.0
    )
    create_date = models.DateTimeField(
        default = datetime(1970, 1, 1, 0, 0, 0, 0)
    )
    created_by = models.ForeignKey('users.CustomUser',
        related_name = 'killed_goodsline_created_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)
    kill_date = models.DateTimeField(default = '1970-01-01')
    killed_by = models.ForeignKey('users.CustomUser',
        related_name = 'killed_goodsline_killed_by',
        default = NOBODY_USER_ID,
        on_delete=models.CASCADE)

    def __str__(self):
        return str(self.human_id)


