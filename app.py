from flask import Flask, request, jsonify, send_from_directory
import paho.mqtt.client as mqtt

app = Flask(__name__)

mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
mqtt_client.connect("localhost", 1883, 60)
mqtt_client.loop_start()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/publish', methods=['POST'])
def publish_message():
    try:
        data = request.json
        topic = data.get('topic')
        message = data.get('message')
        
        if not topic or not message:
            return jsonify({"success": False, "error": "Topic et message requis"}), 400
        
        result = mqtt_client.publish(topic, message)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Erreur MQTT: {result.rc}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    print("Serveur démarré! Accédez à http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)