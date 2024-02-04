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

# Dictionary to store information about game rooms
rooms = {}


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


# ... (previous code)

def create_room(user_id, input_type=None, room_code=None, room_data=None, message=None):
    if input_type is None:
        # Generate a random room code
        room_code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=4))

        # Initialize room data
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

        # Update the rooms dictionary
        rooms[room_code] = room_data

        # Ask the admin for the number of players
        bot.send_message(user_id, "How many players will there be?")
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
                bot.send_message(user_id, "How many additional words will you provide?")
                bot.register_next_step_handler_by_chat_id(user_id,
                                                          lambda m: create_room(user_id, 'num_words', room_code,
                                                                                room_data, m))
            else:
                # Create a JSON file for the room
                room_filename = f'rooms/{room_code}.json'
                with open(room_filename, 'w') as room_file:
                    json.dump(room_data, room_file)

                # Send a message to the admin indicating the room is created
                bot.send_message(user_id, f"Your room has been created! Room code: {room_code}")

                # Introduce a delay of 3 seconds before calling ask_a_word for the admin
                time.sleep(3)
                # Call ask_a_word for the admin after the room is created
                ask_a_word(user_id, room_code, is_admin=True)
        except ValueError:
            bot.send_message(user_id, "Please enter a valid number.")
            create_room(user_id, input_type, room_code, room_data)

# ... (remaining code)



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

        # Introduce a delay (adjust as needed) before calling ask_a_word for the player
        time.sleep(3)

        # Call ask_a_word for the player after joining the room
        ask_a_word(user_id, room_code, is_admin=False)
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


def ask_a_word(user_id, room_code, is_admin=False):
    if is_admin:
        bot.send_message(user_id, "As the admin, please type a word:")
    else:
        bot.send_message(user_id, "Please type a word:")

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

        with open(room_filename, 'w') as room_file:
            json.dump(room_data, room_file)

        confirmation_message = f"The word {'admin_word' if is_admin else 'you'} added: {word}"
        bot.send_message(user_id, confirmation_message)
    else:
        bot.send_message(user_id, "Room not found. Please check the code and try again.")


# Add a function to handle the '/get_words' command
@bot.message_handler(commands=['get_words'])
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

            bot.send_message(user_id, f"Words in the room {room_code}:\n{words_message}")
        else:
            bot.send_message(user_id, "Room not found. Please check the code and try again.")
    else:
        bot.send_message(user_id, "You are not in any room. Please create or join a room first.")


# Function to get the room code associated with a user
def get_user_room_code(user_id):
    print(f"DEBUG - Rooms: {rooms}")
    for room_code, room_data in rooms.items():
        print(
            f"DEBUG - Checking Room: {room_code}, Admin: {room_data['admin']['user_id']}, Players: {room_data['players']}")
        if user_id == room_data['admin']['user_id'] or any(
                player['user_id'] == user_id for player in room_data['players']):
            return room_code
    return None



# Function to get the room code associated with a user
def get_user_room_code(user_id):
    for room_code, room_data in rooms.items():
        if user_id == room_data['admin']['user_id'] or any(
                player['user_id'] == user_id for player in room_data['players']):
            return room_code
    return None

# Ensure the while loop is within the try-except block
while True:
    try:
        bot.polling()
    except ConnectionError as e:
        print(f"Connection error: {e}. Retrying in 10 seconds...")
        time.sleep(10)
