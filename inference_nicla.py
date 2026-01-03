import sensor, time, ml, gc
from machine import LED

# ----------------------------
# Camera setup (must match training)
# ----------------------------
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QQVGA)      # must be >= 96x96
sensor.set_windowing((96, 96))          # EXACT training input
sensor.skip_frames(time=2000)

gc.collect()

# ----------------------------
# Load TFLite model (FP16)
# ----------------------------
net = ml.Model("float16.tflite", load_to_fb=True)

# Label order MUST match training
# clear = 0, obstacle = 1
labels = ["Clear", "Obstacle"]

led = LED("LED_BLUE")
clock = time.clock()

print("Model loaded. Starting inference...")

# ----------------------------
# Inference loop
# ----------------------------
while True:
    clock.tick()

    img = sensor.snapshot()

    # Run inference
    out = net.predict([img])[0][0]   # sigmoid output
    pred = 1 if out > 0.5 else 0

    print(labels[pred], "confidence:", out, "FPS:", clock.fps())

    # LED ON if obstacle
    if pred == 1:
        led.on()
    else:
        led.off()
