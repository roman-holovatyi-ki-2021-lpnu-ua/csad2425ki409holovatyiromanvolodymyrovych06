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
    @brief Saves the game configuration to a file.
    @param message The configuration message to save.
    @details This function saves the configuration message to a predefined file.
    @exception Will print an error message if saving the configuration fails.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            f.write(message)
        print(f"Configuration saved to {CONFIG_FILE}")
    except Exception as e:
        print(f"Error saving configuration: {e}")


def load_game_config(file_path, ser):
    """!
    @brief Loads the game configuration from a file and sends it over serial.
    @param file_path The path to the configuration file to load.
    @param ser The serial.Serial object for communication.
    @details This function reads the content of the configuration file and sends it over the serial port.
    @exception Will print an error message if the file cannot be loaded.
    """
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                ini_content = f.read()

            print("Loaded INI content:")
            print(ini_content)

            send_message(ini_content, ser)
        else:
            print("Configuration file not found. Please provide a valid path.")
    except Exception as e:
        print(f"Error loading configuration: {e}")


def main():
    """!
    @brief Main function to initialize serial communication and handle threads.
    @details This function sets up the serial communication, starts the threads for monitoring incoming messages and handling user input, and manages the program loop.
    """
    global can_input, exit_program
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

if __name__ == "__main__":
    main()
