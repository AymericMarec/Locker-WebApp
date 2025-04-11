from flask import jsonify, request, session
from app import app
from services.mqtt_service import mqtt_client, last_scan, get_paired_mac

@app.route('/publish', methods=['POST'])
def publish_message():
    if 'paired_mac' not in session:
        return jsonify({"success": False, "error": "Non appairé"}), 401
        
    try:
        data = request.json
        topic = data.get('topic')
        message = data.get('message')
        
        if not topic or not message:
            return jsonify({"success": False, "error": "Topic et message requis"}), 400
        
        # Ajouter l'adresse MAC appairée au message si nécessaire
        if topic == "scan":
            message = f"{get_paired_mac()}|{message}"
        
        result = mqtt_client.publish(topic, message)
        
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Erreur MQTT: {result.rc}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/last_scan')
def get_last_scan():
    if 'paired_mac' not in session:
        return jsonify({"error": "Non appairé"}), 401
    return jsonify({"uid": last_scan}) 