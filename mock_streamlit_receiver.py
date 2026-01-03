import socket
import json
import threading
import time
import streamlit as st
import pandas as pd
import pyttsx3
try:
    import comtypes
    comtypes.CoInitialize()
except ImportError:
    pass

# -----------------------------
# CONFIG
# -----------------------------
UDP_IP = "0.0.0.0"
UDP_PORT = 5007
MAX_POINTS = 100
UI_UPDATE_INTERVAL = 1.5   # seconds
# -----------------------------

# ---------- TTS ----------
tts = pyttsx3.init()
tts.setProperty("rate", 170)

def speak(msg):
    tts.say(msg)
    tts.runAndWait()

# ---------- STREAMLIT UI ----------
st.set_page_config(layout="wide")
st.title("🦾 Third Eye – Assistive Navigation Dashboard")

alert_placeholder = st.empty()
tof_placeholder = st.empty()

col1, col2 = st.columns(2)
acc_chart = col1.empty()
gyro_chart = col2.empty()

# ---------- STATE ----------
@st.cache_resource
def get_shared_state():
    # This dictionary persists across Streamlit re-runs
    state = {
        "buffer": {k: [0.0] * MAX_POINTS for k in ["ax", "ay", "az", "gx", "gy", "gz"]},
        "alert": "NONE",
        "tof": 1500,
        "lock": threading.Lock()
    }

    def udp_listener(shared_state):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((UDP_IP, UDP_PORT))
            print(f"Listening on {UDP_PORT}...")
        except OSError:
            print(f"Port {UDP_PORT} is busy. Assuming background thread is already running.")
            return

        while True:
            try:
                data, _ = sock.recvfrom(2048)
                pkt = json.loads(data.decode())

                with shared_state["lock"]:
                    shared_state["alert"] = pkt["alert"]
                    shared_state["tof"] = pkt["tof_mm"]
                    imu = pkt["imu"]
                    for k in shared_state["buffer"]:
                        shared_state["buffer"][k].append(imu[k])
                        if len(shared_state["buffer"][k]) > MAX_POINTS:
                            shared_state["buffer"][k].pop(0)
            except Exception as e:
                print(f"Error: {e}")

    # Start the thread only once
    t = threading.Thread(target=udp_listener, args=(state,), daemon=True)
    t.start()
    return state

shared_state = get_shared_state()

display_label = "Safe to Walk"
last_spoken_label = ""
last_ui_update = 0

# ---------- ALERT DECISION ----------
def decide_label(raw_alert, tof_mm):
    # Highest priority first
    if "FALL_DETECTED" in raw_alert:
        return "FALL DETECTED - HELP! FLASHING SOS LIGHTS!"
    if "HORN" in raw_alert:
        return "HORN DETECTED ! Go slowly"
    if "OBSTACLE" in raw_alert or tof_mm < 800:
        return "Obstacle Ahead - STOP! CHANGE DIRECTION!"
    return "Keep Walking Safely"

# ---------- MAIN LOOP ----------
while True:
    now = time.time()

    # Update label every UI_UPDATE_INTERVAL seconds
    if now - last_ui_update >= UI_UPDATE_INTERVAL:
        display_label = decide_label(shared_state["alert"], shared_state["tof"])
        last_ui_update = now

        # Speak only if label changed
        if display_label != last_spoken_label:
            speak(display_label)
            last_spoken_label = display_label

    # UI COLOR
    if display_label == "Keep Walking Safely":
        color = "green"
    elif display_label == "Obstacle Ahead - STOP! CHANGE DIRECTION!":
        color = "orange"
    else:
        color = "red"

    alert_placeholder.markdown(
        f"<h1 style='text-align:center; color:{color};'>{display_label}</h1>",
        unsafe_allow_html=True
    )

    tof_placeholder.markdown(
        f"<h3 style='text-align:center;'>Distance: {shared_state['tof']} mm</h3>",
        unsafe_allow_html=True
    )

    # Charts (unchanged)
    with shared_state["lock"]:
        acc_df = pd.DataFrame({
            "Ax": shared_state["buffer"]["ax"],
            "Ay": shared_state["buffer"]["ay"],
            "Az": shared_state["buffer"]["az"]
        })

        gyro_df = pd.DataFrame({
            "Gx": shared_state["buffer"]["gx"],
            "Gy": shared_state["buffer"]["gy"],
            "Gz": shared_state["buffer"]["gz"]
        })

    acc_chart.line_chart(acc_df)
    gyro_chart.line_chart(gyro_df)

    time.sleep(0.1)
