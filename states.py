from aiogram.dispatcher.filters.state import State, StatesGroup

class RegState(StatesGroup):
	get_login = State()
	get_password = State()

class GetTimeState(StatesGroup):
	get_time = State()

class ConfigState(StatesGroup):
	select = State()

class TechSupportState(StatesGroup):
	wait_message = State()

class ReminderState(StatesGroup):
	get_content_state = State()
	get_date_state = State()
	get_time_state = State()

class CustomizeTitleState(StatesGroup):
	select_item = State()
	custom_title = State()

class UpdatePasswordState(StatesGroup):
	get_password = State()