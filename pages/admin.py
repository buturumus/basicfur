from django.contrib import admin

#from treebeard.admin import TreeAdmin
#from treebeard.forms import movenodeform_factory

from .models import *

# Register your models here.

class HotTransactionAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_id',)
    readonly_fields = ('id',)
admin.site.register(HotTransaction, HotTransactionAdmin)

class BookAccountAdmin(admin.ModelAdmin):
    list_display = ('name', )
admin.site.register(BookAccount, BookAccountAdmin)

class PartnerGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
admin.site.register(PartnerGroup, PartnerGroupAdmin)

class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', )
admin.site.register(Partner, PartnerAdmin)

class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', )
admin.site.register(Material, MaterialAdmin)

class HumanIdAdmin(admin.ModelAdmin):
    list_display = ('num', )
admin.site.register(HumanId, HumanIdAdmin)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('comment', )
    readonly_fields = ('id',)
admin.site.register(Transaction, TransactionAdmin)

class KilledTransactionAdmin(admin.ModelAdmin):
    list_display = ('comment', )
    readonly_fields = ('id',)
admin.site.register(KilledTransaction, KilledTransactionAdmin)

class GoodslineAdmin(admin.ModelAdmin):
    list_display = ('human_id', )
    readonly_fields = ('id',)
admin.site.register(Goodsline, GoodslineAdmin)

class KilledGoodslineAdmin(admin.ModelAdmin):
    list_display = ('human_id', )
    readonly_fields = ('id',)
admin.site.register(KilledGoodsline, KilledGoodslineAdmin)
