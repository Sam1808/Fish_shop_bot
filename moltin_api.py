import json
import os
import requests
import time

from dotenv import load_dotenv
from funcy import retry

MOLTIN_TOKEN = None
MOLTIN_TOKEN_EXPIRES_TIME = 0


@retry(tries=3, timeout=1)
def add_product_to_cart(
        api_base_url,
        client_id,
        client_secret,
        cart_id,
        product_id,
        quantity
):
    """
    Добавляет товар в корзину
    :param cart_id: ID корзины
    :param product_id: ID товара
    :param quantity: Количество товара
    :return: Результат (в т.ч. ошибку) как JSON объект
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )
    headers = {
        'Authorization': f'Bearer {token}',
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
        f'{api_base_url}/v2/carts/{cart_id}/items',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def create_a_file(
        api_base_url,
        client_id,
        client_secret,
        folder_name='images'
):
    """
    Загружает файлы в систему CMS.
    Проверяет папку (по умолчанию 'images') и загружает все найденные картинки.
    Загруженные картинки переименовывает в имя_файла.расширение.uploaded
    Возвращает количество загруженных картинок и их список
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )
    headers = {'Authorization': f'Bearer {token}'}

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
            f'{api_base_url}/v2/files',
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
def create_a_customer(
        api_base_url,
        client_id,
        client_secret,
        name,
        email
):
    """
    Создает покупателя.
    Поле пароля не предусмотрено
    :param name: Имя покупателя
    :param email: Email покупателя
    :return: Результат (в т.ч. ошибку) как JSON объект
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )

    headers = {
        'Authorization': f'Bearer {token}',
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
        f'{api_base_url}/v2/customers',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def create_main_image_relationship(
        api_base_url,
        client_id,
        client_secret,
        product_id,
        image_id
):
    """
    Привязывает главную картинку для продукта на основании ID продукта
     и ID картинки.
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {"data": {"type": "main_image", "id": image_id}}

    response = requests.post(
        f'{api_base_url}/v2/products/{product_id}/relationships/main-image',
        headers=headers,
        data=json.dumps(data)
    )
    response.raise_for_status()
    return response.json()


@retry(tries=3, timeout=1)
def get_token(
        api_base_url,
        client_id,
        client_secret
):
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
        'client_id': client_id,
        'grant_type': 'client_credentials',
        'client_secret': client_secret,
    }
    response = requests.post(
        f'{api_base_url}/oauth/access_token',
        data=data
    )
    response.raise_for_status()
    token_info = response.json()

    MOLTIN_TOKEN_EXPIRES_TIME = token_info['expires']
    MOLTIN_TOKEN = token_info['access_token']
    return MOLTIN_TOKEN


@retry(tries=3, timeout=1)
def get_a_customers(
        api_base_url,
        client_id,
        client_secret,
        customer_id=None
):
    """
    Возвращает список всех покупателей или конкретного покупателя по его ID
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )

    headers = {'Authorization': f'Bearer {token}'}

    url = f'{api_base_url}/v2/customers/'
    if customer_id:
        url += customer_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_files(
        api_base_url,
        client_id,
        client_secret,
        file_id=None
):
    """
    Возвращает описание всех загруженных файлов или конкретного файла по его ID
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )
    headers = {'Authorization': f'Bearer {token}'}

    url = f'{api_base_url}/v2/files/'
    if file_id:
        url += file_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_cart_status(
        api_base_url,
        client_id,
        client_secret,
        card_id,
        items=False
):
    """
    Возвращает статус корзины или ее список товаров в ней
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret,
    )
    headers = {'Authorization': f'Bearer {token}'}

    url = f'{api_base_url}/v2/carts/{card_id}'
    if items:
        url += '/items'

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def get_products(
        api_base_url,
        client_id,
        client_secret,
        product_id=None
):
    """
    Возвращает описание всех продуктов
    или описание конкретного продукта по его ID
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )
    headers = {'Authorization': f'Bearer {token}'}

    url = f'{api_base_url}/v2/products/'
    if product_id:
        url += product_id

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    return response.json()


@retry(tries=3, timeout=1)
def remove_item_from_cart(
        api_base_url,
        client_id,
        client_secret,
        card_id,
        product_id
):
    """
    Удаляет товар из конкретной корзины (cart_id) по ID-товара
    """
    token = get_token(
        api_base_url,
        client_id,
        client_secret
    )

    headers = {'Authorization': f'Bearer {token}'}

    url = f'{api_base_url}/v2/carts/{card_id}/items/{product_id}'

    response = requests.delete(url, headers=headers)
    response.raise_for_status()

    return response.json()


def load_environment():
    load_dotenv()
    api_base_url = os.environ.get('API_BASE_URL', 'https://api.moltin.com')
    client_id = os.environ["CLIENT_ID"]
    client_secret = os.environ["CLIENT_SECRET"]

    return api_base_url, client_id, client_secret
