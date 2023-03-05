import time
import asyncio

from datetime import datetime

from main import bot
from Database import get_cookie_data, get_homeworktime, get_terms, update_term, get_reminders, delete_reminder
from Parser import parse_day, parse_term, check_cookie
from keyboards import get_panel_markup


def decode_cookie(coded, key):
	decoded = int(coded) - key # вычитаем из закодированного dns_id 10-ичный ключ
	decoded = hex(decoded).strip("0x") # переводим раскодированный dns_id в 16-ричную сс и убираем 0x
	return decoded

def code_cookie(dns_id, key):
	dns_id = int(dns_id, 16) # переводим dns_id в 10-ричную сс
	coded = dns_id + key # прибавляем к получившимуся значению 10-ичный ключ
	return coded

def time_is_valid(time):
	"""
	возвращает исходное время, если оно правильное
	возвращает текст ошибки, если время не подходит по формату
	"""
	if ":" in time:
		if time[0:2].isdigit() and time[3:5].isdigit() and len(time) == 5:
			if int(time[0:2]) < 24 and int(time[3:5]) < 60:
				return time
			else:
				return "❌ Подозрительно большие числа... Повторите попытку"
		else:
			return "❌ Неверный формат времени, попробуйте еще раз"
	else:
		return "❌ Вы пропустили двоеточие!"

def date_is_valid(date):
	"""
	возвращает исходную дату, если она правильная 
	возвращает текст ошибки, если дата не подходит по формату
	"""
	try:
		day, month, year = [int(i) for i in date.split(".")]
		year = int("20" + str(year))
		datetime_date = datetime(day=day, month=month, year=year)
		date_now = datetime.now()
		formate_date_now = datetime(
				day=date_now.day,
				month=date_now.month,
				year=date_now.year
			)

		if datetime_date >= formate_date_now:
			return date
		else:
			return "❌ Введенный день уже прошел ❌\nЯ могу отправить напоминание сегодня или потом"
	except Exception as e:
		return "❌ Введена неверная дата! ❌\nПопробуйте снова"
	
def create_titles_dict(term):
	"""
	возвращает словарь
	{"название предмета": "название предмета"}
	нужен для будущего создания своих имен предметам
	"""
	translate_dict = {
	"Родная литература": "Родная лит-ра",
	"Информатика": "Информ.",
	"Литература": "Лит-ра",
	"Русский язык": "Рус.яз.",
	"Основы безопасности жизнедеятельности": "ОБЖ",
	"Физическая культура": "Физ-ра",
	"Математика": "Матем.",
	"Иностранный язык (английский)": "Ин. яз. (англ.)"}

	items = term.split(";")
	titles_text = ""

	for item in items:
		item_name = item.split("|")[0]
		if translate_dict.get(item_name):
			item_name = translate_dict[item_name]

		titles_text += f"{item_name}:{item_name};"


	return titles_text[:-1]

def replace_titles_on_custom(day_info, custom_titles):
	"""
	меняет названия предметов на кастомные.
	Принимает на вход текст от функции parse_day и названия предметов
	"""
	for item in custom_titles[0].split(";"):
		title, custom_title = item.split(":")
		day_info = day_info.replace(title, custom_title)

	return day_info

def create_rating(terms, users_class, my_fio):
	"""
	принимает на вход табели из бд учеников из одного класса, класс ученика и фиол
	функция возвращает рейтинг в классе в формате 
	1 место: ученик, балл
	2 место: ученик, балл
	3 место: ученик, балл
	Моё место, мой балл
	средний балл считается, как среднее арефметическое всех баллов по предметам. Аналог на сайте - поле "ИТОГО"
	"""
	gpas = []

	for user in terms:
		fio, term = user[0], user[1]
		points = []
		for item in term.split(";"):
			if len(item.split("|")) != 1:
				points.append(float(item.split("|")[-1])) # добавляем оценки в список

		gpa = sum(points) / len(points) # находим средний балл
		if fio == my_fio:
			my_gpa = {"fio": fio, "gpa": gpa} # нужен для показа моего места в рейтинге
		gpas.append({ # добавляем в общий список, для сортировки и показа рейтинга
			"fio": fio,
			"gpa": gpa})

	gpas.sort(reverse=True, key=lambda e: e['gpa']) # сортируем по среднему баллу

	text = f"<b>Рейтинг в <em>{users_class}е</em></b>\n\n"
	if len(gpas) >= 1:
		text += f"🥇 место: {gpas[0]['fio']} с баллом {str(gpas[0]['gpa'])[:5]}\n"
	if len(gpas) >= 2:
		text += f"🥈 место: {gpas[1]['fio']} с баллом {str(gpas[1]['gpa'])[:5]}\n"
	if len(gpas) >= 3:
		text += f"🥉 место: {gpas[2]['fio']} с баллом {str(gpas[2]['gpa'])[:5]}\n\n"

	text += f"Ваше место в рейтинге: {gpas.index(my_gpa) + 1}, балл {str(my_gpa['gpa'])[:5]}"
	return text

async def homework_sender():
	"""
	асинхронная функция, которая раз в минуту проверяет, кому нужно отправить дз и отсылает
	"""
	while True:
		timik = time.localtime()
		hours = time.strftime('%H', timik)
		mins = time.strftime('%M', timik)

		homeworktimes = get_homeworktime()
		for user in homeworktimes:
			homework_time_str = str(hours) + ':' + str(mins)

			if user[1] == homework_time_str:
				cookie = get_cookie_data(user[0])[0]
				cookie = decode_cookie(cookie, user[0])
				if (await check_cookie(cookie)):
					day_info = await parse_day(cookie, next_days_n=1) # передаем логин, пароль и смотрим дз на один день вперед

					await bot.send_message(user[0], day_info)

		await asyncio.sleep(60)

async def term_checker():
	"""
	асинхронная функция, раз в N секунд проверяет все табели успеваемости, сравнивает со старой в бд и, если найдены изменения, отсылает их
	"""
	while True:
		start = time.time()
		terms = get_terms()
		tasks = []

		for user in terms:
			if user[2]: # если стоит метка о том, что нужно рассылать новые оценки
				cookie = get_cookie_data(user[0])[0] # получаем логин и пароль
				cookie = decode_cookie(cookie, user[0])
				if (await check_cookie(cookie)):
					asyncio.create_task( # создаем таски в виде функций find_changes
						find_changes(
							cookie=cookie,
							user=user
							)
						)

		asyncio.gather(*tasks)
		await asyncio.sleep(30)

async def find_changes(cookie, user):
	"""
	асинхронная функция, выполняет поиск новых оценок в табели успеваемости
	вызывается из term_checker асинхронно с помощью тасков
	"""
	new_term_for_db = await parse_term(cookie)

	new_term = new_term_for_db.split(";")
	old_term = user[1].split(";")

	for i in range(len(new_term)):
		item_name = old_term[i].split("|")[0]

		if len(new_term[i].split("|")) > 1 and len(old_term[i].split("|")) > 1:
			new_marks = new_term[i].split("|")[1].split("_")
			old_marks = old_term[i].split("|")[1].split("_")
		elif len(new_term[i].split("|")) > 1 and len(old_term[i].split("|")) == 1:
			new_marks = new_term[i].split("|")[1].split("_")
			old_marks = []
		else:
			new_marks = []
			old_marks = []

		changes = []

		for j in range(1, 6): # цикл проверки количества оценок. 1 и 6 - диапазон оценок в edu tatar (6 не учитыается в цикле)
			if old_marks.count(str(j)) != new_marks.count(str(j)):
				for i in range(new_marks.count(str(j)) != old_marks.count(str(j))):
					changes.append(str(j))

		if changes: # если найдены новые оценки, то сразу их высылаем
			await bot.send_message(user[0],
					f"У вас новые оценки по предмету <em>{item_name}</em>: " + " ".join(changes))

			update_term(user[0], new_term_for_db)

async def reminder_sender():
	"""
	асинхронная функция, которая проверяет каждую минуту таблицу reminders
	если есть сейчас время, чтобы отправить напоминание - отправляет
	"""
	while True:
		reminders = get_reminders()
		for user in reminders:
			date, time = user[4], user[3]
			if date == datetime.now().strftime("%d.%m.%y") and time == datetime.now().strftime("%H:%M"):
				await bot.send_message(
					user[1],
					text="<b>Напоминаю!</b>\n\n" + user[2],
					reply_markup=get_panel_markup())

				delete_reminder(user[1], date, time)

		await asyncio.sleep(60)

if __name__ == "__main__":
	terms = get_terms(users_class="11г класс")
	print(create_rating(terms, "11бг класс", "Бахтиева Аделина Альфредовна"))