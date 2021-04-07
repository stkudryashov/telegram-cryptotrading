from django.db import models


class ProposalBtc(models.Model):
    user_telegram_id = models.CharField(max_length=16, verbose_name='user telegram id')  # Телеграмм для клиента
    buy = models.BooleanField(default=False)  # False - купить, True - продать
    is_count = models.BooleanField(default=False)  # Написал ли сумму
    count = models.FloatField(blank=True, null=True)  # Сумма
