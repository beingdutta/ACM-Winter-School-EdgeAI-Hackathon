# THIRD EYE – FINAL NICLA VISION INFERENCE SCRIPT
# Vision + ToF + IMU + UDP

import sensor, time, ml, gc, math, json, socket, network
from machine import LED, Pin, SPI, I2C
from lsm6dsox import LSM6DSOX
import vl53l1x


# -----------------------------
# WIFI CONFIG
# -----------------------------
SSID = "santanu"
KEY  = "12345678"

# ---------------- PORT CONFIG ----------------
UDP_IP = "172.17.200.224"   # <-- CHANGE to laptop/phone IP
UDP_PORT = 5005

# -----------------------------
# CONNECT WIFI
# -----------------------------
red_led = LED("LED_RED")
green_led = LED("LED_GREEN")

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, KEY)

print("Connecting to WiFi...")
timeout = 10
while not wlan.isconnected() and timeout > 0:
    time.sleep_ms(1000)
    timeout -= 1

if not wlan.isconnected():
    print("❌ WiFi connection failed")
    red_led.on()
    while True:
        pass
else:
    print("✅ WiFi Connected:", wlan.ifconfig())
    green_led.on()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# ---------------- CAMERA SETUP ------------------
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)
sensor.set_windowing((96, 96))
sensor.skip_frames(time=2000)
gc.collect()

# ---------------- LOAD MODEL --------------------
net = ml.Model("int8_v1.tflite", load_to_fb=True)
labels = ["Clear", "Obstacle"]

# ---------------- IMU SETUP ---------------------
spi = SPI(5)
cs = Pin("PF6", Pin.OUT_PP, Pin.PULL_UP)
imu = LSM6DSOX(spi, cs)

# Fall detection thresholds
FREE_FALL_TH = 0.4
IMPACT_TH = 1.8
GYRO_TH = 200.0
INACTIVITY_MS = 2000

free_fall = False
free_fall_start = 0
impact_time = 0

fall_active = False
fall_report_time = 0
FALL_HOLD_MS = 5000

# ---------------- TOF SETUP ---------------------
i2c = I2C(2, freq=400000)
tof = vl53l1x.VL53L1X(i2c)

# ---------------- LED ---------------------------
led = LED("LED_BLUE")

# ---------------- UTILS -------------------------
def magnitude(x, y, z):
    return math.sqrt(x*x + y*y + z*z)

clock = time.clock()
last_send = time.ticks_ms()

print("🚀 Third Eye Inference Started")

# ============================================================
# MAIN LOOP
# ============================================================
while True:
    clock.tick()

    # ---------- CAMERA INFERENCE ----------
    img = sensor.snapshot()
    out = net.predict([img])[0][0]
    cnn_pred = 1 if out > 0.5 else 0
    cnn_label = labels[cnn_pred]

    # ---------- TOF ----------
    tof_mm = tof.read()
    if tof_mm == 0:
        tof_mm = 4000

    # ---------- IMU ----------
    ax, ay, az = imu.accel()
    gx, gy, gz = imu.gyro()

    acc_mag = magnitude(ax, ay, az)
    gyro_mag = magnitude(gx, gy, gz)
    now = time.ticks_ms()

    fall_detected = False

    # ---------------- FALL FSM (FIXED) ----------------

    # FREE FALL detection (must last >100 ms)
    if acc_mag < FREE_FALL_TH:
        if not free_fall:
            free_fall = True
            free_fall_start = now
    else:
        # Cancel false free-fall
        if free_fall and time.ticks_diff(now, free_fall_start) < 100:
            free_fall = False

    # IMPACT detection (must follow free-fall)
    if free_fall:
        if acc_mag > IMPACT_TH and time.ticks_diff(now, free_fall_start) > 100:
            impact_time = now
            free_fall = False

    # INACTIVITY after impact → FALL
    if impact_time != 0:
        if time.ticks_diff(now, impact_time) > INACTIVITY_MS:
            fall_active = True
            fall_report_time = now
            impact_time = 0

    # ---------- ALERT LOGIC ----------
    alert = "NONE"

    # FALL overrides everything
    if fall_active:
        if time.ticks_diff(now, fall_report_time) < FALL_HOLD_MS:
            alert = "FALL_DETECTED"
            led.on()
        else:
            fall_active = False
            led.off()

    elif tof_mm < 800 or cnn_label == "Obstacle":
        alert = "OBSTACLE"
        led.on()

    else:
        led.off()

    # ---------- UDP SEND (1–2s rate) ----------
    if time.ticks_diff(now, last_send) > 1200:
        pkt = {
            "imu": {
                "ax": ax, "ay": ay, "az": az,
                "gx": gx, "gy": gy, "gz": gz
            },
            "tof_mm": tof_mm,
            "cnn_label": cnn_label,
            "alert": alert
        }

        sock.sendto(json.dumps(pkt), (UDP_IP, UDP_PORT))
        last_send = now

    print("FPS: %.2f | Label: %s | ToF: %d mm | Alert: %s | Acc: %.2f | Gyro: %.2f" % (
        clock.fps(), cnn_label, tof_mm, alert, acc_mag, gyro_mag
    ))

    time.sleep_ms(50)
