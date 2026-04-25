import requests
import telebot
import json
import random
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from telebot import types
from datetime import datetime
TOKEN = ''
API_KEY = ""

URL_WEATHER_API = 'https://api.openweathermap.org/data/2.5/weather'
URL_WEATHER_GEO = 'https://api.openweathermap.org/geo/1.0/direct'
URL_FORECAST_API = 'https://api.openweathermap.org/data/2.5/forecast'

EMOJI_CODE = {
    200: '⛈', 201: '⛈', 202: '⛈', 210: '🌩', 211: '🌩', 212: '🌩', 221: '🌩',
    230: '⛈', 231: '⛈', 232: '⛈', 300: '🌧', 301: '🌧', 302: '🌧', 310: '🌧',
    311: '🌧', 312: '🌧', 313: '🌧', 314: '🌧', 321: '🌧', 500: '🌧', 501: '🌧',
    502: '🌧', 503: '🌧', 504: '🌧', 511: '🌧', 520: '🌧', 521: '🌧', 522: '🌧',
    531: '🌧', 600: '🌨', 601: '🌨', 602: '🌨', 611: '🌨', 612: '🌨', 613: '🌨',
    615: '🌨', 616: '🌨', 620: '🌨', 621: '🌨', 622: '🌨', 701: '🌫', 711: '🌫',
    721: '🌫', 731: '🌫', 741: '🌫', 751: '🌫', 761: '🌫', 762: '🌫', 771: '🌫',
    781: '🌫', 800: '☀️', 801: '🌤', 802: '☁️', 803: '☁️', 804: '☁️'
}

bot = telebot.TeleBot(TOKEN)


keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
btn_weather = KeyboardButton('📍 Погода сейчас')
btn_forecast = KeyboardButton('📅 Прогноз на 5 дней')
btn_search = KeyboardButton('🔍 Поиск города')
btn_about = KeyboardButton('ℹ️ О проекте')

keyboard.add(btn_weather, btn_forecast)
keyboard.add(btn_search, btn_about)


def get_weather(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'lang': 'ru',
        'units': 'metric',
        'appid': API_KEY
    }

    response = requests.get(URL_WEATHER_API, params=params)
    data = response.json()

    if response.status_code != 200:
        return f"❌ Ошибка: {data.get('message', 'Неизвестная ошибка')}"

    city = data['name']
    desc = data['weather'][0]['description']
    code = data['weather'][0]['id']
    temp = data['main']['temp']
    feels = data['main']['feels_like']
    humidity = data['main']['humidity']
    wind = data['wind']['speed']

    emoji = EMOJI_CODE.get(code, '🌡')

    message = f"🏙 {city}\n\n"
    message += f"{emoji} {desc.capitalize()}\n"
    message += f"🌡 Температура: {temp:.1f}°C\n"
    message += f"🤔 Ощущается: {feels:.1f}°C\n"
    message += f"💧 Влажность: {humidity}%\n"
    message += f"💨 Ветер: {wind} м/с"

    return message

def get_forecast(lat, lon):
    params = {
        'lat': lat,
        'lon': lon,
        'lang': 'ru',
        'units': 'metric',
        'cnt': 40,
        'appid': API_KEY
    }
    response = requests.get(URL_FORECAST_API, params)
    data = response.json()
    if response.status_code != 200:
        return f"❌ Ошибка: {data.get('message', 'Неизвестная ошибка')}"

    city = data['city']['name']
    message = f'Прогноз погоды для {city} на 5 дней:\n\n'

    daily_forecast = {}
    for item in data['list']:
        date = item['dt_txt'].split()[0]
        if date not in daily_forecast:
            daily_forecast[date] = []
        else:
            daily_forecast[date].append(item)
    for date, items in daily_forecast.items():
        temps = [i['main']['temp'] for i in items]
        avg_temp = sum(temps) / len(temps)
        weather = items[len(items) // 2]['weather'][0]
        description = weather['description'].capitalize()
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        formated_date = date_obj.strftime('%d.%m')
        emoji = EMOJI_CODE[weather['id']]
        message += f'{formated_date} {emoji}\n'
        message += f'{avg_temp:.1f}°C (мин: {min(temps):.1f}) (макс: {max(temps):.1f})\n'
        message += f'{description}\n'
        return message


@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = 'Выберите действие:'
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(func=lambda m: m.text == '🔍 Поиск города')
def ask_city(message):
    msg = bot.send_message(message.chat.id, 'Введите название города:')
    bot.register_next_step_handler(msg, search_city)

def search_city(message):
    city = message.text.strip()
    geo_params = {
        'q': city,
        'limit': 1,
        'appid': API_KEY
    }
    response = requests.get(URL_WEATHER_GEO, params = geo_params)
    data = response.json()
    if data:
        lat = data[0]['lat']
        lon = data[0]['lon']
        weather_msg = get_weather(lat, lon)
        bot.send_message(message.chat.id, weather_msg, reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, '❌ Город не найден', reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == '📍 Погода сейчас')
def request_location_for_weather(message):
    location_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    location_keyboard.add(KeyboardButton('📍 Отправить геолокацию', request_location=True))
    bot.send_message(message.chat.id, 'Пожалуйста, отправьте вашу геолокацию:', reply_markup=location_keyboard)
    bot.register_next_step_handler(message, process_location, 'weather')

@bot.message_handler(func=lambda m: m.text == '📅 Прогноз на 5 дней')
def request_location_for_forecast(message):
    location_keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    location_keyboard.add(KeyboardButton('📍 Отправить геолокацию', request_location=True))
    bot.send_message(message.chat.id, 'Пожалуйста, отправьте вашу геолокацию:', reply_markup=location_keyboard)
    bot.register_next_step_handler(message, process_location, 'forecast')

def process_location(message, request_type):
    if message.location:
        lat = message.location.latitude
        lon = message.location.longitude

        if request_type == 'weather':
            weather_msg = get_weather(lat, lon)
            bot.send_message(message.chat.id, weather_msg, reply_markup=keyboard)

        elif request_type == 'forecast':
            forecast_msg = get_forecast(lat, lon)
            bot.send_message(message.chat.id, forecast_msg, reply_markup=keyboard)
    else:
        bot.send_message(message.chat.id, '❌ Не удалось получить геопозицию', reply_markup=keyboard)





@bot.message_handler(func=lambda m: m.text == 'ℹ️ О проекте')
def send_about(message):
    text = '🤖 Бот написан на базе OpenWeather\nhttps://openweathermap.org/'
    bot.send_message(message.chat.id, text, reply_markup=keyboard)


@bot.message_handler(func=lambda m: True)
def handle_text(message):
    bot.send_message(message.chat.id, 'Используйте кнопки меню', reply_markup=keyboard)


bot.infinity_polling()

















































































































