import time
import telebot
from telebot import types
import json
import os
import random
from config import TOKEN

# Initialize the bot with your Telegram Bot token
bot = telebot.TeleBot(TOKEN)

# Ensure 'rooms' directory exists
os.makedirs('rooms', exist_ok=True)

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Welcome! Choose an option from the menu below:")
    show_menu(user_id)

def show_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    create_room_button = types.KeyboardButton('Create room')
    join_room_button = types.KeyboardButton('Join room')
    markup.add(create_room_button, join_room_button)
    bot.send_message(user_id, "Choose an action:", reply_markup=markup)

def create_room(user_id):
    room_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))
    room_data = {
        'admin': {
            'user_id': user_id,
            'username': bot.get_chat(user_id).username,
            'first_name': bot.get_chat(user_id).first_name,
            'last_name': bot.get_chat(user_id).last_name,
        },
        'players': [],
        'num_players': None,
        'num_words': None,
        'words': [],
    }
    room_filename = f'rooms/{room_code}.json'
    with open(room_filename, 'w') as room_file:
        json.dump(room_data, room_file)
    bot.send_message(user_id, f"Your room has been created! Room code: {room_code}")

def join_room(user_id):
    # Prompt the user to enter a room code
    bot.send_message(user_id, "Enter the room code:")
    bot.register_next_step_handler_by_chat_id(user_id, process_join_code)

def process_join_code(message):
    user_id = message.chat.id
    room_code = message.text.upper()
    room_filename = f'rooms/{room_code}.json'

    if os.path.exists(room_filename):
        # Load the room data
        with open(room_filename, 'r') as room_file:
            room_data = json.load(room_file)

        # Add the user to the 'players' list
        room_data['players'].append({
            'user_id': user_id,
            'username': bot.get_chat(user_id).username,
            'first_name': bot.get_chat(user_id).first_name,
            'last_name': bot.get_chat(user_id).last_name,
        })

        # Update the room JSON file
        with open(room_filename, 'w') as room_file:
            json.dump(room_data, room_file)

        # Send a message to the user indicating a successful join
        bot.send_message(user_id, f"You have joined the room {room_code} successfully!")
    else:
        # Send an error message to the user
        bot.send_message(user_id, "Room not found. Please check the code and try again.")

# Handle the 'Create room' button
@bot.message_handler(func=lambda message: message.text == 'Create room')
def handle_create_room(message):
    user_id = message.chat.id
    create_room(user_id)

# Handle the 'Join room' button
@bot.message_handler(func=lambda message: message.text == 'Join room')
def handle_join_room(message):
    user_id = message.chat.id
    join_room(user_id)

# Ensure the while loop is within the try-except block
while True:
    try:
        bot.polling()
    except ConnectionError as e:
        print(f"Connection error: {e}. Retrying in 10 seconds...")
        time.sleep(10)
