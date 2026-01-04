import time, math
from machine import Pin, SPI
from lsm6dsox import LSM6DSOX

FREE_FALL_TH   = 0.4      # g
IMPACT_TH      = 1.8      # g
INACTIVITY_MS  = 2000     # 2 seconds

free_fall = False
impact_time = 0
free_fall_time = 0

def magnitude(x, y, z):
    return math.sqrt(x*x + y*y + z*z)

print("=== Fall Detection Started (REAL TEST MODE) ===")

spi = SPI(5)
cs = Pin("PF6", Pin.OUT_PP, Pin.PULL_UP)
imu = LSM6DSOX(spi, cs)

print("Time | AccMag | Status")

while True:
    ax, ay, az = imu.accel()
    ts = time.ticks_ms()
    acc_mag = magnitude(ax, ay, az)

    status = "NORMAL"

    # -------- STEP 1: FREE FALL --------
    if acc_mag < FREE_FALL_TH:
        if not free_fall:
            free_fall_time = ts
        free_fall = True
        status = "FREE FALL"

    # -------- STEP 2: IMPACT --------
    if free_fall and acc_mag > IMPACT_TH:
        if time.ticks_diff(ts, free_fall_time) > 100:
            impact_time = ts
            free_fall = False
            status = "IMPACT"

    # -------- STEP 3: INACTIVITY --------
    if impact_time != 0:
        if time.ticks_diff(ts, impact_time) > INACTIVITY_MS:
            status = "🚨 FALL DETECTED 🚨"
            impact_time = 0
            time.sleep_ms(3000)

    print("%6d | %5.2f | %s" % (ts, acc_mag, status))

    time.sleep_ms(50)   # 🔥 HIGH SAMPLING RATE