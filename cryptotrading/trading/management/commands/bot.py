from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import Bot, Update

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.ext import CallbackContext, CallbackQueryHandler

from telegram.utils.request import Request

from datetime import datetime
from datetime import timedelta

import telepot
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton

from trading.models import ProposalBtc, ExchangePoint

import requests
from bs4 import BeautifulSoup


def btc_bot_new_messages(update: Update, context: CallbackContext):
    message = update.message.text

    user_telegram_id = update.message.chat_id
    bot = telepot.Bot(settings.TOKEN)

    if ProposalBtc.objects.filter(user_telegram_id=user_telegram_id).count() == 1:
        proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)

        if not proposal_btc.is_number:
            if len(message) < 11:
                bot_message = 'Я не понимаю твоего номера'
            else:
                proposal_btc.user_number = message
                proposal_btc.is_number = True
                proposal_btc.save()

                bot_message = 'Я запомнил твой номер :)\nТеперь напиши точку обмена'

            bot.sendMessage(user_telegram_id, bot_message)
        elif not proposal_btc.is_point:
            point_name = ExchangePoint.objects.filter(name=message)

            if point_name:
                proposal_btc.point_name = message
                proposal_btc.is_point = True
                proposal_btc.save()

                bot_message = 'Я нашел эту точку :)\nВыбери что тебя интересует'

                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text='Купить', callback_data='buy'),
                                      InlineKeyboardButton(text='Продать', callback_data='sell')]])

                bot.sendMessage(chat_id=user_telegram_id, text=bot_message, reply_markup=keyboard)
            else:
                bot_message = 'Я не смог найти такую точку :с\nПопробуй написать название точки еще раз'
                bot.sendMessage(user_telegram_id, bot_message)

        elif not proposal_btc.is_count:
            try:
                value = float(message.replace(',', '.'))
                exchange_point = ExchangePoint.objects.get(name=proposal_btc.point_name)

                if proposal_btc.buy:
                    exchange_point_value = exchange_point.sells
                else:
                    exchange_point_value = exchange_point.stocks

                if exchange_point_value < value:
                    bot_message = 'У точки нет столько денег :с'
                else:
                    proposal_btc.count = float(message.replace(',', '.'))
                    proposal_btc.is_count = True
                    proposal_btc.save()

                    bot_message = 'Все отлично, ваша заявка создана'
            except ValueError:
                bot_message = 'Я тебя не понял, попробуй написать сумму еще раз'

            bot.sendMessage(user_telegram_id, bot_message)
        else:
            pass
    else:
        if message == '/start' or message == 'начать':
            bot_message = 'Привет, я бот по обмену крипты :)\nДля начала напиши номер телефона'

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id,
            )

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message)
        else:
            bot_message = 'Я тебя не понял, воспользуйся кнопкой ниже, чтобы начать обмен'

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Начать', callback_data='start')]])

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message, reply_markup=keyboard)


def got_now_btc_run():
    # Биток к USD
    response = requests.get('https://www.rbc.ru/crypto/currency/btcusd')
    soup = BeautifulSoup(response.text, 'html.parser')
    btc_usd = soup.find('div', attrs={'class': 'chart__subtitle js-chart-value'})
    btc_usd = btc_usd.contents[0].replace(' ', '').replace('\n', '').replace(',', '.')
    btc_usd = float(btc_usd)

    # USD к рублю
    response = requests.get('https://quote.rbc.ru/ticker/59111')
    soup = BeautifulSoup(response.text, 'html.parser')
    rub_usd = soup.find('span', attrs={'class': 'chart__info__sum'}).text
    rub_usd = rub_usd.replace('₽', '').replace(',', '.')
    rub_usd = float(rub_usd)

    btc_rub = btc_usd * rub_usd
    return btc_rub


def btc_bot_edit_messages(update: Update, context: CallbackContext):
    query = update.callback_query

    button_press = query.data
    edit_message = (query.message.chat_id, query.message.message_id)

    user_telegram_id = query.message.chat_id
    bot = telepot.Bot(settings.TOKEN)

    if 'start' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            bot_message = 'Привет, я бот по обмену крипты :)\nДля начала напиши номер телефона'

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id,
            )

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message)
    elif 'buy' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)
            percent = got_now_btc_run() * ExchangePoint.objects.get(name=proposal_btc.point_name).percent_sell

            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB\n\n".format(round(got_now_btc_run() - percent, 2))
            bot_text += "На какую сумму ₽ хотите купить BTC?"

            proposal_btc.buy = True
            proposal_btc.save()

            bot.sendMessage(chat_id=user_telegram_id, text=bot_text)
    elif 'sell' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)
            percent = got_now_btc_run() * ExchangePoint.objects.get(name=proposal_btc.point_name).percent_buy

            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB\n\n".format(round(got_now_btc_run() + percent, 2))
            bot_text += "На какую сумму ₽ хотите продать BTC?"

            bot.sendMessage(chat_id=user_telegram_id, text=bot_text)


class Command(BaseCommand):
    help = 'Crypto Trading Bot'

    def handle(self, *args, **options):
        request = Request(connect_timeout=0.5, read_timeout=1.0)
        bot = Bot(request=request, token=settings.TOKEN, base_url=settings.PROXY_URL)

        updater = Updater(bot=bot)

        btc_handler = CommandHandler('start', btc_bot_new_messages)
        updater.dispatcher.add_handler(btc_handler)

        updater.dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, btc_bot_new_messages))

        buttons_handler = CallbackQueryHandler(callback=btc_bot_edit_messages, pass_chat_data=False)
        updater.dispatcher.add_handler(buttons_handler)

        updater.start_polling()
        updater.idle()
