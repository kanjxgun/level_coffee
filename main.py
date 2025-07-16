import telebot
from telebot import types
from dotenv import load_dotenv
import os

load_dotenv()

TOKEN = str(os.getenv('TOKEN'))
ADMIN_CHAT_ID = str(os.getenv('ADMIN_CHAT_ID'))  # ID приватного канала для заказов

bot = telebot.TeleBot(TOKEN)

cart = {}

# Для хранения пожеланий пользователя перед подтверждением заказа
user_wishes = {}
user_names = {}

# Избранное теперь хранит список словарей с параметрами товара
favorites = {}  # user_id: [ {product, volume, syrup, altmilk, price}, ... ]

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Меню', 'Корзина')
    markup.row('Избранное', 'Новый заказ')
    bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Меню')
def show_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Кофе', 'Вода', 'Десерты', 'Еда', 'Шоколадки')
    markup.row('Назад')
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

products = {
    'Кофе': ['Эспрессо', 'Капучино', 'Латте','Флэт Уайт','Американо','Раф','Лимонад','Эспрессо тоник','Айс-кофе','Какао','Чай','Матча'],
    'Вода': ['Кола', 'Спрайт','Фанта','Мохито швепс','Квас','Ред Булл - 0,3','Ред булл 0,5','Адреналин','Боржоми','Святой источник'],
    'Десерты': ['Молочный ломтик','Зефир','Суфле'],
    'Еда': ['Чиабатта ветчина и сыр','Чиабатта пепперони и салями','Чиабатта с курицей','Круассан с беконом и халапенью','Блинчики с курицей и сыром','Сырники','Салат цезарь','Орешки со сгущенкой','Печенье 2 шоколада','Трубочка со сгущенкой'],
    'Шоколадки': ['Mars','Snickers','Twix','Picnic']
}

prices = {
    'Эспрессо': 120,
    'Капучино': {'200 мл': 130, '300 мл': 170, '400 мл': 200},
    'Латте': {'300 мл': 170, '400 мл': 200},
    'Флэт Уайт': 150,
    'Американо': {'200 мл': 130, '300 мл': 160, '400 мл': 200},
    'Раф': {'300 мл': 250, '400 мл': 300},
    'Лимонад': {'400 мл': 250},
    'Эспрессо тоник': 350,
    'Айс-кофе': 250,
    'Какао': {'300 мл': 200, '400 мл': 240},
    'Чай': {'300 мл': 120, '400 мл': 150},
    'Матча': {'300 мл': 200, '400 мл': 250},
    'Кола': 130,
    'Спрайт': 130,
    'Фанта': 130,
    'Мохито швепс': 130,
    'Квас': 100,
    'Ред Булл - 0,3': 170,
    'Ред булл 0,5': 270,
    'Адреналин': 220,
    'Боржоми': 200,
    'Святой источник': 50,
    'Молочный ломтик': 200,
    'Зефир': 200,
    'Суфле': 200,
    'Чиабатта ветчина и сыр': 300,
    'Чиабатта пепперони и салями': 300,
    'Чиабатта с курицей': 300,
    'Круассан с беконом и халапенью': 300,
    'Блинчики с курицей и сыром': 250,
    'Сырники': 250,
    'Салат цезарь': 300,
    'Орешки со сгущенкой': 170,
    'Печенье 2 шоколада': 130,
    'Трубочка со сгущенкой': 130,
    'Mars': 120,
    'Snickers': 120,
    'Twix': 120,
    'Picnic': 120,
}

# Собираем все товары в один список
all_products = []
for items in products.values():
    all_products.extend(items)

# Кофейные напитки, к которым можно добавить сироп и альтернативное молоко
coffee_drinks = ['Эспрессо', 'Капучино', 'Латте', 'Флэт Уайт', 'Американо', 'Раф', 'Айс-кофе', 'Матча']

# Для хранения временного выбора объема и опций
user_volume_choice = {}
user_customization = {}

@bot.message_handler(func=lambda m: m.text in products.keys())
def show_products(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for item in products[message.text]:
        markup.row(item)
    markup.row('Назад')
    bot.send_message(message.chat.id, f"Выберите товар из категории {message.text}:", reply_markup=markup)

# --- Новый обработчик: добавить в избранное товар без параметров ---
@bot.message_handler(func=lambda m: m.text.startswith('★ '))
def add_simple_favorite(message):
    user_id = message.from_user.id
    product = message.text[2:]
    # Проверяем, есть ли параметры у товара
    if isinstance(prices.get(product), dict) or product in coffee_drinks:
        bot.send_message(message.chat.id, "Для добавления этого товара в избранное выберите параметры!")
        return
    fav = {'product': product, 'volume': None, 'syrup': False, 'altmilk': False, 'price': prices.get(product, 0)}
    if fav in favorites.get(user_id, []):
        bot.send_message(message.chat.id, f"{product} уже в избранном!")
    else:
        favorites.setdefault(user_id, []).append(fav)
        bot.send_message(message.chat.id, f"{product} добавлен в избранное!")

# --- Изменяем обработчик выбора товара ---
@bot.message_handler(func=lambda m: m.text in all_products)
def choose_product(message):
    user_id = message.from_user.id
    product = message.text
    # Если у товара есть варианты объема
    if isinstance(prices.get(product), dict):
        user_volume_choice[user_id] = product
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for volume in prices[product].keys():
            markup.row(volume)
        markup.row('Назад')
        bot.send_message(message.chat.id, f"Выберите объем для {product}:", reply_markup=markup)
    else:
        # Товар без объема
        if product in coffee_drinks:
            # Кофейный напиток без объема — спрашиваем про сироп
            user_customization[user_id] = {'product': product, 'price': prices[product], 'volume': None, 'syrup': False, 'altmilk': False}
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row('Да', 'Нет')
            bot.send_message(message.chat.id, "Добавить сироп за 50₽?", reply_markup=markup)
        else:
            # Не кофейный напиток — сразу добавляем
            price = prices.get(product, 0)
            cart.setdefault(user_id, []).append(f"{product} — {price}₽")
            # Кнопка для добавления в избранное
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(f'★ {product}', 'В меню категорий')
            bot.send_message(message.chat.id, f"{product} добавлен в корзину по цене {price}₽!", reply_markup=markup)

# --- Изменяем обработчик выбора объема ---
@bot.message_handler(func=lambda m: any(isinstance(prices.get(prod), dict) and m.text in prices[prod] for prod in prices if prod in user_volume_choice.values()))
def add_product_with_volume(message):
    user_id = message.from_user.id
    product = user_volume_choice.get(user_id)
    if product and isinstance(prices.get(product), dict):
        volume = message.text
        price = prices[product][volume]
        if product in coffee_drinks:
            # Кофейный напиток с объемом — спрашиваем про сироп
            user_customization[user_id] = {'product': product, 'price': price, 'volume': volume, 'syrup': False, 'altmilk': False}
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row('Да', 'Нет')
            bot.send_message(message.chat.id, "Добавить сироп за 50₽?", reply_markup=markup)
        else:
            cart.setdefault(user_id, []).append(f"{product} ({volume}) — {price}₽")
            # Кнопка для добавления в избранное
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row(f'★ {product} ({volume})', 'В меню категорий')
            bot.send_message(message.chat.id, f"{product} ({volume}) добавлен в корзину по цене {price}₽!", reply_markup=markup)
        user_volume_choice.pop(user_id, None)
    else:
        bot.send_message(message.chat.id, "Ошибка выбора объема. Попробуйте снова.")

# --- Новый обработчик: добавить в избранное товар с объемом ---
@bot.message_handler(func=lambda m: m.text.startswith('★ ') and '(' in m.text)
def add_volume_favorite(message):
    user_id = message.from_user.id
    # Пример: ★ Капучино (300 мл)
    text = message.text[2:]
    if ' (' in text:
        product = text.split(' (')[0]
        volume = text.split('(')[1].split(')')[0]
    else:
        product = text
        volume = None
    price = 0
    if product in prices and isinstance(prices[product], dict) and volume in prices[product]:
        price = prices[product][volume]
    fav = {'product': product, 'volume': volume, 'syrup': False, 'altmilk': False, 'price': price}
    if fav in favorites.get(user_id, []):
        bot.send_message(message.chat.id, f"{product} ({volume}) уже в избранном!")
    else:
        favorites.setdefault(user_id, []).append(fav)
        bot.send_message(message.chat.id, f"{product} ({volume}) добавлен в избранное!")

# --- Изменяем обработку сиропа и молока ---
@bot.message_handler(func=lambda m: m.text in ['Да', 'Нет'] and m.from_user.id in user_customization)
def handle_syrup(message):
    user_id = message.from_user.id
    if user_id not in user_customization:
        return
    if message.text == 'Да':
        user_customization[user_id]['syrup'] = True
    # После сиропа спрашиваем про альтернативное молоко
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Да', 'Нет')
    bot.send_message(message.chat.id, "Приготовить на альтернативном молоке за 60₽?", reply_markup=markup)
    # Следующий шаг — обработка молока
    bot.register_next_step_handler(message, handle_altmilk)

def handle_altmilk(message):
    user_id = message.from_user.id
    if user_id not in user_customization:
        return
    if message.text == 'Да':
        user_customization[user_id]['altmilk'] = True
    # Формируем строку для корзины
    c = user_customization[user_id]
    name = c['product']
    price = c['price']
    details = []
    if c['volume']:
        name = f"{name} ({c['volume']})"
    if c['syrup']:
        details.append('сироп')
        price += 50
    if c['altmilk']:
        details.append('альт. молоко')
        price += 60
    if details:
        name = f"{name} + {' + '.join(details)}"
    cart.setdefault(user_id, []).append(f"{name} — {price}₽")
    # Кнопка для добавления в избранное с параметрами
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(f'★ {name}', 'В меню категорий')
    bot.send_message(message.chat.id, f"{name} добавлен в корзину по цене {price}₽!", reply_markup=markup)
    # Сохраняем параметры для избранного
    c['price'] = price
    c['name'] = name
    user_customization[user_id] = c
    user_customization.pop(user_id, None)

# --- Новый обработчик: добавить в избранное товар с параметрами (сироп/молоко) ---
@bot.message_handler(func=lambda m: m.text.startswith('★ ') and ('сироп' in m.text or 'альт. молоко' in m.text))
def add_full_favorite(message):
    user_id = message.from_user.id
    # Пример: ★ Капучино (300 мл) + сироп + альт. молоко
    text = message.text[2:]
    # Парсим название, объем, сироп, молоко
    parts = text.split(' + ')
    base = parts[0]
    options = parts[1:] if len(parts) > 1 else []
    if '(' in base:
        product = base.split(' (')[0]
        volume = base.split('(')[1].split(')')[0]
    else:
        product = base
        volume = None
    syrup = 'сироп' in options
    altmilk = 'альт. молоко' in options
    # Определяем цену
    price = 0
    if product in prices:
        if isinstance(prices[product], dict) and volume in prices[product]:
            price = prices[product][volume]
        elif isinstance(prices[product], int):
            price = prices[product]
    if syrup:
        price += 50
    if altmilk:
        price += 60
    fav = {'product': product, 'volume': volume, 'syrup': syrup, 'altmilk': altmilk, 'price': price}
    if fav in favorites.get(user_id, []):
        bot.send_message(message.chat.id, f"{text} уже в избранном!")
    else:
        favorites.setdefault(user_id, []).append(fav)
        bot.send_message(message.chat.id, f"{text} добавлен в избранное!")

# --- Изменяем отображение избранного ---
@bot.message_handler(func=lambda m: m.text == 'Избранное')
def show_favorites(message):
    user_id = message.from_user.id
    favs = favorites.get(user_id, [])
    if not favs:
        bot.send_message(message.chat.id, "У вас нет избранных товаров.")
        return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for fav in favs:
        name = fav['product']
        if fav['volume']:
            name += f" ({fav['volume']})"
        details = []
        if fav['syrup']:
            details.append('сироп')
        if fav['altmilk']:
            details.append('альт. молоко')
        if details:
            name += ' + ' + ' + '.join(details)
        markup.row(name)
    markup.row('Добавить все в корзину', 'Очистить избранное')
    markup.row('Назад')
    bot.send_message(message.chat.id, "Ваши избранные товары:", reply_markup=markup)

# --- Изменяем добавление всех избранных в корзину ---
@bot.message_handler(func=lambda m: m.text == 'Добавить все в корзину')
def add_all_favorites_to_cart(message):
    user_id = message.from_user.id
    favs = favorites.get(user_id, [])
    if not favs:
        bot.send_message(message.chat.id, "У вас нет избранных товаров.")
        return
    for fav in favs:
        name = fav['product']
        if fav['volume']:
            name += f" ({fav['volume']})"
        details = []
        price = fav['price']
        if fav['syrup']:
            details.append('сироп')
        if fav['altmilk']:
            details.append('альт. молоко')
        if details:
            name += ' + ' + ' + '.join(details)
        cart.setdefault(user_id, []).append(f"{name} — {price}₽")
    bot.send_message(message.chat.id, "Все избранные товары добавлены в корзину!")
    show_cart(message)

# --- Изменяем очистку избранного ---
@bot.message_handler(func=lambda m: m.text == 'Очистить избранное')
def clear_favorites(message):
    user_id = message.from_user.id
    favorites[user_id] = []
    bot.send_message(message.chat.id, "Избранное очищено.")
    show_favorites(message)

@bot.message_handler(func=lambda m: m.text == 'Корзина')
def show_cart(message):
    user_id = message.from_user.id
    items = cart.get(user_id, [])
    if not items:
        bot.send_message(message.chat.id, "Ваша корзина пуста.")
    else:
        # Считаем итоговую сумму
        total = 0
        for item in items:
            if '—' in item:
                try:
                    price = int(item.split('—')[-1].replace('₽', '').strip())
                    total += price
                except:
                    pass
        text = "Ваша корзина:\n" + "\n".join(items) + f"\n\nИтого: {total}₽"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row('Оформить заказ', 'Очистить корзину')
        markup.row('Назад')
        bot.send_message(message.chat.id, text, reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Очистить корзину')
def clear_cart(message):
    user_id = message.from_user.id
    cart[user_id] = []
    bot.send_message(message.chat.id, "Корзина очищена.")

@bot.message_handler(func=lambda m: m.text == 'Оформить заказ')
def checkout(message):
    user_id = message.from_user.id
    items = cart.get(user_id, [])
    if not items:
        bot.send_message(message.chat.id, "Ваша корзина пуста.")
        return
    # Запрашиваем имя
    bot.send_message(message.chat.id, "Пожалуйста, введите ваше имя для заказа:")
    bot.register_next_step_handler(message, handle_name)

def handle_name(message):
    user_id = message.from_user.id
    name = message.text.strip()
    user_names[user_id] = name
    # Запрашиваем пожелания
    bot.send_message(message.chat.id, "Есть ли у вас особые пожелания? (например, сколько сахара, какой сироп и т.д.) Напишите их в сообщении или отправьте «-», если пожеланий нет.")
    bot.register_next_step_handler(message, handle_wishes)

def handle_wishes(message):
    user_id = message.from_user.id
    wishes = message.text.strip()
    user_wishes[user_id] = wishes if wishes != '-' else ''
    # Формируем итоговую корзину
    items = cart.get(user_id, [])
    total = 0
    for item in items:
        if '—' in item:
            try:
                price = int(item.split('—')[-1].replace('₽', '').strip())
                total += price
            except:
                pass
    text = "Ваш заказ:\n" + "\n".join(items) + f"\n\nИтого: {total}₽"
    if user_wishes[user_id]:
        text += f"\n\nПожелания: {user_wishes[user_id]}"
    text += "\n\nВсе ли верно? (Да/Нет)"
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, confirm_order)

def confirm_order(message):
    user_id = message.from_user.id
    answer = message.text.strip().lower()
    if answer == 'да':
        items = cart.get(user_id, [])
        total = 0
        for item in items:
            if '—' in item:
                try:
                    price = int(item.split('—')[-1].replace('₽', '').strip())
                    total += price
                except:
                    pass
        order_text = f"Новый заказ от @{message.from_user.username or message.from_user.id}:\nИмя: {user_names.get(user_id, '')}\n" + "\n".join(items) + f"\n\nИтого: {total}₽"
        wishes = user_wishes.get(user_id, '')
        if wishes:
            order_text += f"\n\nПожелания: {wishes}"
        bot.send_message(ADMIN_CHAT_ID, order_text)
        bot.send_message(message.chat.id, "Ваш заказ отправлен! Спасибо!")
        cart[user_id] = []
        user_wishes.pop(user_id, None)
        user_names.pop(user_id, None)
    elif answer == 'нет':
        bot.send_message(message.chat.id, "Заказ не отправлен. Вы можете изменить корзину или оформить заказ заново.")
    else:
        bot.send_message(message.chat.id, "Пожалуйста, ответьте 'Да' или 'Нет'. Все ли верно?")
        bot.register_next_step_handler(message, confirm_order)

@bot.message_handler(func=lambda m: m.text == 'Добавить в избранное')
def add_to_favorites(message):
    user_id = message.from_user.id
    # Найти последний добавленный товар в корзине
    items = cart.get(user_id, [])
    if not items:
        bot.send_message(message.chat.id, "Сначала добавьте товар в корзину.")
        return
    last_item = items[-1]
    # Извлечь название товара (до '—')
    product_name = last_item.split('—')[0].strip()
    if product_name in favorites.get(user_id, []):
        bot.send_message(message.chat.id, f"{product_name} уже в избранном!")
    else:
        favorites.setdefault(user_id, []).append(product_name)
        bot.send_message(message.chat.id, f"{product_name} добавлен в избранное!")
    # Возвращаемся к меню категорий
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Кофе', 'Вода', 'Десерты', 'Еда', 'Шоколадки')
    markup.row('Назад')
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'В меню категорий')
def back_to_categories(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Кофе', 'Вода', 'Десерты', 'Еда', 'Шоколадки')
    markup.row('Назад')
    bot.send_message(message.chat.id, "Выберите категорию:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == 'Назад')
def go_back(message):
    start(message)

@bot.message_handler(func=lambda m: m.text == 'Новый заказ')
def new_order(message):
    user_id = message.from_user.id
    cart[user_id] = []
    user_wishes.pop(user_id, None)
    user_names.pop(user_id, None)
    # Очищаем переписку (по возможности)
    # Возвращаем к стартовому меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Меню', 'Корзина')
    markup.row('Избранное', 'Новый заказ')
    bot.send_message(message.chat.id, "Корзина и данные сброшены. Начните новый заказ!", reply_markup=markup)

bot.polling(none_stop=True)

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(3)
            print(e)
