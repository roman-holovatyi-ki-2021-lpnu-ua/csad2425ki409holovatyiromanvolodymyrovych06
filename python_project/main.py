import serial
import time
import threading
import os

CONFIG_FILE = 'config/game_config.ini'


def setup_serial_port():
    try:
        port = input("Enter the serial port (e.g., /dev/ttyUSB0 or COM3): ")
        return serial.Serial(port, 9600, timeout=1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        exit(1)


def send_message(message, ser):
    try:
        ser.write((message + '\n').encode())
    except serial.SerialException as e:
        print(f"Error sending message: {e}")


def receive_message(ser):
    try:
        received = ser.readline().decode('utf-8', errors='ignore').strip()
        if received:
            print(received)
        return received
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None


def receive_multiple_messages(ser, count):
    messages = []
    for _ in range(count):
        message = receive_message(ser)
        if message:
            messages.append(message)
    return messages


def user_input_thread(ser):
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
    global can_input
    global last_received_time
    while not exit_program:
        received = receive_message(ser)
        if received:
            last_received_time = time.time()
            if not can_input:
                can_input = True


def save_game_config(message):
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
                        config[key.strip()] = value.strip()  # Зберігаємо ключ-значення

            # Завантажуємо значення з конфігурації (якщо є)
            game_mode = int(config.get("gameMode", 0))  # За замовчуванням 0
            player_choices = [
                config.get("playerChoices1", "Rock"),  # За замовчуванням "Rock"
                config.get("playerChoices2", "Paper"),  # За замовчуванням "Paper"
                config.get("playerChoices3", "Scissors")  # За замовчуванням "Scissors"
            ]

            print(f"Game Mode: {game_mode}")
            print(f"Player Choices: {player_choices}")

            # Формуємо повідомлення в INI форматі (якщо потрібно передати через серіалізацію)
            ini_message = f"gameMode={game_mode} "
            ini_message += f"playerChoices1={player_choices[0]} "
            ini_message += f"playerChoices2={player_choices[1]} "
            ini_message += f"playerChoices3={player_choices[2]} "

            print(ini_message)

            send_message(ini_message, ser)  # Відправка повідомлення через серіал
        else:
            print("Configuration file not found. Please provide a valid path.")
    except Exception as e:
        print(f"Error loading configuration: {e}")


if __name__ == "__main__":
    ser = setup_serial_port()
    can_input = True
    exit_program = False
    last_received_time = time.time()

    threading.Thread(target=monitor_incoming_messages, args=(ser,), daemon=True).start()
    threading.Thread(target=user_input_thread, args=(ser,), daemon=True).start()

    try:
        while not exit_program:
            if time.time() - last_received_time >= 1 and can_input:
                pass
            else:
                time.sleep(0.1)
    except KeyboardInterrupt:
        print("Exit!")
    finally:
        if ser.is_open:
            print("Closing serial port...")
            ser.close()
