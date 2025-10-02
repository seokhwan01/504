from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
import time

# ----------------------------
# GPIO 설정
# ----------------------------
GPIO.setmode(GPIO.BCM)
traffic1 = {"r": 17, "y": 27, "g": 22}
traffic2 = {"r": 14, "y": 15, "g": 18}
all_pins = list(traffic1.values()) + list(traffic2.values())
for pin in all_pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def set_light(light, color):
    for c, pin in light.items():
        GPIO.output(pin, GPIO.LOW)
    if color in light:
        GPIO.output(light[color], GPIO.HIGH)

# ----------------------------
# I2C LCD 초기화
# ----------------------------
lcd = CharLCD(i2c_expander='PCF8574', address=0x27,
              cols=16, rows=2, auto_linebreaks=False)
lcd.backlight_enabled = True

# LCD 토글 상태 변수
lcd_toggle = False

# ----------------------------
# 가운데 정렬 함수
# ----------------------------
def center_text(text, width=16):
    """문자열을 LCD 폭(width) 기준 가운데 정렬"""
    if len(text) > width:
        text = text[:width]
    padding = (width - len(text)) // 2
    return ' ' * padding + text + ' ' * (width - len(text) - padding)

# ----------------------------
# 초기 신호등 상태
# ----------------------------
set_light(traffic1, "r")
set_light(traffic2, "g")
current_state = "r"
print("초기 상태: 신호등1 빨강 / 신호등2 초록")

dir_map = {"북": "N", "남": "S", "동": "E", "서": "W",
           "북동": "NE", "남동": "SE", "남서": "SW", "북서": "NW"}
turn_map = {"직진": "Straight", "좌회전": "Left", "우회전": "Right", "유턴": "U-turn"}

# ----------------------------
# 메인 루프
# ----------------------------
try:
    while True:
        input("Press any key to change traffic lights: ")

        # LCD 토글
        lcd_toggle = not lcd_toggle
        if lcd_toggle:
            lcd.clear()
            lcd.cursor_pos = (0, 0)
            lcd.write_string(center_text("!!EMERGENCY!!"))  # 1행
            lcd.cursor_pos = (1, 0)
            lcd.write_string(center_text("Control Traffic"))  # 2행
            print("LCD: EMERGENCY / Controlling Traffic (ON)")
        else:
            lcd.clear()
            print("LCD: off (OFF)")

        # 신호등 상태 변경
        if current_state == "r":
            set_light(traffic2, "y")
            print("Traffic 2: Green → Yellow (1 sec)")
            time.sleep(1)
            set_light(traffic2, "r")
            print("Traffic 2: Red")
            set_light(traffic1, "g")
            current_state = "g"
            print("Changed: Traffic 1 Green / Traffic 2 Red")
        else:
            set_light(traffic1, "y")
            print("Traffic 1: Green → Yellow (1 sec)")
            time.sleep(1)
            set_light(traffic1, "r")
            print("Traffic 1: Red")
            set_light(traffic2, "g")
            current_state = "r"
            print("Changed: Traffic 1 Red / Traffic 2 Green")

except KeyboardInterrupt:
    pass
finally:
    lcd.clear()
    GPIO.cleanup()
