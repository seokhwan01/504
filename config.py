import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = "secret_key_for_session"
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "test.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MQTT_BROKER = "localhost" #MQTT 브로커 ip로 변경
    MQTT_PORT = 1883
