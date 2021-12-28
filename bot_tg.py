import os
import redis
import logging

from functools import partial

from moltin_api import add_product_to_cart
from moltin_api import create_a_customer
from moltin_api import get_cart_status
from moltin_api import get_files
from moltin_api import get_products
from moltin_api import load_environment
from moltin_api import remove_item_from_cart

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Filters, Updater
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler
from textwrap import dedent


def _error(_, context):
    """Собираем ошибки"""
    logging.info('Bot catch some exception. Need your attention.')
    logging.exception(context.error)


def start(update, _):
    """
    Функция start - запуск бота (функция partial_handle_users_reply)
    и переход в состояние HANDLE_MENU.
    """

    keyboard = list()
    for product in get_products()['data']:
        product_id = str(product['id'])
        keyboard.append(
            [
                InlineKeyboardButton(product['name'], callback_data=product_id)
            ]
        )
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='/cart')])
    reply_markup = InlineKeyboardMarkup(keyboard)
    message = 'Список предложений:'
    if update.message:
        update.message.reply_text(text=message, reply_markup=reply_markup)
        update.message.delete()
    else:
        update.callback_query.message.reply_text(
            text=message,
            reply_markup=reply_markup
        )
        update.callback_query.message.delete()

    return "HANDLE_MENU"


def handle_menu(update, _):
    """Предложение и выбор товара"""

    query = update.callback_query

    if query.data == '/cart':
        return handle_cart(update, _)

    product_description = get_products(product_id=query.data)['data']
    unit_price = \
        product_description['meta']['display_price']['with_tax']['formatted']
    message = f'''\
    {product_description['name']}
    Описание: {product_description['description']}
    Цена: {unit_price} за килограмм'''

    file_id = product_description['relationships']['main_image']['data']['id']
    file_description = get_files(file_id=file_id)
    file_url = file_description['data']['link']['href']

    keyboard = [
        [
            InlineKeyboardButton('1кг', callback_data=f'{query.data}>1'),
            InlineKeyboardButton('5кг', callback_data=f'{query.data}>5'),
            InlineKeyboardButton('10кг', callback_data=f'{query.data}>10'),
        ],
        [InlineKeyboardButton('Назад', callback_data='/back')],
        [InlineKeyboardButton('Корзина', callback_data='/cart')],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_photo(
        photo=file_url,
        caption=dedent(message),
        reply_markup=reply_markup
    )
    query.message.delete()

    query.answer()
    return "HANDLE_DESCRIPTION"


def handle_description(update, _):
    """Добавление определенного кол-ва товара в корзину"""

    query = update.callback_query

    if '/back' == query.data:
        return start(update, _)
    elif '/cart' == query.data:
        return handle_cart(update, _)

    purchase = str(query.data).split('>')
    purchase_id = purchase[0]
    purchase_quantity = int(purchase[1])

    chat_id = update.effective_message.chat_id
    add_product_to_cart(chat_id, purchase_id, purchase_quantity)

    keyboard = [
        [InlineKeyboardButton('Назад', callback_data='/back')],
        [InlineKeyboardButton('Корзина', callback_data='/cart')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    product_description = get_products(product_id=purchase_id)['data']

    message = f'''\
    В корзину добавлен товар:
    {product_description['name']}.
    Количество: {purchase_quantity} килограмм'''

    query.message.reply_text(text=dedent(message), reply_markup=reply_markup)
    query.message.delete()

    query.answer()
    return "HANDLE_DESCRIPTION"


def handle_cart(update, _):
    """Работа с корзиной"""

    chat_id = update.effective_message.chat_id
    query = update.callback_query

    if '/pay' == query.data:
        return handle_email(update, _)
    elif '/back' == query.data:
        return start(update, _)
    elif 'delete>' in query.data:
        product_id = str(query.data).split('>')[1]
        remove_item_from_cart(chat_id, product_id)

    cart_status = get_cart_status(chat_id)
    cart_status_items = get_cart_status(chat_id, items=True)

    product_message = ''
    keyboard = list()

    for product in cart_status_items['data']:
        unit_price = \
            product['meta']['display_price']['with_tax']['unit']['formatted']
        total_price = \
            product['meta']['display_price']['with_tax']['value']['formatted']
        product_message += dedent(f'''        
        {product['name']}
        {product['description']}
        Цена за килограмм(кг): {unit_price}
        Количество: {product['quantity']} кг
        Всего цена: {total_price}
        ''')

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Удалить: {product['name']}",
                    callback_data=f"delete>{product['id']}"
                )
            ]
        )
    total_cost = \
        cart_status['data']['meta']['display_price']['with_tax']['formatted']
    product_message += f'\nИтого цена: {total_cost}'

    keyboard.append(
        [
            InlineKeyboardButton('В меню', callback_data='/back'),
            InlineKeyboardButton('Оплатить', callback_data='/pay')
        ],
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    query.message.reply_text(text=product_message, reply_markup=reply_markup)
    query.message.delete()

    query.answer()
    return 'HANDLE_CART'


def handle_email(update, _):
    """Функция, которая создает пользователя на основе полученного email"""

    if update.message:
        keyboard = [
            [
                InlineKeyboardButton(
                    'Верно',
                    callback_data=f'/create_customer>{update.message.text}'
                ),
                InlineKeyboardButton('Я ошибся', callback_data='/wrong_email')
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)

        message = f'Вы прислали e-mail: {update.message.text}'
        update.message.delete()
        update.message.reply_text(text=message, reply_markup=reply_markup)
    else:
        message = 'Пожалуйста сообщите свой e-mail для формирования заказа'
        query = update.callback_query

        if '/create_customer' in query.data:
            username = query.message.from_user['username']
            email = str(query.data).split('>')[1]
            customer = create_a_customer(username, email)['data']
            message = f'''\
            Покупатель: {customer['name']}
            E-mail: {customer['email']}
            ID: {customer['id']}
            '''
            query.message.delete()

        elif '/wrong_email' in query.data:
            query.message.delete()

        query.message.reply_text(text=dedent(message))
        query.answer()

    return 'WAITING_EMAIL'


def handle_users_reply(update, _, db_connection):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает
     как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую
     функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается
     в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его
     написать "/start", поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может
     воспользоваться этой командой.
    """

    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return

    if user_reply == '/start':
        user_state = 'START'
    else:
        user_state = db_connection.get(chat_id).decode("utf-8")

    states_functions = {
        'START': start,
        'HANDLE_MENU': handle_menu,
        'HANDLE_DESCRIPTION': handle_description,
        'HANDLE_CART': handle_cart,
        'WAITING_EMAIL': handle_email,
    }
    state_handler = states_functions[user_state]

    next_state = state_handler(update, _)

    db_connection.set(chat_id, next_state)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    load_environment()

    updater = Updater(os.environ["TELEGRAM-TOKEN"])

    database_host = os.environ["REDIS-BASE"]
    database_port = os.environ["REDIS-PORT"]
    database_password = os.environ["REDIS-PASSWORD"]
    db_connection = redis.Redis(
        host=database_host,
        port=int(database_port),
        password=database_password
    )

    partial_handle_users_reply = partial(
        handle_users_reply,
        db_connection=db_connection
    )

    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(partial_handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, partial_handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', partial_handle_users_reply))
    dispatcher.add_error_handler(_error)
    updater.start_polling()
    updater.idle()
