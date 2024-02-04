import os
import time
import json
import random
import telebot
from config import TOKEN
from telebot import types

# Initialize the bot with your Telegram Bot token
bot = telebot.TeleBot(TOKEN)

# Ensure 'rooms' directory exists
os.makedirs('rooms', exist_ok=True)

# Dictionary to store information about game rooms
rooms = {}


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Привіт, це гра Імперія. Тут потрібно вгадати хто яке слово загадав:")
    show_menu(user_id)


def show_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    create_room_button = types.KeyboardButton('Створити кімнату')
    join_room_button = types.KeyboardButton('Зайти в кімнату')
    markup.add(create_room_button, join_room_button)
    bot.send_message(user_id, "Вибери:", reply_markup=markup)


def generate_room_code():
    return ''.join(random.choices('1234567890', k=4))


def initialize_room_data(user_id):
    return {
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


def create_room(user_id, input_type=None, room_code=None, room_data=None, message=None):
    if input_type is None:
        # Generate a random room code
        room_code = generate_room_code()

        # Initialize room data
        room_data = initialize_room_data(user_id)

        # Update the rooms dictionary
        rooms[room_code] = room_data

        # Ask the admin for the number of players
        bot.send_message(user_id, "Скільки буде гравців?")
        bot.register_next_step_handler_by_chat_id(user_id,
                                                  lambda m: create_room(user_id, 'num_players', room_code, room_data,
                                                                        m))
    else:
        try:
            # Parse the user's input as an integer
            input_value = int(message.text)

            # Update the room data
            room_data[input_type] = input_value

            # Ask for the number of additional words if 'num_players' is processed
            if input_type == 'num_players':
                bot.send_message(user_id, "Скільки додаткових слів додасть адмін?")
                bot.register_next_step_handler_by_chat_id(user_id,
                                                          lambda m: create_room(user_id, 'num_words', room_code,
                                                                                room_data, m))
            else:
                # Create a JSON file for the room
                room_filename = f'rooms/{room_code}.json'
                with open(room_filename, 'w') as room_file:
                    json.dump(room_data, room_file)

                # Send a message to the admin indicating the room is created
                bot.send_message(user_id, f"Кімнату створено! Код входу: {room_code}")

                # Introduce a delay of 3 seconds before calling ask_a_word for the admin
                time.sleep(3)
                # Call ask_a_word for the admin after the room is created
                ask_a_word(user_id, room_code, is_admin=True)
        except ValueError:
            bot.send_message(user_id, "Будь ласка, введіть валідний номер.")
            create_room(user_id, input_type, room_code, room_data)


def join_room(user_id):
    # Prompt the user to enter a room code
    bot.send_message(user_id, "Ведіть Код входу:")
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
        bot.send_message(user_id, f"Ви зайшли в кімнату {room_code} успішно!")

        # Introduce a delay (adjust as needed) before calling ask_a_word for the player
        time.sleep(3)

        # Call ask_a_word for the player after joining the room
        ask_a_word(user_id, room_code, is_admin=False)
    else:
        # Send an error message to the user
        bot.send_message(user_id, "Кімнату не знайдено. Уточніть код в адміна.")


# Handle the 'Create room' button
@bot.message_handler(func=lambda message: message.text == 'Створити кімнату')
def handle_create_room(message):
    user_id = message.chat.id
    create_room(user_id)


# Handle the 'Join room' button
@bot.message_handler(func=lambda message: message.text == 'Зайти в кімнату')
def handle_join_room(message):
    user_id = message.chat.id
    join_room(user_id)


def ask_a_word(user_id, room_code, is_admin=False):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    button_text = "Як адмін, будь ласка, додайте слово:" if is_admin else "Будь ласка, введіть слово:"

    bot.send_message(user_id, button_text, reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(user_id, lambda message: process_word(message, room_code, is_admin))


def process_word(message, room_code, is_admin):
    user_id = message.chat.id
    word = message.text

    room_filename = f'rooms/{room_code}.json'

    if os.path.exists(room_filename):
        with open(room_filename, 'r') as room_file:
            room_data = json.load(room_file)

        if is_admin:
            # Store the admin word in 'words' list
            room_data['words'].append({'user_id': user_id, 'word': word})
        else:
            # Store player words in 'words' list
            room_data['words'].append({'user_id': user_id, 'word': word})

        with open(room_filename, 'w', encoding='utf-8') as room_file:
            json.dump(room_data, room_file, ensure_ascii=False)  # Set ensure_ascii to False

        confirmation_message = f"Слово додали: {word}"
        bot.send_message(user_id, confirmation_message)
    else:
        bot.send_message(user_id, "Кімнату не знайдено. Будь ласка, уточніть код в адміна.")


@bot.message_handler(commands=['go'])
def get_words(message):
    user_id = message.chat.id
    room_code = get_user_room_code(user_id)

    print(f"DEBUG - User ID: {user_id}, Room Code: {room_code}")

    if room_code:
        room_filename = f'rooms/{room_code}.json'
        if os.path.exists(room_filename):
            with open(room_filename, 'r') as room_file:
                room_data = json.load(room_file)

            words_list = [word['word'] for word in room_data['words']]
            words_message = "\n".join(words_list)

            # Send words to the admin with the clear_words button
            if user_id == room_data['admin']['user_id']:
                markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                clear_words_button = types.KeyboardButton('/clear_words')
                markup.add(clear_words_button)

                clear_words_message = (
                    f"Слова в кімнаті {room_code}:\n{words_message}\n\n"
                    "Натисни /clear_words щоб очистити введені слова і зіграти знову."
                )

                bot.send_message(user_id, clear_words_message, reply_markup=markup)
            else:
                bot.send_message(user_id, f"Слова в кімнаті {room_code}:\n{words_message}")

            # Send words to all players
            for player in room_data['players']:
                bot.send_message(player['user_id'], f"Слова в кімнаті {room_code}:\n{words_message}")
        else:
            bot.send_message(user_id, "Кімнату не знайдено. Будь ласка уточніть код в адміна.")
    else:
        bot.send_message(user_id, "Ви не в кімнаті. Будь ласка створіть чи зайдіть в кімнату.")


# Function to get the latest room code associated with a user
def get_user_room_code(user_id):
    user_rooms = [(room_code, room_data) for room_code, room_data in rooms.items() if
        user_id == room_data['admin']['user_id'] or any(
            player['user_id'] == user_id for player in room_data['players'])]

    if user_rooms:
        # Return the latest room code (based on creation time)
        latest_room = max(user_rooms, key=lambda x: os.path.getctime(f'rooms/{x[0]}.json'))
        return latest_room[0]

    return None


@bot.message_handler(commands=['clear_words'])
def clear_words(message):
    user_id = message.chat.id
    room_code = get_user_room_code(user_id)

    if room_code:
        room_filename = f'rooms/{room_code}.json'
        if os.path.exists(room_filename):
            with open(room_filename, 'r') as room_file:
                room_data = json.load(room_file)

            # Clear the 'words' list
            room_data['words'] = []

            # Save the updated room data
            with open(room_filename, 'w', encoding='utf-8') as room_file:
                json.dump(room_data, room_file, ensure_ascii=False)

            # Send a message to the admin
            bot.send_message(user_id, "Слова видалено.")

            # Trigger ask_a_word for admin
            ask_a_word(user_id, room_code, is_admin=True)

            # Trigger ask_a_word for all players
            for player in room_data['players']:
                ask_a_word(player['user_id'], room_code, is_admin=False)
        else:
            bot.send_message(user_id, "Кімнату не знайдено. Будь ласка, уточніть код в адміна.")
    else:
        bot.send_message(user_id, "Ви не в кімнаті. Будь ласка створіть або зайдіть в кімнату.")


# Ensure the while loop is within the try-except block
while True:
    try:
        bot.polling()
    except ConnectionError as e:
        print(f"Connection error: {e}. Retrying in 10 seconds...")
        time.sleep(10)
