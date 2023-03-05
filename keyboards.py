from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup

def get_welcome_markup():
	markup = ReplyKeyboardMarkup(True, True)

	markup.add(
		KeyboardButton("🏠Войти в систему edu.tatar")
		)

	return markup

def get_panel_markup():
	markup = ReplyKeyboardMarkup(True, True, row_width=2)

	markup.add(
			KeyboardButton(text="🧰Профиль"),
			KeyboardButton(text="🏆Мой рейтинг"),
			KeyboardButton(text="📕Оценки и дз"),
			KeyboardButton(text="📖Информация"),
			KeyboardButton(text="⚙️Настройки"),
			KeyboardButton(text="🔧Техподдержка"),
			KeyboardButton(text="📝Добавить заметки"),
			KeyboardButton(text="👨‍💼Репетиторы"),
			KeyboardButton(text="🗑Выйти из системы")
		)

	return markup

def get_config_markup():
	markup = ReplyKeyboardMarkup(True, True, row_width=1)

	markup.add(
		KeyboardButton(text="⏰Изменить режим отправки сообщений"),
		KeyboardButton(text="Изменить названия предметов"),
		KeyboardButton(text="🏆Участвовать в рейтинге класса"),
		KeyboardButton(text="Присылать уведомления об оценках"),
		KeyboardButton(text="Назад🔙"))

	return markup

def get_day_menu_markup(page_num=0):
	markup = InlineKeyboardMarkup()

	markup.add(
		InlineKeyboardButton(text="⏪", callback_data=f"back_{page_num}"),
		InlineKeyboardButton(text="⏩", callback_data=f"next_{page_num}")
		)

	return markup

def get_items_markup(items):
	markup = ReplyKeyboardMarkup(True, True, row_width=2)

	markup.add(KeyboardButton(text="Отмена"))
	for item in items[0].split(";"):
		if item.split(':')[1] == item.split(':')[0]:
			text = item.split(':')[0]
		else:
			text = f"{item.split(':')[1]}({item.split(':')[0]})"
		markup.add(KeyboardButton(text=text))


	return markup

def get_cancel_markup():
	markup = ReplyKeyboardMarkup(resize_keyboard=True)
	markup.add(
		KeyboardButton(text="Отмена")
		)

	return markup