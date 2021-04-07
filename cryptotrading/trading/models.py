from django.db import models


class ProposalBtc(models.Model):
    user_telegram_id = models.CharField(max_length=16, verbose_name='user telegram id')  # Телеграмм для клиента
    is_number = models.BooleanField(default=False)  # Написал ли телефон
    user_number = models.CharField(max_length=16, verbose_name='user phone number', blank=True)  # Телефон
    buy = models.BooleanField(default=False)  # False - продать, True - купить
    is_count = models.BooleanField(default=False)  # Написал ли сумму
    count = models.FloatField(blank=True, null=True)  # Сумма
    is_point = models.BooleanField(default=False)  # Написал ли точку обмена
    point_name = models.CharField(max_length=16, verbose_name='exchange point', blank=True, null=True)  # Точка обмена
    date = models.DateTimeField(auto_now_add=True)  # Дата заявки
    date_visit = models.CharField(max_length=16, verbose_name='date of visit', blank=True, null=True)  # Дата визита

    def __str__(self):
        return '{}-{}'.format(self.user_telegram_id, self.point_name)

    class Meta:
        verbose_name = 'exchange request'
        verbose_name_plural = 'exchange requests'


class ExchangePoint(models.Model):
    name = models.CharField(max_length=16, verbose_name='exchange point')
    stocks = models.FloatField(default=0, verbose_name='how much is in stock')
    sells = models.FloatField(default=0, verbose_name='how much can sell')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'exchange point'
        verbose_name_plural = 'exchange points'
