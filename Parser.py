import time
import requests # импортируем библиотеки
import asyncio
import random
import aiohttp

from datetime import datetime, timedelta
from bs4 import BeautifulSoup as BS

def get_headers(s):
	''' функция создает специальные заголовки для запросов
	если эти заголовки не передавать, то сайт распознает в нас робота, из-за чего
	мы не сможем войти в аккаунт пользователя'''
	headers = s.headers # получаем заголовки, которые уже были обозначены сессией автоматически

	chars = "abcdef1234567890" # массив символов, которые используются в 16-ричной системе счисления. Из них состоит DNSID
	dns_id = ""
	for i in range(40): # создаём DNSID. По сути вся головная боль этого проекта именно в этой штуке
		dns_id += str(random.choice(chars))

	headers.update({"Cookie": "DNSID={}".format(dns_id),
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 OPR/93.0.0.0",
		"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
		"Connection": "keep-alive",
		"Host": "edu.tatar.ru",
		"Referer": "https://www.google.com/",
		"Origin": "https://edu.tatar.ru",
		"Referer": "https://edu.tatar.ru/logon",
		"sec-ch-ua": '"Opera GX";v="93", "Not/A)Brand";v="8", "Chromium";v="107"',
		"Sec-Fetch-User": "?1",
		"sec-ch-ua-platform": "Windows"})

	return headers


async def create_cookie(login, psswd):
	"""
	функция проверяет, существует ли пользователь с таким логином и паролем
	возвращает куки/False
	"""
	url_login = "https://edu.tatar.ru/logon"
	error_url = "https://edu.tatar.ru/message"
	data = {"main_login2": login, "main_password2": psswd}

	session = aiohttp.ClientSession() 
	session.headers.update(get_headers(session))

	r = await session.post(url_login, data=data, allow_redirects=True)
	soup = BS(await r.text(), "lxml")

	if "Мой дневник" in soup.text and r.url != error_url:
		for cookie in session.cookie_jar:
			if cookie.key == "DNSID":
				await session.close()
				return cookie.value
	else:
		await session.close()
		return False

async def check_cookie(cookie):
	"""
	принимает на вход DNSID из бд
	возвращает True, если еще активный DNSID
	возвращает False, если DNSID истек
	"""
	session = aiohttp.ClientSession() 
	session.cookie_jar.update_cookies({"DNSID": cookie})

	async with session.get("https://edu.tatar.ru/user/anketa", allow_redirects=True) as r:
		await session.close()
		if str(r.url) == "https://edu.tatar.ru/logon":
			return False
		else:
			return True

async def get_user_info(cookie): # получаем фио и класс
	session = aiohttp.ClientSession() 
	session.cookie_jar.update_cookies({"DNSID": cookie})

	async with session.get("https://edu.tatar.ru/user/diary/week", allow_redirects=True) as r:
		soup = BS(await r.text(), "lxml")

	await session.close()

	container = soup.find("div", {"class": "top-panel-user"})
	fio = container.find("strong").text
	users_class = container.find("span").text[-9:]

	return fio, users_class


async def parse_day(cookie, next_days_n=0):
	"""
	позволяет узнать оценки за сегодня
	опциональный аргумент next_days_n принимает целое число - количество дней вперед, на которые нужно смотреть дз
	"""
	date = datetime.now() + timedelta(days=next_days_n)

	if date.weekday() == 6:
		return "Воскресенье, отдыхаем!"
	elif date.weekday() < 3: # если смотрим за понедельник, вторник или среду
		start_day = date - timedelta(days=date.weekday()) # получаем число понедельника
	else:
		start_day = date - timedelta(days=date.weekday() - 3) # получаем число четверга

	unix = time.mktime(start_day.timetuple()) # получаем время дня недели по unix
	unix -= unix % 86400 # избавляемся от секунд, минут и часов
	url_week = "https://edu.tatar.ru/user/diary/week?date=" + str(int(unix)) # str(int()) избавляемся от .0

	session = aiohttp.ClientSession() 
	session.cookie_jar.update_cookies({"DNSID": cookie})

	async with session.get(url_week, allow_redirects=True) as r:
		soup = BS(await r.text(), "lxml")

	await session.close()

	table = soup.find("tbody")
	rows = table.find_all("tr")
	day = str(date.day)

	for i in range(len(rows)):
		date_in_edu = rows[i].find("td", {"class": "tt-days"})
		if date_in_edu and int(day) == int(date_in_edu.text):
			today_table = rows[i:i + 8]
			break

	text = f"<b>Домашняя работа на {date.day}.{date.month}.{date.year}</b>\n\n"
	start = time.time()
	for row in today_table:
		if row.text:
			subject = row.find("td", {"class": "tt-subj"}).text.strip("\n").strip(" ")
			task = row.find("td", {"class": "tt-task"}).text.strip("\n").strip(" ")
			mark = row.find("td", {"class": "tt-mark"}).text.strip("\n").strip(" ")

			if subject:
				while True: # убираем лишние символы
					if task.startswith("	"): # если начинается с пустоты, то убираем
						task = task[1:]
					elif task.endswith("	") or task.endswith("\n"): # если заканчивается на пустоту или перенос строки, то убираем
						task = task[:-1]
					elif subject: # убираем условием пустые строки
						text += f"<em>{subject}</em>: " # добавляем его в конечный текст

						if task:
							text += task + " "
						if mark: # если есть оценка
							text += "<b>" + mark + "</b>" + "\n"
						else: text += "\n"
							
						break

	return text

async def parse_term(cookie):
	"""
	функция парсит табель успеваемости
	возвращает строку, содержащую переформатированную табель под хранение в бд
	формат сохранения оценок: item_name|mark_mark_mark_mark_..._mark|gpa;
	"""
	session = aiohttp.ClientSession() 
	session.cookie_jar.update_cookies({"DNSID": cookie})

	async with session.get("https://edu.tatar.ru/user/diary/term", allow_redirects=True) as r:
		soup = BS(await r.text(), "lxml")
	await session.close()

	table_body = soup.find("table", {"class": "table term-marks"}).find("tbody") # нашли табель
	items = table_body.find_all("tr")[:-1] # нашли все предметы (строки) в табели и убрали ИТОГО

	term = ""
	for item in items:
		cells = item.find_all("td")[:-2] # нашли все ячейки в строке и убрали итоговую оценку и просмотр графика
		item_name, marks, gpa = cells[0], cells[1:-1], cells[-1]

		clear_marks = []
		for mark in marks: # удаляем пустые ячейки
			if mark.text != "":
				clear_marks.append(mark)

		term += item_name.text
		if clear_marks: # если есть оценки - есть средний балл - добавляем их
			term += "|"
			for mark in clear_marks:
				term += mark.text + "_"
			term = term[:-1] + "|" # убираем лишнее нижнее подчеркивание от последней оценки, чтобы не было пустого результата при split-е и добавляем разделитель
			term += gpa.text + ";"
		else:
			term += ";"

	term = term[:-1] # убиарем последнюю точку с запятой, чтобы не было пустых результатов при split-е

	return term

if __name__ == "__main__":
	loop = asyncio.get_event_loop()
	from utils import decode_cookie
	cookie = loop.run_until_complete(check_cookie(decode_cookie("1077480640181075687883348737712116608287756555306", 752594294)))
	loop.run_until_complete(parse_day(cookie))

