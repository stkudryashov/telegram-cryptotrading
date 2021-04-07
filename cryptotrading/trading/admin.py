from django.contrib import admin
from trading.models import ProposalBtc, ExchangePoint


@admin.register(ProposalBtc)
class ProposalBtcAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_telegram_id', 'buy', 'point_name', 'date')
    list_display_links = ('id', 'user_telegram_id')


@admin.register(ExchangePoint)
class ExchangePointAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'stocks', 'sells')
    list_display_links = ('id', 'name')
