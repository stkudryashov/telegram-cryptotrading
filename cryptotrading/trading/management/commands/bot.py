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

        if not proposal_btc.is_count:
            try:
                value = float(message.replace(',', '.'))

                if proposal_btc.buy:
                    exchange_points = ExchangePoint.objects.filter(sells__gte=value)
                else:
                    exchange_points = ExchangePoint.objects.filter(stocks__gte=value)

                if exchange_points:
                    keyboard = []
                    for exchange_point in exchange_points:
                        keyboard.append([InlineKeyboardButton(text=exchange_point.name,
                                                              callback_data='ep {}'.format(exchange_point.name))])

                    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

                    proposal_btc.count = value
                    proposal_btc.save()

                    bot_message = 'Теперь выбери точку обмена'
                    bot.sendMessage(user_telegram_id, bot_message, reply_markup=keyboard)
                else:
                    bot_message = 'У точек нет столько денег :с\nПопробуй ввести сумму меньше'
                    bot.sendMessage(user_telegram_id, bot_message)
            except ValueError:
                bot_message = 'Я тебя не понял, попробуй написать сумму еще раз'
                bot.sendMessage(user_telegram_id, bot_message)
        elif not proposal_btc.is_date:
            keyboard = []
            for number in range(20):
                if number % 5 == 0:
                    keyboard.append([])
                keyboard[number // 5].append(InlineKeyboardButton(
                    text=(datetime.today() + timedelta(days=number)).strftime("%d.%m"),
                    callback_data='date {}'.format(number)))

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

            bot_message = 'Отлично! Теперь выбери дату визита'
            bot.sendMessage(user_telegram_id, bot_message, reply_markup=keyboard)
        elif not proposal_btc.is_time:
            keyboard = []
            for number in range(12):
                if number % 4 == 0:
                    keyboard.append([])
                keyboard[number // 4].append(InlineKeyboardButton(
                    text='{}:00'.format(number + 9),
                    callback_data='time {}'.format(number)))

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

            bot_message = 'Осталось выбрать время визита'
            bot.sendMessage(user_telegram_id, bot_message, reply_markup=keyboard)
        elif not proposal_btc.is_number:
            if len(message) < 11:
                bot_message = 'Я не понимаю твоего номера'
            else:
                proposal_btc.user_number = message
                proposal_btc.is_number = True
                proposal_btc.save()

                bot_message = 'Ура! Твоя заявка готова'

            bot.sendMessage(user_telegram_id, bot_message)
        else:
            bot.sendMessage(user_telegram_id, 'Заявка уже создана')
    else:
        if message == '/start' or message == 'начать':
            bot_message = 'Привет, я бот по обмену крипты :)\nЧто ты хочешь сделать?'

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text='Купить', callback_data='buy'),
                                  InlineKeyboardButton(text='Продать', callback_data='sell')]])

            bot.sendMessage(chat_id=user_telegram_id, text=bot_message, reply_markup=keyboard)
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
            bot_message = 'Привет, я бот по обмену крипты :)\nДля что ты хочешь сделать?'

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
            percent = got_now_btc_run() * 0.015

            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB\n\n".format(round(got_now_btc_run() - percent, 2))
            bot_text += "На какую сумму ₽ хотите купить BTC?"

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id,
                buy=True
            )

            bot.sendMessage(chat_id=user_telegram_id, text=bot_text)
    elif 'sell' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            percent = got_now_btc_run() * 0.02

            bot_text = "Текущий курс: \n\n 1 BTC -> {0} RUB\n\n".format(round(got_now_btc_run() + percent, 2))
            bot_text += "На какую сумму ₽ хотите продать BTC?"

            ProposalBtc.objects.create(
                user_telegram_id=user_telegram_id
            )

            bot.sendMessage(chat_id=user_telegram_id, text=bot_text)
    elif 'ep' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)
            proposal_btc.point_name = button_press.split(' ')[1]
            proposal_btc.is_count = True
            proposal_btc.is_point = True
            proposal_btc.save()

            keyboard = []
            for number in range(20):
                if number % 5 == 0:
                    keyboard.append([])
                keyboard[number // 5].append(InlineKeyboardButton(
                    text=(datetime.today() + timedelta(days=number)).strftime("%d.%m"),
                    callback_data='date {}'.format(number)))

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

            bot_message = 'Отлично! Теперь выбери дату визита'
            bot.sendMessage(user_telegram_id, bot_message, reply_markup=keyboard)
    elif 'date' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)
            proposal_btc.date_visit = (datetime.today() + timedelta(days=int(button_press.split(' ')[1]))).strftime("%d.%m.%y")
            proposal_btc.is_date = True
            proposal_btc.save()

            keyboard = []
            for number in range(12):
                if number % 4 == 0:
                    keyboard.append([])
                keyboard[number // 4].append(InlineKeyboardButton(
                    text='{}:00'.format(number + 9),
                    callback_data='time {}'.format(number + 9)))

            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard)

            bot_message = 'Осталось выбрать время визита'
            bot.sendMessage(user_telegram_id, bot_message, reply_markup=keyboard)
    elif 'time' in button_press:
        try:
            bot.deleteMessage(edit_message)
        except telepot.exception.TelegramError:
            pass
        finally:
            proposal_btc = ProposalBtc.objects.get(user_telegram_id=user_telegram_id)
            proposal_btc.time_visit = '{}:00'.format(button_press.split(' ')[1])
            proposal_btc.is_time = True
            proposal_btc.save()

            bot_message = 'Последний шаг. Введите номер телефона'
            bot.sendMessage(user_telegram_id, bot_message)


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
