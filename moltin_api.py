import json
import os
import requests
import time

from dotenv import load_dotenv
from funcy import retry

API_BASE_URL = None
CLIENT_ID = None
CLIENT_SECRET = None
MOLTIN_TOKEN = None
MOLTIN_TOKEN_EXPIRES_TIME = 0


@retry(tries=3, timeout=1)
def add_product_to_cart(cart_id, product_id, quantity):
    """
    Добавляет товар в корзину
    :param cart_id: ID корзины
    :param product_id: ID товара
    :param quantity: Количество товара
    :return: Результат (в т.ч. ошибку) как JSON объект
    """
    headers = {
        'Authorization': f'Bearer {get_token()}',
        'Content-Type': 'application/json',
    }
    data = {
        "data":
            {
                "id": product_id,
                "type": "cart_item",
                "quantity": quantity
            }
    }
    response = requests.post(
        f'{API_BASE_URL}/v2/carts/{cart_id}/items',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def create_a_file(folder_name='images'):
    """
    Загружает файлы в систему CMS.
    Проверяет папку (по умолчанию 'images') и загружает все найденные картинки.
    Загруженные картинки переименовывает в имя_файла.расширение.uploaded
    Возвращает количество загруженных картинок и их список
    """
    headers = {'Authorization': f'Bearer {get_token()}'}

    filenames = os.listdir(folder_name)
    uploaded_files = []
    for filename in filenames:
        if 'uploaded' in filename:
            continue

        filename_path = os.path.join(folder_name, filename)
        files = {
            'file': (filename, open(filename_path, 'rb')),
            'public': (None, 'true'),
        }
        response = requests.post(
            f'{API_BASE_URL}/v2/files',
            headers=headers,
            files=files
        )
        response.raise_for_status()

        uploaded_files.append(filename)
        uploaded_filename_path = os.path.join(
            folder_name,
            f'{filename}.uploaded'
        )
        os.rename(filename_path, uploaded_filename_path)

    return f'Uploaded {len(uploaded_files)} files. Details: {uploaded_files}'


@retry(tries=3, timeout=1)
def create_a_customer(name, email):
    """
    Создает покупателя.
    Поле пароля не предусмотрено
    :param name: Имя покупателя
    :param email: Email покупателя
    :return: Результат (в т.ч. ошибку) как JSON объект
    """

    headers = {
        'Authorization': f'Bearer {get_token()}',
        'Content-Type': 'application/json',
    }
    data = {
        "data":
            {
                "type": "customer",
                "name": name,
                "email": email
            }
    }
    response = requests.post(
        f'{API_BASE_URL}/v2/customers',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def create_main_image_relationship(product_id, image_id):
    """
    Привязывает главную картинку для продукта на основании ID продукта
     и ID картинки.
    """
    headers = {
        'Authorization': f'Bearer {get_token()}',
        'Content-Type': 'application/json',
    }

    data = {"data": {"type": "main_image", "id": image_id}}

    response = requests.post(
        f'{API_BASE_URL}/v2/products/{product_id}/relationships/main-image',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def get_token():
    """
    Создает или возвращает актуальный токен,
     т.к. токены имеют свойство _протухать_
    """
    global MOLTIN_TOKEN_EXPIRES_TIME
    global MOLTIN_TOKEN

    current_time = int(time.time())
    if current_time <= MOLTIN_TOKEN_EXPIRES_TIME:
        return MOLTIN_TOKEN

    data = {
        'client_id': CLIENT_ID,
        'grant_type': 'client_credentials',
        'client_secret': CLIENT_SECRET,
    }
    response = requests.post(
        f'{API_BASE_URL}/oauth/access_token',
        data=data
    )
    response.raise_for_status()
    json_answer = response.json()

    MOLTIN_TOKEN_EXPIRES_TIME = json_answer['expires']
    MOLTIN_TOKEN = json_answer['access_token']
    return MOLTIN_TOKEN


@retry(tries=3, timeout=1)
def get_a_customers(customer_id=None):
    """
    Возвращает список всех покупателей или конкретного покупателя по его ID
    """

    headers = {'Authorization': f'Bearer {get_token()}'}

    url = f'{API_BASE_URL}/v2/customers/'
    if customer_id:
        url += customer_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_files(file_id=None):
    """
    Возвращает описание всех загруженных файлов или конкретного файла по его ID
    """
    headers = {'Authorization': f'Bearer {get_token()}'}

    url = f'{API_BASE_URL}/v2/files/'
    if file_id:
        url += file_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_cart_status(card_id, items=False):
    """
    Возвращает статус корзины или ее список товаров в ней
    """
    headers = {'Authorization': f'Bearer {get_token()}'}

    url = f'{API_BASE_URL}/v2/carts/{card_id}'
    if items:
        url += '/items'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_products(product_id=None):
    """
    Возвращает описание всех продуктов
    или описание конкретного продукта по его ID
    """

    headers = {'Authorization': f'Bearer {get_token()}'}

    url = f'{API_BASE_URL}/v2/products/'
    if product_id:
        url += product_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def remove_item_from_cart(card_id, product_id):
    """
    Удаляет товар из конкретной корзины (cart_id) по ID-товара
    """
    headers = {'Authorization': f'Bearer {get_token()}'}

    url = f'{API_BASE_URL}/v2/carts/{card_id}/items/{product_id}'

    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    return response.json()


def load_environment():
    load_dotenv()
    global API_BASE_URL
    global CLIENT_ID
    global CLIENT_SECRET

    API_BASE_URL = os.environ.get('API_BASE_URL', 'https://api.moltin.com')
    CLIENT_ID = os.environ["CLIENT_ID"]
    CLIENT_SECRET = os.environ["CLIENT_SECRET"]


if __name__ == '__main__':
    load_environment()
