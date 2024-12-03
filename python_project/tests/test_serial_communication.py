import pytest
from unittest.mock import patch, MagicMock, mock_open
from unittest import mock
import serial
import threading
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import main
from main import (
    setup_serial_port,
    send_message,
    receive_message,
    save_game_config,
    load_game_config,
    user_input_thread
)

CONFIG_FILE = "game_config.ini"


@patch('builtins.input', return_value='/dev/ttyUSB0')
@patch('serial.Serial', return_value=MagicMock())
def test_setup_serial_port_success(mock_serial, mock_input):
    """!
    @brief Tests the successful setup of the serial port.
    @details Ensures that the serial port is correctly initialized when valid input is provided.
    @param mock_serial Mock for serial.Serial class.
    @param mock_input Mock for input function.
    """
    ser = setup_serial_port()
    assert ser is not None, "Повернений об'єкт має бути не None"
    mock_serial.assert_called_once_with('/dev/ttyUSB0', 9600, timeout=1)


@patch('builtins.input', return_value='/dev/ttyUSB0')
@patch('serial.Serial', side_effect=serial.SerialException("Port not found"))
@patch('builtins.exit')
def test_setup_serial_port_exception(mock_exit, mock_serial, mock_input):
    """!
    @brief Tests the setup_serial_port function when a SerialException occurs.
    @details Ensures the program exits gracefully with an error message if the serial port cannot be opened.
    @param mock_exit Mock for exit function.
    @param mock_serial Mock for serial.Serial class.
    @param mock_input Mock for input function.
    """
    with patch('builtins.print') as mock_print:
        setup_serial_port()
        mock_print.assert_called_once_with("Error: Port not found")
        mock_exit.assert_called_once_with(1)


def test_send_message_success():
    """!
    @brief Tests successful message sending via serial port.
    @details Ensures that the message is correctly written to the serial port.
    """
    mock_ser = MagicMock(spec=serial.Serial)
    
    send_message("Test message", mock_ser)
    
    mock_ser.write.assert_called_once_with(b'Test message\n')


def test_send_message_exception():
    """!
    @brief Tests send_message function when a SerialException occurs.
    @details Ensures that an error message is printed if writing to the serial port fails.
    """
    mock_ser = MagicMock(spec=serial.Serial)
    
    mock_ser.write.side_effect = serial.SerialException("Write error")
    
    with patch('builtins.print') as mock_print:
        send_message("Test message", mock_ser)
        mock_print.assert_called_with("Error sending message: Write error")


def test_receive_message_success():
    """!
    @brief Tests successful message receiving via serial port.
    @details Ensures that a message is correctly read and decoded from the serial port.
    """
    mock_ser = MagicMock(spec=serial.Serial)
    
    mock_ser.readline.return_value = b'Test message\n'
    
    result = receive_message(mock_ser)
    assert result == 'Test message'
    mock_ser.readline.assert_called_once()


def test_receive_message_exception():
    """!
    @brief Tests receive_message function when a SerialException occurs.
    @details Ensures that None is returned and an error message is printed if reading from the serial port fails.
    """
    mock_ser = MagicMock(spec=serial.Serial)
    
    mock_ser.readline.side_effect = serial.SerialException("Read error")
    
    with patch('builtins.print') as mock_print:
        result = receive_message(mock_ser)
        assert result is None
        mock_print.assert_called_with("Error receiving message: Read error")


def test_exit_program():
    """!
    @brief Tests the exit functionality in the user_input_thread function.
    @details Ensures the program sets the exit flag and prints an exit message when 'exit' is input.
    """
    with patch.dict('main.__dict__', {'can_input': True, 'exit_program': False}):
        with patch('builtins.input', return_value='exit'), patch('builtins.print') as mock_print:
            ser = MagicMock()

            thread = threading.Thread(target=main.user_input_thread, args=(ser,))
            thread.start()

            time.sleep(1)

            assert main.exit_program is True

            mock_print.assert_called_with("Exiting...")

            thread.join(timeout=1)


def test_send_message_called():
    """!
    @brief Tests if send_message is called with the correct parameters.
    @details Ensures that the user_input_thread function invokes the send_message function with the user input and serial object.
    """
    with patch.dict('main.__dict__', {'can_input': True}):
        with patch('builtins.input', return_value='Hello'), patch('builtins.print'), patch('main.send_message') as mock_send_message:
            ser = MagicMock()

            thread = threading.Thread(target=main.user_input_thread, args=(ser,))
            thread.start()

            time.sleep(1)

            mock_send_message.assert_called_with('Hello', ser)

            with patch.dict('main.__dict__', {'can_input': False}):
                thread.join(timeout=1)


def test_load_game_config_called():
    """!
    @brief Tests if load_game_config is called with the correct parameters.
    @details Ensures that the user_input_thread function invokes the load_game_config function when the 'load' command is entered by the user.
    """
    with patch.dict('main.__dict__', {'can_input': True}):
        with patch('builtins.input', side_effect=['load', '/path/to/file']), patch('main.load_game_config') as mock_load_game_config, patch('builtins.print'):
            ser = MagicMock()

            thread = threading.Thread(target=main.user_input_thread, args=(ser,))
            thread.start()

            time.sleep(1)

            mock_load_game_config.assert_called_with('/path/to/file', ser)

            with patch.dict('main.__dict__', {'can_input': False}):
                thread.join(timeout=1)


def test_monitor_incoming_messages_can_input():
    """!
    @brief Tests if monitor_incoming_messages sets can_input to True after receiving a message.
    @details Verifies that the function updates the can_input flag when a message is received from the serial port.
    """
    with patch.dict('main.__dict__', {'can_input': False, 'exit_program': False}):
        with patch('main.receive_message', return_value='Test message'), patch('time.time', return_value=100):
            ser = MagicMock()

            thread = threading.Thread(target=main.monitor_incoming_messages, args=(ser,))
            thread.start()

            time.sleep(1)

            assert main.can_input is True

            main.exit_program = True
            thread.join(timeout=1)


def test_monitor_incoming_messages_last_received_time():
    """!
    @brief Tests if monitor_incoming_messages updates the last_received_time correctly.
    @details Ensures that the function sets last_received_time to the current timestamp after receiving a message.
    """
    with patch.dict('main.__dict__', {'exit_program': False}):
        with patch('main.receive_message', return_value='Test message'), patch('time.time', return_value=100):
            ser = MagicMock()

            thread = threading.Thread(target=main.monitor_incoming_messages, args=(ser,))
            thread.start()

            time.sleep(1)

            assert main.last_received_time == 100

            main.exit_program = True
            thread.join(timeout=1)


def test_monitor_incoming_messages_exit_program():
    """!
    @brief Tests if monitor_incoming_messages exits the thread when exit_program is set to True.
    @details Ensures that the monitoring thread stops running once the exit_program flag is set to True.
    """
    with patch.dict('main.__dict__', {'exit_program': False}):
        with patch('main.receive_message', return_value='Test message'):
            ser = MagicMock()

            thread = threading.Thread(target=main.monitor_incoming_messages, args=(ser,))
            thread.start()

            time.sleep(1)
            main.exit_program = True
            thread.join(timeout=1)

            assert not thread.is_alive()


def test_monitor_incoming_messages_no_message():
    """!
    @brief Tests if monitor_incoming_messages handles the absence of incoming messages.
    @details Verifies that the can_input flag remains False when no messages are received.
    """
    with patch.dict('main.__dict__', {'can_input': False, 'exit_program': False}):
        with patch('main.receive_message', return_value=None):
            ser = MagicMock()

            thread = threading.Thread(target=main.monitor_incoming_messages, args=(ser,))
            thread.start()

            time.sleep(1)

            assert main.can_input is False

            main.exit_program = True
            thread.join(timeout=1)


def test_save_game_config_success():
    """!
    @brief Tests the successful saving of game configuration.
    @details Ensures that the save_game_config function writes the correct message to the specified file.
    """
    with patch("builtins.open", mock_open()) as mock_file:
        message = '{ "game_state": "paused" }'

        main.save_game_config(message)

        mock_file.assert_called_once_with(main.CONFIG_FILE, 'w')

        mock_file().write.assert_called_once_with(message)


def test_save_game_config_error():
    """!
    @brief Tests error handling in save_game_config.
    @details Ensures that an appropriate error message is printed when saving fails.
    """
    with patch("builtins.open", side_effect=Exception("Test error")):
        message = '{ "game_state": "paused" }'

        with patch("builtins.print") as mock_print:
            main.save_game_config(message)

            mock_print.assert_called_once_with("Error saving configuration: Test error")


def test_load_game_config_success():
    """!
    @brief Tests the successful loading of a game configuration file.
    @details Verifies that the configuration is loaded, printed, and sent via the provided serial port.
    """
    mock_file_content = '{"game_state": "paused"}'
    mock_file_path = 'test_config.ini'

    with patch("os.path.exists", return_value=True), patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file, patch("main.send_message") as mock_send_message, patch("builtins.print") as mock_print:
        main.load_game_config(mock_file_path, None)

        mock_file.assert_called_once_with(mock_file_path, 'r')

        mock_send_message.assert_called_once_with(mock_file_content, None)

        mock_print.assert_any_call("Loaded INI content:")
        mock_print.assert_any_call(mock_file_content)


def test_load_game_config_file_not_found():
    """!
    @brief Tests handling of a non-existent configuration file.
    @details Ensures that an appropriate message is printed when the file does not exist.
    """
    mock_file_path = 'non_existent_config.ini'

    with patch("os.path.exists", return_value=False), patch("builtins.print") as mock_print:
        main.load_game_config(mock_file_path, None)

        mock_print.assert_called_once_with("Configuration file not found. Please provide a valid path.")


def test_load_game_config_error():
    """!
    @brief Tests error handling in load_game_config.
    @details Ensures that an appropriate error message is printed when loading fails.
    """
    mock_file_path = 'test_config.ini'

    with patch("os.path.exists", return_value=True), patch("builtins.open", side_effect=Exception("Test error")), patch("builtins.print") as mock_print:
        main.load_game_config(mock_file_path, None)

        mock_print.assert_called_once_with("Error loading configuration: Test error")


@pytest.fixture
def stop_event():
    """!
    @brief Provides a threading.Event for stopping tests cleanly.
    @details This fixture creates and ensures proper cleanup of the stop event used in tests.
    @yield threading.Event object.
    """
    event = threading.Event()
    yield event
    event.set()


@pytest.fixture
def mock_serial_port():
    """!
    @brief Provides a mock serial port fixture for testing.
    @details Simulates an open serial port for use in unit tests.
    @return Mocked serial port object.
    """
    mock_ser = mock.MagicMock()
    mock_ser.is_open = True
    return mock_ser


@pytest.fixture
def mock_monitor_incoming_messages():
    """!
    @brief Provides a mock for monitor_incoming_messages.
    @details Simulates the monitoring of incoming messages.
    @yield Mocked monitor_incoming_messages function.
    """
    with mock.patch("main.monitor_incoming_messages") as mock_func:
        yield mock_func


@pytest.fixture
def mock_user_input_thread():
    """!
    @brief Provides a mock for user_input_thread.
    @details Simulates the user input handling thread.
    @yield Mocked user_input_thread function.
    """
    with mock.patch("main.user_input_thread") as mock_func:
        yield mock_func


def test_main(mock_serial_port, mock_monitor_incoming_messages, mock_user_input_thread, stop_event):
    """!
    @brief Tests the main function setup and behavior.
    @details Verifies initialization, thread management, and serial port closure.
    """
    with mock.patch("main.setup_serial_port", return_value=mock_serial_port) as mock_setup_serial, \
         mock.patch("main.monitor_incoming_messages", wraps=mock_monitor_incoming_messages), \
         mock.patch("main.user_input_thread", wraps=mock_user_input_thread), \
         mock.patch("main.time.time", side_effect=[0, 0.5, 1.5, 2.5]), \
         mock.patch("main.time.sleep", side_effect=lambda x: stop_event.set()):  # Simulate loop termination
        
        # Override global states
        def patched_main():
            main.can_input = True
            main.exit_program = stop_event.is_set()
            main.main()  # Call the actual main function

        main_thread = threading.Thread(target=patched_main)
        main_thread.start()

        # Wait for test to complete
        stop_event.wait(timeout=2)
        main_thread.join(timeout=1)

        # Assertions to verify behavior
        mock_setup_serial.assert_called_once()
        mock_monitor_incoming_messages.assert_called_once_with(mock_serial_port)
        mock_user_input_thread.assert_called_once_with(mock_serial_port)

        assert mock_serial_port.close.called, "Serial port was not closed properly."


@pytest.fixture(autouse=True)
def cleanup_after_tests():
    """!
    @brief Automatically cleanup after tests.
    @details Ensures the global state (e.g., exit_program) is reset after each test.
    """
    yield
    if hasattr(main, "exit_program"):
        main.exit_program = False
    if hasattr(main, "can_input"):
        main.can_input = False