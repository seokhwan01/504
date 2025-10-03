import paho.mqtt.client as mqtt
from RPLCD.i2c import CharLCD
import RPi.GPIO as GPIO
import time, json
from config import Config

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

dir_map = {"북": "N", "남": "S", "동": "E", "서": "W",
           "북동": "NE", "남동": "SE", "남서": "SW", "북서": "NW"}
turn_map = {"직진": "Straight", "좌회전": "Left", "우회전": "Right", "유턴": "U-turn"}

# ----------------------------
# 가운데 정렬 함수
# ----------------------------
def center_text(text, width=16):
    if len(text) > width:
        text = text[:width]
    padding = (width - len(text)) // 2
    return ' ' * padding + text + ' ' * (width - len(text) - padding)

# ----------------------------
# 초기 신호등 상태
# ----------------------------
def set_initial_state():
    set_light(traffic1, "r")
    set_light(traffic2, "g")
    print("초기 상태: 신호등1 빨강 / 신호등2 초록")

set_initial_state()

# ----------------------------
# 상태 전환 함수
# ----------------------------
def emergency_mode(in_dir="", out_dir="", turn=""):
    """응급차 진입시 상태 변경"""
    lcd.clear()
    lcd.cursor_pos = (0, 0)
    lcd.write_string(center_text("!!EMERGENCY!!"))
    if in_dir and out_dir:
        direction_text = f"{in_dir} to {out_dir}"
    else:
        direction_text = "UNKNOWN"
    if turn:
        direction_text += f" {turn}"

    lcd.cursor_pos = (1, 0)
    lcd.write_string(center_text(direction_text))
    print(f"LCD: EMERGENCY {direction_text}")

    # 신호등 전환 (Traffic1 초록, Traffic2 빨강)
    set_light(traffic2, "y")
    print("Traffic 2: Green → Yellow (1 sec)")
    time.sleep(1)
    set_light(traffic2, "r")
    print("Traffic 2: Red")
    set_light(traffic1, "g")
    print("Changed: Traffic 1 Green / Traffic 2 Red")

def clear_mode():
    """응급차 통과 후 원래 상태 복귀"""
    try:
        time.sleep(0.2)   # 약간의 대기
        lcd.clear()
        lcd.write_string(center_text("CLEAR"))
        print("LCD: CLEAR (복귀)")
    except Exception as e:
        print("⚠️ LCD Clear Error:", e)

    set_initial_state()
    

# ----------------------------
# MQTT 콜백
# ----------------------------
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe("ambulance/web/crossroad/1552")

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())

        event = data.get("event")      # approach / arrived / passed
        turn = data.get("turn")
        in_dir = data.get("in_dir")
        out_dir = data.get("out_dir")
        explain = data.get("explain")

        # 영어 변환
        in_dir_en  = dir_map.get(in_dir, in_dir)
        out_dir_en = dir_map.get(out_dir, out_dir)
        turn_en    = turn_map.get(turn, turn)

        print(f"[MQTT] event={event}, turn={turn_en}, explain={explain}")

        if event == "approach":
            emergency_mode(in_dir_en, out_dir_en, turn_en)
        elif event == "passed":
            clear_mode()

    except Exception as e:
        print("메시지 처리 오류:", e)


# ----------------------------
# MQTT 클라이언트 설정
# ----------------------------
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(Config.MQTT_BROKER, Config.MQTT_PORT, 60)  # 필요 시 브로커 IP 수정

# ----------------------------
# 메인 루프
# ----------------------------
try:
    client.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    lcd.clear()
    GPIO.cleanup()
