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

from trading.models import ProposalBtc

import requests
from bs4 import BeautifulSoup


def btc_bot_new_messages(update: Update, context: CallbackContext):
    message = update.message.text

    user_telegram_id = update.message.chat_id
    bot = telepot.Bot(settings.TOKEN)

    if ProposalBtc.objects.filter(user_telegram_id=user_telegram_id).count() == 1:
        proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)

        if not proposal_btc.is_count:
            try:
                proposal_btc.count = float(message.replace(',', '.'))
                proposal_btc.proposal_btc = True

                bot_message = 'Все отлично, напиши в какой из наших точек ты хотел бы совершить обмен?'
            except ValueError:
                bot_message = 'Я тебя не понял, попробуй написать сумму еще раз'

            bot.sendMessage(user_telegram_id, bot_message)
        else:
            bot.sendMessage('123')
    else:
        if message == '/start' or message == 'начать':
            bot_message = 'Привет я бот по обмену крипты :)\nВыбери что тебя интересует'

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Купить', callback_data='buy'),
                                  InlineKeyboardButton(text='Продать', callback_data='sell')]])

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message, reply_markup=keyboard)
        else:
            bot_message = 'Я тебя не понял, воспользуйся кнопкой ниже чтобы начать обмен'

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
            bot_message = 'Привет я бот по обмену крипты :)\nВыбери что тебя интересует'

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Купить', callback_data='buy'),
                                  InlineKeyboardButton(text='Продать', callback_data='sell')]])

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message, reply_markup=keyboard)
    elif 'buy' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB\n\n".format(got_now_btc_run())
            bot_text += "На какую сумму хотите купить BTC?"

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id,
            )

            bot.sendMessage(chat_id=user_telegram_id, text=bot_text)
    elif 'sell' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB".format(got_now_btc_run())
            bot_text += "На какую сумму хотите продать BTC?"

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id,
                buy=True,
            )

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
