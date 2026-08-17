import RPi.GPIO as GPIO
import time

IN1 = 17
IN2 = 27
IN3 = 22
IN4 = 23

PINS = [IN1, IN2, IN3, IN4]

GPIO.setmode(GPIO.BCM)

for pin in PINS:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# 8-step sequence
sequence = [
    [1, 0, 0, 0],
    [1, 1, 0, 0],
    [0, 1, 0, 0],
    [0, 1, 1, 0],
    [0, 0, 1, 0],
    [0, 0, 1, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1]
]

def move(steps, direction):
    if direction == 1:
        seq = sequence
    else:
        seq = sequence[::-1]

    for _ in range(steps):
        for step in seq:
            for pin, value in zip(PINS, step):
                GPIO.output(pin, value)

            time.sleep(0.003)

try:
    print("=== NEMA 17 TEST ===")
    print("1 = move clockwise")
    print("2 = move counter-clockwise")
    print("q = quit")

    while True:
        command = input("> ")

        if command == "1":
            print("Moving...")
            move(50, 1)

        elif command == "2":
            print("Moving backwards...")
            move(50, -1)

        elif command.lower() == "q":
            break

finally:
    for pin in PINS:
        GPIO.output(pin, GPIO.LOW)

    GPIO.cleanup()
