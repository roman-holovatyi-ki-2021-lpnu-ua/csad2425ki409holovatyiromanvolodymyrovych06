import serial
import time

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
        print(f"Sent: {message}")
    except serial.SerialException as e:
        print(f"Error sending message: {e}")

def receive_message(ser):
    try:
        received = ser.readline().decode('utf-8', errors='ignore').strip()
        if received:
            print(f"Received: {received}")
        return received
    except serial.SerialException as e:
        print(f"Error receiving message: {e}")
        return None

if __name__ == "__main__":
    ser = setup_serial_port()
    try:
        while True:
            user_message = input("Message to server: ")
            if user_message.lower() == 'exit':
                print("Exiting...")
                break
            send_message(user_message, ser)
            receive_message(ser)
    except KeyboardInterrupt:
        print("Exit!")
    finally:
        if ser.is_open:
            print("Closing serial port...")
            ser.close()
