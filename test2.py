
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO.setwarnings(False)
#white button 1
GPIO.setup(20, GPIO.OUT)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#white button 2
GPIO.setup(19, GPIO.OUT)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#white button 3
GPIO.setup(13, GPIO.OUT)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#white button 4
GPIO.setup(12, GPIO.OUT)
GPIO.setup(6, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#green button
GPIO.setup(11, GPIO.OUT)
GPIO.setup(5, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#red button
GPIO.setup(25, GPIO.OUT)
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

while  True:
    #WhiteButton1
    if GPIO.input(21):
        GPIO.output(20, GPIO.HIGH)
    else:
        GPIO.output(20, GPIO.LOW)
    #WhiteButton2
    if GPIO.input(26):
        GPIO.output(19, GPIO.HIGH)
    else:
        GPIO.output(19, GPIO.LOW)
    #WhiteButton3
    if GPIO.input(16):
        GPIO.output(13, GPIO.HIGH)
    else:
        GPIO.output(13, GPIO.LOW)
    #WhiteButton4
    if GPIO.input(6):
        GPIO.output(12, GPIO.HIGH)
    else:
        GPIO.output(12, GPIO.LOW)
    #GreenButton
    if GPIO.input(5):
        GPIO.output(11, GPIO.HIGH)
    else:
        GPIO.output(11, GPIO.LOW)
    #RedButton 
    if GPIO.input(9):
        GPIO.output(25, GPIO.HIGH)
    else:
        GPIO.output(25, GPIO.LOW)
    
    