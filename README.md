# Telegram-бот магазин на основе API от [Elastic Path](https://www.elasticpath.com)

### 1. Общее описание 
Телеграм бот, работающий по API CMS от Elastic Path. 
Это [MVP](https://ru.wikipedia.org/wiki/Минимально_жизнеспособный_продукт) версия продукта для демонстрации заказщику.
Бот реализован до шага получения заказа и контактов покупателя.

### 2. Подготовительные работы

Для успешного запуска системы необходимо подготовить следующее:   
2.1 Все работает на Python 3.8 или выше  
2.2 Скопировать текущий репозиторий
```shell
git clone https://github.com/Sam1808/Fish_shop_bot.git
```
2.3 Python окружение с установленными зависимостями согласно `requirements.txt`
```shell
pip install -r requirements.txt
```
2.4 Файл `.env` со следующим содержимым
```text
# Данные от Elastic Path
CLIENT_ID=ваш клиент id
CLIENT_SECRET=ваш Elastic ключ
# URL API интерфейса от Elastic Path (необязательный параметр)
API_BASE_URL=https://api.moltin.com

# Токен телеграм бота полученный через Отца ботов
TELEGRAM-TOKEN=ваш токен

# Доступ к базе данных Redis
REDIS-BASE=полное имя базы данных
REDIS-PORT=порт базы данных
REDIS-PASSWORD=пароль к базе данных
```
2.5 Добавьте в папку `images` фото ваших товаров.

### 3. Подготавливаем данные в [Elastic Path](https://www.elasticpath.com) для работы магазина

Для работы магазина нам нужны данные. Пришлось разработать отдельный файл методов для работы с API от Elastic Path. 
<hr>

Все методы собраны в файле `shop_utils.py`. Список реализованных методов (примеры и описание) отражен в 
[отдельном файле](./docs/description.md).

Таким образом, для работы магазина убедитесь, что у вас пройдены следующие шаги: 
1. Получена учетная запись [Elastic Path](https://www.elasticpath.com), создан `store`, если необходимо.
2. Созданы товары и заполнены все обязательные поля (ручной труд).
3. С помощью описанных методов загружены картинки для товаров и они связаны с товарами.
4. Вы почти на финише :)

### 3. Описание и запуск Telegram бота.  
 Телеграм бот позволяет:  
  
- Получить список товаров
- Сформировать покупку в корзине, согласно опций товара
- Отредактировать содержимое корзины
- Направить контакты покупателя.

Для запуска бота достаточно запустить команду:
```shell
python3 bot_tg.py
```
Для остановки работы бота используйте сочетание `Ctrl+C`.  
 Аргументов нет, логгинг минимальный посредством функционала Telegram.

### 4. Примеры

Если все шаги выполнены верно, вы получите примерно следующий результат:   
![fish_shop.gif](fish_shop.gif)  

И ещё один пример:  
**Временно** прототип бота развернут на [HEROKU](https://dashboard.heroku.com), можете попробовать его в действии [@My_DVMN_lessons_bot](https://t.me/My_DVMN_lessons_bot)

### 5. Известные проблемы
*Рекомендация:* Будьте внимательны с уровнем прав доступа в [Elastic Path](https://www.elasticpath.com), изучите 
[документацию](https://documentation.elasticpath.com/commerce-cloud/docs/api/index.html).
Часть методов может не работать или работать не корректно при недостаточном уровне доступа.