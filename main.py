import telebot
from telebot.types import Message
import requests
import jsons
import datetime
from Class_ModelResponse import ModelResponse

with open('token.txt', 'r', encoding='utf-8') as file:
    API_TOKEN = file.readline()
bot = telebot.TeleBot(API_TOKEN)
BOT_LOR = """ Бот-шутник. Постоянно закидывает шуточками, чтобы жизнь стала веселее. """

# Команды
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "Hello there! I am a bot that always jokes.\n"
        "My commands are:\n"
        "/start - get started with talking\n"
        "/model - the model that is trying to talk to you\n"
        "/clear - delete the history of the chat\n"
        "Let's start talking, should we?"
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['model'])
def send_model_name(message):
    # Отправляем запрос к LM Studio для получения информации о модели
    response = requests.get('http://127.0.0.1:1234/v1/models')

    if response.status_code == 200:
        model_info = response.json()
        model_name = model_info['data'][0]['id']
        bot.reply_to(message, f"I am using {model_name} to talk to you")
    else:
        bot.reply_to(message, 'Can\'t identify the model version.')


@bot.message_handler(commands=['clear'])
def send_model_name(message):
    user_id = message.from_user.id
    if user_id in user_message_history:
        del user_message_history[user_id]
        bot.reply_to(message, 'Bye-bye!')
    else:
        bot.reply_to(message, 'Oooooops..........')


user_message_history = {}


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if user_id not in user_message_history:
        user_message_history[user_id] = [
            {"role": "assistant", "content": BOT_LOR},
            {"role": "system", "content": "Always reply with a joke."}
        ]

    # Получаем историю сообщений текущего пользователя
    user_history = user_message_history.get(user_id, [])

    user_history.append({"role": "user", "content": message.text})

    #  Добавим в контест текущую дату и время
    current_date_time = datetime.datetime.now().strftime("%d %B %Y, %H:%M MSK")
    messages = [{
        "role": "system",
        "content": f"Текущая дата: {current_date_time}"
    }]

    for msg in user_history:
        messages.append(msg)

    bot.send_chat_action(chat_id, "typing")  # like our bot is typing

    # user_query = message.text
    request = {
        "messages": messages
    }
    response = requests.post(
        'http://127.0.0.1:1234/v1/chat/completions',
        json=request
    )

    if response.status_code == 200:
        model_response: ModelResponse = jsons.loads(response.text, ModelResponse)
        reply = model_response.choices[0].message.content
        # Добавляем ответ бота в историю пользователя
        user_history.append({"role": "assistant", "content": reply})
        # Сохраняем усеченную историю
        user_message_history[user_id] = user_history[-30:]
        bot.reply_to(message, reply)
    else:
        txt = 'An error occurred while trying to get the model response...'
        bot.reply_to(message, txt)

    print('do')


# Запуск бота
if __name__ == '__main__':
    bot.polling(none_stop=True)
