from flask import Flask, request
import telebot
import requests
import schedule
import time
from datetime import datetime, timedelta
import os

app = Flask(__name__)

TOKEN = os.environ['BOT_TOKEN']
EVENTBRITE_TOKEN = os.environ['EVENTBRITE_TOKEN']  # Pega tu key aquí (gratis en Eventbrite)
MEETUP_KEY = os.environ['MEETUP_KEY']  # Pega tu key aquí (gratis en Meetup)

bot = telebot.TeleBot(TOKEN)
users = []  # Lista de suscriptores (chat IDs)

@bot.message_handler(commands=['start'])
def start(m):
    chat_id = m.chat.id
    if chat_id not in users:
        users.append(chat_id)
        bot.reply_to(m, "🧘 ¡Suscrito a Yoga Alerts en Rosemont! Recibirás notifs diarias de clases cercanas. /stop para salir.")
    else:
        bot.reply_to(m, "Ya estás suscrito. ¡Checa mañana!")

@bot.message_handler(commands=['stop'])
def stop(m):
    chat_id = m.chat.id
    if chat_id in users:
        users.remove(chat_id)
        bot.reply_to(m, "Desuscrito. Usa /start pa' volver.")
    else:
        bot.reply_to(m, "No estabas suscrito.")

def get_yoga_events():
    events = []
    
    # Eventbrite API
    url = "https://www.eventbriteapi.com/v3/events/search/"
    params = {
        "token": EVENTBRITE_TOKEN,
        "location.address": "Rosemont, Montreal",
        "location.within": "5km",
        "q": "yoga",
        "start_date.range_start": datetime.now().isoformat(),
        "start_date.range_end": (datetime.now() + timedelta(days=7)).isoformat()
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        for event in data.get("events", [])[:3]:
            events.append(f"🧘 {event['name']['text']} - {event['start']['local'][:16]} - {event['venue']['address']['localized_area_display']} [Link]({event['url']})")
    
    # Meetup API
    url = "https://api.meetup.com/find/upcoming_events"
    params = {
        "key": MEETUP_KEY,
        "location": "Rosemont, Montreal",
        "topic": "yoga",
        "page": 3
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        for event in data.get("events", [])[:3]:
            events.append(f"🧘 {event['name']} - {event['local_date'][:16]} - {event['venue']['name']} [Link]({event['event_url']})")
    
    return events if events else ["No hay yoga hoy, pero checa Aloha Yoga pa' clases semanales."]

def send_daily_events():
    events = get_yoga_events()
    msg = "*🧘 YOGA ALERTS HOY EN ROSEMONT* 🔥\n\n" + "\n".join(events)
    for chat_id in users:
        bot.send_message(chat_id, msg, parse_mode="Markdown", disable_web_page_preview=False)

schedule.every().day.at("08:00").do(send_daily_events)

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    bot.process_new_updates(request.get_json(force=True))
    return 'OK'

@app.route('/')
def index():
    bot.remove_webhook()
    bot.set_webhook(url=os.environ['URL'] + '/' + TOKEN)
    return 'Yoga Bot vivo! Suscríbete con /start'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
