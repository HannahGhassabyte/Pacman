import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time
import config

cols = 16
i2c_expander = 'PCF8574'
address = 0x27

def updateLCD():  # should be within main game loop
    lcd = CharLCD (i2c_expander, address)
    lcd.cursor_pos = (0, 5)
    lcd.write_string ("PACMAN")
    for i in range (len (string_padded) - cols + 1):
        lcd.home ()
        string_display = string_padded[i:i + cols]
        lcd.cursor_pos = (1, 0)
        lcd.write_string (string_display)
        time.sleep (0.2)


def intialization():
    GPIO.setmode (GPIO.BCM)
    GPIO.setwarnings (False)
    # white button 1
    GPIO.setup (20, GPIO.OUT)
    GPIO.setup (21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # white button 2
    GPIO.setup (19, GPIO.OUT)
    GPIO.setup (26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # white button 3
    GPIO.setup (13, GPIO.OUT)
    GPIO.setup (16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # white button 4
    GPIO.setup (12, GPIO.OUT)
    GPIO.setup (6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # green button
    GPIO.setup (11, GPIO.OUT)
    GPIO.setup (5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # red button
    GPIO.setup (25, GPIO.OUT)
    GPIO.setup (9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)



def buttonWaitingPattern(count):
    if count == 0:
        GPIO.output (12, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (12, GPIO.LOW)
    elif count == 1:
        GPIO.output (20, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (20, GPIO.LOW)
    elif count == 2:
        GPIO.output (13, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (13, GPIO.LOW)
    elif count == 3:
        GPIO.output (19, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (19, GPIO.LOW)
    elif count == 4:
        GPIO.output (11, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (11, GPIO.LOW)
    elif count == 5:
        GPIO.output (25, GPIO.HIGH)
        time.sleep (0.5)
        GPIO.output (25, GPIO.LOW)
        count = -1
    count += 1
    return count
