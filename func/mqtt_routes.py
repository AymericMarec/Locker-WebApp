from flask import jsonify, request, session
from app import app
from services.mqtt_service import mqtt_client, last_scan

@app.route('/publish', methods=['POST'])
def publish_message():
    if not session.get('logged_in'):
        return jsonify({"success": False, "error": "Non authentifié"}), 401
        
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

@app.route('/last_scan')
def get_last_scan():
    if not session.get('logged_in'):
        return jsonify({"error": "Non authentifié"}), 401
    return jsonify({"uid": last_scan}) 