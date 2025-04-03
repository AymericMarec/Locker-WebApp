# Installation: pip install paho-mqtt
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connecté au broker MQTT avec code:", rc)
    client.subscribe("mon/topic")

def on_message(client, userdata, msg):
    print(f"Message reçu sur {msg.topic}: {msg.payload.decode()}")

client = mqtt.Client(protocol=mqtt.MQTTv5)
client.on_connect = on_connect
client.on_message = on_message

client.connect("localhost", 1883, 60)

client.publish("mon/topic", "Hello depuis Python")

client.loop_forever()