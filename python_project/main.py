import serial
import time
import threading
import os

CONFIG_FILE = 'config/game_config.ini'


def setup_serial_port():
    """!
    @brief Sets up the serial port for communication.
    @details Prompts the user to input the serial port name and initializes a serial connection.
    @return A configured serial.Serial object.
    """
    try:
        port = input("Enter the serial port (e.g., /dev/ttyUSB0 or COM3): ")
        return serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        exit(1)


def send_message(message, ser):
    """!
    @brief Sends a message over the serial connection.
    @param message The message to send.
    @param ser The serial connection object.
    @return None
    """
    try:
        ser.write((message + '\n').encode())
    except serial.SerialException as e:
        print(f"Error sending message: {e}")


def receive_message(ser):
    """!
    @brief Receives a message from the serial connection.
    @param ser The serial connection object.
    @return The received message as a string, or None if there was an error.
    """
    try:
        received = ser.readline().decode('utf-8', errors='ignore').strip()
        if received:
            print(received)
        return received
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None


def receive_multiple_messages(ser, count):
    """!
    @brief Receives multiple messages from the serial connection.
    @param ser The serial connection object.
    @param count The number of messages to receive.
    @return A list of received messages.
    """
    messages = []
    for _ in range(count):
        message = receive_message(ser)
        if message:
            messages.append(message)
    return messages


def user_input_thread(ser):
    """!
    @brief A thread function that listens for user input and sends it over the serial connection.
    @param ser The serial connection object.
    """
    global can_input
    while True:
        if can_input:
            user_message = input()
            if user_message.lower() == 'exit':
                print("Exiting...")
                global exit_program
                exit_program = True
                break
            elif user_message.lower().startswith('save'):
                save_game_config(user_message)
            elif user_message.lower().startswith('load'):
                file_path = input("Enter the path to the configuration file: ")
                load_game_config(file_path, ser)
            send_message(user_message, ser)
            can_input = False


def monitor_incoming_messages(ser):
    """!
    @brief Monitors incoming messages from the serial connection.
    @param ser The serial connection object.
    """
    global can_input
    global last_received_time
    while not exit_program:
        received = receive_message(ser)
        if received:
            last_received_time = time.time()
            if not can_input:
                can_input = True


def save_game_config(message):
    """!
    @brief Saves the current game configuration to a file.
    @param message The message from which the configuration is extracted.
    @return None
    """
    config = {
        "gameMode": 0,
        "playerChoices1": "Rock",
        "playerChoices2": "Paper",
        "playerChoices3": "Scissors"
    }

    try:
        params = message.split()
        if len(params) == 2 and params[1].isdigit():
            config["gameMode"] = int(params[1])

        with open(CONFIG_FILE, 'w') as f:
            f.write(f"gameMode={config['gameMode']}\n")
            f.write(f"playerChoices1={config['playerChoices1']}\n")
            f.write(f"playerChoices2={config['playerChoices2']}\n")
            f.write(f"playerChoices3={config['playerChoices3']}\n")

        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def load_game_config(file_path, ser):
    """!
    @brief Loads a game configuration from a file.
    @param file_path The path to the configuration file.
    @param ser The serial connection object.
    @return None
    """
    try:
        if os.path.exists(file_path):
            config = {}
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(";") or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()  # Save key-value pair

            # Load configuration values (if present)
            game_mode = int(config.get("gameMode", 0))  # Default to 0
            player_choices = [
                config.get("playerChoices1", "Rock"),  # Default to "Rock"
                config.get("playerChoices2", "Paper"),  # Default to "Paper"
                config.get("playerChoices3", "Scissors")  # Default to "Scissors"
            ]

            print(f"Game Mode: {game_mode}")
            print(f"Player Choices: {player_choices}")

            # Formulate INI message (if needed to send over serial)
            ini_message = f"gameMode={game_mode} "
            ini_message += f"playerChoices1={player_choices[0]} "
            ini_message += f"playerChoices2={player_choices[1]} "
            ini_message += f"playerChoices3={player_choices[2]} "

            print(ini_message)

            send_message(ini_message, ser)  # Send message over serial
        else:
            print("Configuration file not found. Please provide a valid path.")
    except Exception as e:
        print(f"Error loading configuration: {e}")
