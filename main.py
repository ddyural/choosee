import asyncio
import time

from aiogram import Bot, executor, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import * # импортируем токен, сообщения
from keyboards import * # импортируем все, заранее заготовленные, клавиатуры
from states import * # импортируем все необходимое для работы машины состояний
from Parser import * # импортируем средства парсинга
from Database import *

storage = MemoryStorage()

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot, storage=storage)

@dp.message_handler(commands=["start"])
async def welcome(message):
	if check_user(message.from_user.id):
		await message.answer(welcome_message, reply_markup=get_panel_markup())
	else:
		await message.answer(welcome_message, reply_markup=get_welcome_markup())

@dp.message_handler()
async def handler(message):
	if message.text == "🏠Войти в систему edu.tatar":
		await message.answer("Введите свой логин edu.tatar")
		await RegState.get_login.set()
	elif message.text == "🏆Мой рейтинг":
		if get_take_part_in_rating(message.from_user.id)[0]:
			fio, users_class, _ = get_profile(message.from_user.id)
			terms = get_terms(users_class=users_class)
			raiting = create_rating(terms, users_class, fio)

			await message.answer(raiting, reply_markup=get_panel_markup())
		else:
			await message.answer(
					"Вы не участвуете в рейтинге класса! Но это можно изменить в ⚙️Настройках",
					reply_markup=get_panel_markup()
				)
	elif message.text == "📖Информация":
		await message.answer(bot_info_message)
	elif message.text == "🧰Профиль":
		fio, users_class, login = get_profile(message.from_user.id)
		await message.answer("<b>ФИО:</b> " + fio + "\n\n" + "<b>Класс:</b> " + users_class + "\n\n<b>Логин:</b> " + str(login))
	elif message.text == "⚙️Настройки":
		await message.answer("⚙️Настройки:", reply_markup=get_config_markup())
		await ConfigState.select.set()
	elif message.text == "🔧Техподдержка":
		await message.answer(tech_support_message, reply_markup=get_cancel_markup())
		await TechSupportState.wait_message.set()
	elif message.text == "🗑Выйти из системы":
		await message.answer(logout_message, reply_markup=get_welcome_markup())
		delete_user # удаляем запись в бд
	elif message.text == "📕Оценки и дз":
		cookie = get_cookie_data(message.from_user.id)[0] # берем куки для парсинга
		cookie = decode_cookie(cookie, message.from_user.id) # декодируем куки по user_id
		if (await check_cookie(cookie)):

			text = replace_titles_on_custom(
					await parse_day(cookie),
					get_items(message.from_user.id)
				)

			await message.answer(text, reply_markup=get_day_menu_markup())
		else:
			await message.answer("Функция недоступная! Срок действия хранения пароля истек, повторите ввод\n<b>Введите пароль</b>:")
			await UpdatePasswordState.get_password.set()
	elif message.text == "👨‍💼Репетиторы":
		await message.answer(repets_message)
	elif message.text == "📝Добавить заметки":
		await message.answer("Отправьте текст, который я пришлю вам в нужное время!", reply_markup=get_cancel_markup())
		await ReminderState.get_content_state.set()
	else:
		await message.answer(unknown_command_message, reply_markup=get_panel_markup())

# функция в состоянии UpdatePasswordState
@dp.message_handler(state=UpdatePasswordState.get_password)
async def get_updated_password(message, state):
	login = get_profile(message.from_user.id)[2]
	cookie = await create_cookie(login, message.text)
	if cookie:
		cookie = code_cookie(cookie, message.from_user.id) # кодируем куки файлы по user_id
		update_cookie(message.from_user.id, str(cookie))
		await message.answer("Ваш пароль обновлен, можете продолжать пользоваться ботом!")
		await state.finish()
	else:
		await message.answer("Неверный пароль, попробуйте снова")


# функции в состоянии RegState
@dp.message_handler(state=RegState.get_login)
async def get_login(message, state):
	if len(message.text) != 10:
		await message.answer("Ошибка! Обычно, логин содержит 10 цифр, попробуйте еще раз")
	elif not message.text.isdigit():
		await message.answer("Логин не может содержать буквы, попробуйте еще раз")
	else:
		await message.answer("Теперь введите пароль")

		await state.update_data(login=message.text)
		await RegState.get_password.set()

@dp.message_handler(state=RegState.get_password)
async def get_password(message, state):
	login = (await state.get_data()).get("login")
	password = message.text

	cookie = (await create_cookie(login, password))

	if cookie:
		await message.answer(succes_login_message)

		fio, users_class = await get_user_info(cookie)
		term = await parse_term(cookie)
		titles_dict = create_titles_dict(term)
		cookie = code_cookie(cookie, message.from_user.id) # кодируем куки файлы по user_id

		add_new_user(user_id=message.from_user.id, # добавляем в бд фио, класс, логин, пароль
					login=login,
					cookie=cookie,
					fio=fio,
					users_class=users_class,
					term=term,
					custom_titles=titles_dict)

		await state.finish()
		await GetTimeState.get_time.set()
	else:
		await message.answer("Пользователя с таким логином и паролем не существует, пожалуйста, попробуйте снова")
		await message.answer("Введите свой логин edu.tatar")

		await RegState.get_login.set()

# функция в состоянии GetTimeState
@dp.message_handler(state=GetTimeState.get_time) # получаем время отправки дз, полностью завершаем регистрацию пользователя
async def get_time(message, state):
	valid_time = time_is_valid(message.text)
	if valid_time == message.text:
		change_homeworktime(message.from_user.id, message.text) # добавление времени в бд
		await message.answer("✅ <b>Вы успешно выбрали время отправки</b>", reply_markup=get_panel_markup())
		await state.finish()
	else:
		await message.answer(valid_time)

# функция в состоянии ConfigState
@dp.message_handler(state=ConfigState.select)
async def select(message, state):
	if message.text == "⏰Изменить режим отправки сообщений":
		await message.answer("❓ Когда вам будет удобно получать список с домашним заданием?\n<i>(Например: 09:45)</i>")

		await state.finish()
		await GetTimeState.get_time.set()
	elif message.text == "🏆Участвовать в рейтинге класса":
		state = get_take_part_in_rating(message.from_user.id)[0]
		if state:
			await message.answer("Вы больше не участвуете в рейтинге, одноклассники не будут видеть ваш прогресс, а вы их",
								reply_markup=get_config_markup())
		else:
			await message.answer("Теперь вы участвуете в рейтинге класса!",
								reply_markup=get_config_markup())
		update_take_part_in_rating(message.from_user.id, not state)
	elif message.text == "Присылать уведомления об оценках":
		state = get_send_changes(message.from_user.id)[0]
		if state: # если стоит рассылка на True
			await message.answer("Вы больше не будете получать уведомления об оценках",
								reply_markup=get_config_markup())
		else:
			await message.answer("Теперь вы будете получать уведомления о новых оценках!",
								reply_markup=get_config_markup())
		update_send_changes(message.from_user.id, not state)
	elif message.text == "Изменить названия предметов":
		await message.answer("<b>Выберите предмет из списка</b>\n\n\
			Его имя в списке дз будет отображаться так, как вы захотите",
			reply_markup=get_items_markup(
				get_items(
					message.from_user.id
					)
				)
			)
		await CustomizeTitleState.select_item.set()
	elif message.text == "Назад🔙":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
		await state.finish()

# функции в состоянии TechSupportState
@dp.message_handler(state=TechSupportState.wait_message)
async def wait_message(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
	else:
		for admin_id in ADMINS:
			await bot.send_message(
				admin_id, message.text + "\n" + message.from_user.first_name + "    " + message.from_user.username)

		await message.answer(
					"Ваше сообщение передано администраторам. Спасибо за обратную связь!",
					reply_markup=get_panel_markup())

	await state.finish()

# функции в состоянии ReminderState
@dp.message_handler(state=ReminderState.get_content_state)
async def get_content_state(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
		await state.finish()
	else:
		await state.update_data(content=message.text)
		await message.answer("Отлично! Теперь мне нужна дата. Отправьте её в формате <b>дд.мм.гг</b>")
		await ReminderState.get_date_state.set()

@dp.message_handler(state=ReminderState.get_date_state)
async def get_date_state(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
		await state.finish()
	else:
		valid_date = date_is_valid(message.text)

		if valid_date == message.text:
			await state.update_data(date=valid_date)
			await message.answer(
				"Последний шаг. Отправьте время в формате <b>чч:мм</b>, в которое вы получите это сообщение")
			await ReminderState.get_time_state.set()
		else:
			await message.answer(valid_date)

@dp.message_handler(state=ReminderState.get_time_state)
async def get_time_state(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
		await state.finish()
	else:
		valid_time = time_is_valid(message.text)

		if valid_time == message.text:
			state_data = await state.get_data()
			content, date = state_data.get("content"), state_data.get("date")

			create_reminder(
					user_id=message.from_user.id,
					content=content,
					date=date,
					time=valid_time
				)

			await message.answer(
				f"Напоминание сохранено и придёт вам {date} в {message.text}",
				reply_markup=get_panel_markup())

			await state.finish()
		else:
			await message.answer(valid_time)

# функции в состоянии CustomizeTitleState
@dp.message_handler(state=CustomizeTitleState.select_item)
async def select_item(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_config_markup())
		await ConfigState.select.set()
	else:
		await state.update_data(source_item_name=message.text)
		await message.answer("✅ Введите новое название для этого предмета", reply_markup=get_cancel_markup())
		await CustomizeTitleState.custom_title.set()

@dp.message_handler(state=CustomizeTitleState.custom_title)
async def custom_title(message, state):
	if message.text == "Отмена":
		await message.answer("Возвращаю обратно...", reply_markup=get_panel_markup())
	else:
		source_item_name = (await state.get_data()).get("source_item_name")
		item_names = get_items(message.from_user.id)

		custimized_titles = ""
		for item in item_names[0].split(";"):
			if source_item_name == item.split(":")[0]:
				item = f"{source_item_name}:{message.text}"

			custimized_titles += item + ";"


		update_items(message.from_user.id, custimized_titles[:-1])

		await message.answer(
						f"Название предмета <b>{source_item_name}</b> заменено на <b>{message.text}</b>",
						reply_markup=get_config_markup()
					)

	await ConfigState.select.set()

# функция отвечает за обработку inline клавиш
@dp.callback_query_handler()
async def day_menu(callback):
	if callback.data.startswith("back"):
		page_num = int(callback.data.split("_")[1]) - 1
	elif callback.data.startswith("next"):
		page_num = int(callback.data.split("_")[1]) + 1

	cookie = get_cookie_data(callback.from_user.id)[0]
	cookie = decode_cookie(cookie, callback.from_user.id) # декодируем куки по user_id
	if (await check_cookie(cookie)):

		day_info = await parse_day(cookie, next_days_n=page_num)
		text = replace_titles_on_custom(
					day_info,
					get_items(callback.from_user.id)
				)

		day_menu_markup = get_day_menu_markup(page_num=page_num)

		await callback.message.edit_text(text=text, reply_markup=day_menu_markup)
	else:
		await message.answer("Функция недоступная! Срок действия хранения пароля истек, повторите ввод\n<b>Введите пароль</b>:")
		await UpdatePasswordState.set()

	await callback.answer()

if __name__ == "__main__":
	from utils import time_is_valid, date_is_valid,reminder_sender,\
	homework_sender, term_checker, create_titles_dict, replace_titles_on_custom,\
	create_rating, code_cookie, decode_cookie

	init_db()

	loop = asyncio.get_event_loop() # получаем цикл событий
	loop.create_task(homework_sender()) # добавляем к циклу функцию рассылки дз
	loop.create_task(term_checker()) # добавляем к циклу функцию проверки оценок
	loop.create_task(reminder_sender()) # добавляем к циклу функцию проверки оценок

	executor.start_polling(dp, skip_updates=False, loop=loop)