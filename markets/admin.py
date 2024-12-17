import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Market, Instrument, Payout, Trade

# Register your models here.


class ExportCsvMixin:
    """
    Mixin that provides functionality to export data as a CSV file.
    """

    def export_as_csv(self, request, queryset):
        """Exports the given queryset as a CSV file."""

        meta = self.model._meta
        field_names = list(self.list_display)
        field_names_clean = [name.replace("get_", "") for name in field_names]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_names_clean)
        for obj in queryset:
            result = []
            for field in field_names:
                attr = getattr(obj, field, None)
                if attr and callable(attr):
                    result.append(attr())
                elif attr:
                    result.append(attr)  
                else:
                    attr = getattr(self, field, None)
                    if attr:
                        result.append(attr(obj))
                    else:
                        result.append(attr)
            row = writer.writerow(result)

        return response

    export_as_csv.short_description = "Export To CSV"


class PayoutAdmin(admin.ModelAdmin, ExportCsvMixin):
    """
    Admin class for managing Payout objects in the Django admin interface.
    """
    list_display = ('market', 'user', 'amount', 'status')
    list_filter = ('status', 'market',)
    search_fields = ('user__email','market__name',)
    actions = ['pay', 'unpay', 'export_as_csv']


    def pay(self, request, queryset):
        for obj in queryset:
            obj.status = 'PAID'
            obj.save()
    
    def unpay(self, request, queryset):
        for obj in queryset:
            obj.status = 'PENDING'
            obj.save()
    
    pay.short_description = 'Mark as Paid'
    unpay.short_description = 'Mark as Pending'


class MarketAdmin(admin.ModelAdmin):
    """
    Admin class for managing Market objects in the Django admin interface.
    """

    readonly_fields = ('status','initial_yes_value')    
    exclude = ('n_exec_trades',)
    save_as = True
    list_display = ('name', 'status')
    list_filter = ('status',)
    actions = ['suspend', 'close', 'open', 'pending']
    actions_selection_counter = True
    
    read_only_by_status ={
        'PENDING': ('outcome',),
        'OPEN': ('initial_yes_value', 'opening_date', 'opening_time', 'outcome',),
        'CLOSED': ('initial_yes_value', 'opening_date', 'opening_time',),
    }

    def suspend(self, request, queryset):
        queryset.update(status='SUSPENDED') 

    def close(self, request, queryset):
        queryset.update(status='CLOSED')  

    def open(self, query, queryset):
        queryset.update(status='OPEN')  

    def pending(self, query, queryset):
        queryset.update(status='PENDING')  

    def get_readonly_fields(self, request, obj):
        """Dynamically determines the read-only fields based on the market status."""
        if obj is None:
            return self.readonly_fields + ('outcome',)
        elif obj.status == 'PENDING':
            return self.readonly_fields + ('outcome',)
        elif obj.status == 'OPEN':
            return self.readonly_fields + ('name','initial_yes_value','opening_date','opening_time','starting_funds','outcome',)
        elif obj.status == 'CLOSED':
            return self.readonly_fields + ('name','initial_yes_value','opening_date','opening_time','starting_funds',)
        elif obj.status == 'SETTLED':
            return self.readonly_fields + ('name','initial_yes_value','opening_date','opening_time','starting_funds',)
        return super().get_readonly_fields(request, obj)

    suspend.short_description = 'Suspend Markets'
    close.short_description = 'Close Markets'
    open.short_description = 'Open Selected Markets'
    pending.short_description = 'Set Selected Markets As Pending'

    def _get_outcomes(self, obj):
        """Retrieves the tradeable instruments for the given market."""
        instruments = obj._get_tradeable_instrs()
        return instruments

    def render_change_form(self, request, context, *args, **kwargs):
        """Customizes the rendering of the change form for Market objects."""
        obj = context.get('original')
        if obj is not None:
            try:
                context['adminform'].form.fields['outcome'].queryset = self._get_outcomes(obj)
            except KeyError:
                pass
        return super().render_change_form(request, context, *args, **kwargs)
    

class InstrumentAdmin(admin.ModelAdmin):
    """
    Admin class for managing Instrument objects in the Django admin interface.
    """
    list_display = ("get_market","name","price","price_upd_mt")
    readonly_fields = ('price',)
    list_filter = ('market',)

    def get_readonly_fields(self, request, obj = None):
        if obj and obj.name == "Cash":
            return self.readonly_fields + ('name',)
        return super().get_readonly_fields(request, obj)

    def get_market(self,obj):
        return obj.market.name
        
    get_market.short_description = "Market"


class TradeAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ("user", "get_market", "instrument","type", "get_shares_before", "shares","get_shares_after","price", "get_cash_before", "get_cash_after", "timestamp", "status")
    list_filter  = ("user",)
    search_fields = ("user__email","instrument__market__name","status",)
    actions = ["export_as_csv"]
    readonly_fields = ('type','market_time_seconds', 'user', 'instrument', 'shares', 'price', 'timestamp', 'status', 'trade_metadata', 'get_market', 'get_cash_before', 'get_cash_after', 'get_shares_before', 'get_shares_after',)
    list_per_page = 50

    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def get_market(self,obj):
        return obj.instrument.market.name

    def get_cash_before(self, obj):
        return obj.trade_metadata.cash_before

    def get_cash_after(self, obj):
        return obj.trade_metadata.cash_after

    def get_shares_before(self, obj):
        return obj.trade_metadata.shares_before

    def get_shares_after(self, obj):
        return obj.trade_metadata.shares_after

    get_market.short_description = "Market"
    get_cash_before.short_description = "Cash Before"
    get_cash_after.short_description = "Cash After"
    get_shares_before.short_description = "Shares Before"
    get_shares_after.short_description = "Shares After"

admin.site.register(Market, MarketAdmin)
admin.site.register(Instrument, InstrumentAdmin)
admin.site.register(Payout, PayoutAdmin)
admin.site.register(Trade, TradeAdmin)
