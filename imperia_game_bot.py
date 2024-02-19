import os
import time
import json
import random
import telebot
from config import TOKEN
from telebot import types
from datetime import datetime

# Initialize the bot with your Telegram Bot token
bot = telebot.TeleBot(TOKEN)

# Ensure 'rooms' directory exists
os.makedirs('rooms', exist_ok=True)

# Dictionary to store information about game rooms
rooms = {}


def log_user_info(user_id, username, first_name, last_name):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    file_path = 'user_log.txt'

    # Check if the file exists, create it if not
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            pass  # Create an empty file

    # Check if the user information already exists in the log file
    with open(file_path, 'r') as log_file:
        existing_users = log_file.readlines()
        for user_info in existing_users:
            if str(user_id) in user_info:
                return  # User already logged, so exit the function

    # If user information doesn't exist in the log file, append it with date and time
    with open(file_path, 'a') as log_file:
        log_file.write(
            f"{current_time}: User ID: {user_id}, Username: "
            f"{username}, First Name: {first_name}, Last Name: {last_name}\n")


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    username = message.chat.username
    first_name = message.chat.first_name
    last_name = message.chat.last_name

    # Log user information
    log_user_info(user_id, username, first_name, last_name)

    bot.send_message(user_id, "Привіт, це гра Імперія. Тут потрібно вгадати хто яке слово загадав:")
    show_menu(user_id)


def show_menu(user_id):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    create_room_button = types.KeyboardButton('Створити кімнату')
    join_room_button = types.KeyboardButton("Зайти в кімнату")
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
    else:
        try:
            # Parse the user's input as an integer
            input_value = int(message.text)

            # Update the room data
            room_data[input_type] = input_value

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
    if is_admin:
        markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
        done_button = types.KeyboardButton('/done')
        markup.add(done_button)

        bot.send_message(user_id, "Як адмін, додайте слово або натисніть кнопку нижче, щоб завершити додавання слів:",
                         reply_markup=markup)
    else:
        bot.send_message(user_id, "Будь ласка, введіть слово:")

    bot.register_next_step_handler_by_chat_id(user_id, lambda message: process_word(message, room_code, is_admin))


def process_word(message, room_code, is_admin):
    user_id = message.chat.id
    word = message.text

    if is_admin:
        if word.lower() == '/done':
            bot.send_message(user_id, "Додавання слів завершено.")
            ask_to_start_game(user_id, room_code)
        else:
            add_word_to_room(user_id, room_code, word)
            ask_a_word(user_id, room_code, is_admin)
    else:
        add_word_to_room(user_id, room_code, word)
        bot.send_message(user_id, "Слово додано.")


def add_word_to_room(user_id, room_code, word):
    room_filename = f'rooms/{room_code}.json'

    if os.path.exists(room_filename):
        with open(room_filename, 'r') as room_file:
            room_data = json.load(room_file)

        # Store the word in 'words' list
        room_data['words'].append({'user_id': user_id, 'word': word})

        # Save the updated room data
        with open(room_filename, 'w', encoding='utf-8') as room_file:
            json.dump(room_data, room_file, ensure_ascii=False)

    else:
        bot.send_message(user_id, "Кімнату не знайдено. Будь ласка, уточніть код в адміна.")


def ask_to_start_game(user_id, room_code):
    markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
    start_game_button = types.KeyboardButton('/go')
    markup.add(start_game_button)

    bot.send_message(user_id, "Натисніть /go, щоб розпочати гру.", reply_markup=markup)


@bot.message_handler(commands=['go'])
def get_words(message):
    user_id = message.chat.id
    room_code = get_user_room_code(user_id)

    if room_code:
        room_filename = f'rooms/{room_code}.json'
        if os.path.exists(room_filename):
            with open(room_filename, 'r') as room_file:
                room_data = json.load(room_file)

            # Shuffle the words in random order
            random.shuffle(room_data['words'])

            words_list = [word['word'] for word in room_data['words']]
            words_message = "\n".join(words_list)

            # Send words to the admin with the clear_words button
            if user_id == room_data['admin']['user_id']:
                markup = types.ReplyKeyboardMarkup(row_width=1, resize_keyboard=True)
                clear_words_button = types.KeyboardButton('/clear_words')
                markup.add(clear_words_button)

                clear_words_message = (
                    f"Слова в кімнаті {room_code} (випадковий порядок):\n{words_message}\n\n"
                    "Натисни /clear_words щоб очистити введені слова і зіграти знову або "
                    "/delete_room щоб видалити кімнату і закінчити гру."
                )

                bot.send_message(user_id, clear_words_message, reply_markup=markup)
            else:
                bot.send_message(user_id, f"Слова в кімнаті {room_code} (випадковий порядок):\n{words_message}")

            # Send words to all players
            for player in room_data['players']:
                bot.send_message(player['user_id'],
                                 f"Слова в кімнаті {room_code} (випадковий порядок):\n{words_message}")
        else:
            bot.send_message(user_id, "Кімнату не знайдено. Будь ласка, уточніть код в адміна.")
    else:
        bot.send_message(user_id, "Ви не в кімнаті. Будь ласка створіть чи зайдіть в кімнату.")


# Function to get the latest room code associated with a user
def get_user_room_code(user_id):
    user_rooms = [(room_code, room_data) for room_code, room_data in rooms.items() if
        user_id == room_data['admin']['user_id'] or any(
            player['user_id'] == user_id for player in room_data['players'])]

    if user_rooms:
        # Return the latest room code (based on creation time) if the room file exists
        for room_code, _ in sorted(user_rooms, key=lambda x: os.path.getctime(f'rooms/{x[0]}.json') if os.path.exists(
                f'rooms/{x[0]}.json') else 0, reverse=True):
            if os.path.exists(f'rooms/{room_code}.json'):
                return room_code

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


@bot.message_handler(commands=['rules'])
def rules(message):
    user_id = message.chat.id
    rules_message = (
        "Правила гри Імперія:\n"
        "0. /start щоб розпочати.\n"
        "1. Адмін створює кімнату та вказує кількість гравців.\n"
        "2. Гравці долучаються до кімнати за допомогою Коду.\n"
        "3. Адмін та гравці додають слова.\n"
        "4. Після додавання усіх слів, адмін натискає /go, щоб всі побачили слова у випадковому порядку.\n"
        "5. Гравці по черзі вгадують хто яке слово загадав. Треба назвати слово і ім'я\n"
        "6. Той кого назвали повинен підтвердити чи спростувати гіпотезу\n"
        "7. Не можна двічі опитувати того самого гравця\n"
        "8. Якщо гравець A вгадав слово гравця B, то гравець "
        "B приєднується в його імперію (вони разом повинні вгадати наступне слово)\n"
        "9. Якщо інший гравець (С) вгадав слово гравця А, то обидва гравці А і В приєднуються в імперію гравця С\n"
        "10. Мета гри залучити всіх гравців в одну імперію (вгадавши всі слова)\n"
        "11. Після вгадування всіх слів, адмін натискає /clear_words, "
        "щоб очистити слова в Кімнаті та зіграти знову. Або можна створити нову кімнату\n"
    )
    bot.send_message(user_id, rules_message)


@bot.message_handler(commands=['contact_developer'])
def contact_developer(message):
    user_id = message.chat.id
    contact_message = (
        "Ідеї, запитання, просто подякувати:\n"
        "Електронна пошта: m.khranovskyi@gmail.com\n"
        "Телеграм: @mik788"
    )
    bot.send_message(user_id, contact_message)


@bot.message_handler(commands=['delete_room'])
def delete_room(message):
    user_id = message.chat.id
    room_code = get_user_room_code(user_id)

    if room_code:
        room_filename = f'rooms/{room_code}.json'
        if os.path.exists(room_filename):
            os.remove(room_filename)  # Delete the room file
            bot.send_message(user_id, f"Кімнату з кодом {room_code} було видалено.")
        else:
            bot.send_message(user_id, "Кімнату не знайдено.")
    else:
        bot.send_message(user_id, "Ви не в кімнаті. Будь ласка, створіть або зайдіть в кімнату.")

    # Remove the keyboard markup after deleting the room
    bot.send_message(user_id, "Видалено кімнату. Натисни /contact_developer для зв'язку з розробником."
                              "\nАбо /start щоб розпочати гру знову.",
                     reply_markup=types.ReplyKeyboardRemove())


# Start the bot
bot.infinity_polling(timeout=10, long_polling_timeout = 5)
