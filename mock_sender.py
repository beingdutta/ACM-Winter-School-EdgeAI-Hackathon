import socket
import time
import random
import json

# -----------------------------
# CONFIG
# -----------------------------
# If in laptop/android emulator data needs to be received, then 
# use IP: 127.0.0.1 (this IP is used to receive data on same device
# which is generating the data)

# For Android emulator we need to do port forwarding using:
# C:\Users\aritr\AppData\Local\Android\Sdk\platform-tools\adb emu redir add udp:5005:5005

# Otherwise:
# For the below code to work, the sender, and the receiver 
# should be on the same LAN. Connect all the devices to the 
# same LAN, then check IP of the network in android phone, paste here, 
# check IP of laptop using ipconfig / ifconfig and paste here.

TARGETS = [
    ("192.168.43.216", 5005),  # Android
    ("127.0.0.1", 5007),  # Laptop
]
SEND_INTERVAL = 0.1    # 10 Hz
# -----------------------------

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

print("Mock Nicla Vision sender started")

mode = "normal"
mode_timer = time.time()

def random_imu(scale=0.05):
    return {
        "ax": random.uniform(-scale, scale),
        "ay": random.uniform(-scale, scale),
        "az": 9.8 + random.uniform(-scale, scale),
        "gx": random.uniform(-scale, scale),
        "gy": random.uniform(-scale, scale),
        "gz": random.uniform(-scale, scale),
    }

while True:
    now = time.time()

    # Change scenario every ~5 seconds
    if now - mode_timer > 5:
        mode = random.choice(["normal", "obstacle", "fall"])
        mode_timer = now

    alert = "NONE"
    tof_mm = random.randint(900, 1500)
    imu = random_imu()
    cnn_label = "Clear"

    if mode == "obstacle":
        tof_mm = random.randint(300, 700)
        alert = "OBSTACLE_AHEAD. STOP!"
        cnn_label = "Obstacle"

    elif mode == "fall":
        imu = {
            "ax": random.uniform(-8, 8),
            "ay": random.uniform(-8, 8),
            "az": random.uniform(-8, 8),
            "gx": random.uniform(-10, 10),
            "gy": random.uniform(-10, 10),
            "gz": random.uniform(-10, 10),
        }
        alert = "FALL_DETECTED. GET UP SLOWLY!"

    packet = {
        "timestamp": now,
        "imu": imu,
        "tof_mm": tof_mm,
        "alert": alert,
        "cnn_label": cnn_label
    }

    encoded_packet = json.dumps(packet).encode()
    for ip, port in TARGETS:
        sock.sendto(encoded_packet, (ip, port))
    time.sleep(SEND_INTERVAL)
