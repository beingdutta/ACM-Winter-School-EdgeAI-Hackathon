# =====================================================
# VL53L1 (U4 VL53L1CBV0FY/1) Distance Measurement
# Arduino Nicla Vision + OpenMV
# Output: OpenMV Terminal only
# =====================================================

import time
from machine import I2C
import vl53l1x

# I2C2 is used internally on Nicla Vision
i2c = I2C(2, freq=400000)

# Initialize VL53L1 using OpenMV driver
tof = vl53l1x.VL53L1X(i2c)

print("========================================")
print(" VL53L1 ToF Distance Measurement (0–4 m) ")
print("========================================")
print("Distance (mm) | Distance (m) | Status")

while True:
    distance_mm = tof.read()   # distance in millimeters

    if distance_mm == 0:
        status = "Out of range / No target"
        dist_m = 0.0
    else:
        dist_m = distance_mm / 1000.0
        if distance_mm < 500:
            status = "⚠️ VERY CLOSE"
        elif distance_mm < 1500:
            status = "⚠️ OBSTACLE AHEAD"
        else:
            status = "CLEAR"

    print("%12d | %10.2f | %s" % (distance_mm, dist_m, status))
    time.sleep_ms(200)
