
from RPLCD.i2c import CharLCD
import time
import config

# constants to initialise the LCD
lcdmode = 'i2c'
cols = 16
rows = 2
i2c_expander = 'PCF8574'
address = 0x27
port = 1


# Initialise the LCD
lcd = CharLCD(i2c_expander, address)
lcd.cursor_pos =(0,5)
lcd.write_string("PACMAN")

while True:
    # Write a string on first line and move to next line
    padding=' '*cols
    string = "BEAT THE HIGH SCORE "+str(config.g_highscore)
    string_padded = padding+string+padding
    for i in range(len(string_padded) - cols + 1):
        lcd.home()
        string_display = string_padded[i:i+cols]
        lcd.cursor_pos=(1,0)
        lcd.write_string(string_display)
        time.sleep(0.2)
