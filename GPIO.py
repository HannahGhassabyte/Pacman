import RPi.GPIO as GPIO
from RPLCD.i2c import CharLCD
import time
import config

cols = 16
i2c_expander = 'PCF8574'
address = 0x27


def startLCD():
    # Initialise the LCD
    lcd = CharLCD (i2c_expander, address)
    lcd.cursor_pos = (0, 5)
    lcd.write_string ("PACMAN")


def updateLCD():  # should be within main game loop
    lcd = CharLCD (i2c_expander, address)
    padding = ' ' * cols
    string = "BEAT THE HIGH SCORE " + str (config.g_highscore)
    string_padded = padding + string + padding
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


def isButtonPressed():
    if (isUpPressed () or isDownPressed () or isRightPressed () or isLeftPressed ()
            or isRedPressed () or isLeftPressed ()):
        return True
    return False


def isUpPressed():
    if GPIO.input (21):
        GPIO.output (20, GPIO.HIGH)
        return True
    else:
        GPIO.output (20, GPIO.LOW)
        return False


def isDownPressed():
    if GPIO.input (26):
        GPIO.output (19, GPIO.HIGH)
        return True
    else:
        GPIO.output (19, GPIO.LOW)
        return False


def isRightPressed():
    if GPIO.input (16):
        GPIO.output (13, GPIO.HIGH)
        return True
    else:
        GPIO.output (13, GPIO.LOW)
        return False


def isLeftPressed():
    if GPIO.input (6):
        GPIO.output (12, GPIO.HIGH)
        return True
    else:
        GPIO.output (12, GPIO.LOW)
        return True


def isRedPressed():
    if GPIO.input (9):
        GPIO.output (25, GPIO.HIGH)
        return True
    else:
        GPIO.output (25, GPIO.LOW)
        return False


def isGreenPressed():
    if GPIO.input (5):
        GPIO.output (11, GPIO.HIGH)
    else:
        GPIO.output (11, GPIO.LOW)


def buttonWaitingPattern(count):
    if count == 0:
        GPIO.output(25, GPIO.HIGH)
        GPIO.output (12, GPIO.HIGH)
    elif count == 1:
        GPIO.output (12, GPIO.LOW)
        GPIO.output (20, GPIO.HIGH)
    elif count == 2:
        GPIO.output (20, GPIO.LOW)
        GPIO.output (13, GPIO.HIGH)
    elif count == 3:
        GPIO.output (13, GPIO.LOW)
        GPIO.output (19, GPIO.HIGH)
    elif count == 4:
        GPIO.output (19, GPIO.LOW)
        GPIO.output (12, GPIO.HIGH)
    elif count == 5:
        GPIO.output (12, GPIO.LOW)
        GPIO.output (25, GPIO.HIGH)
        count = 0
    count += 1
    return count
