from flask import jsonify, request, session, redirect, url_for, render_template
from app import app, available_macs
from models.badge import Badge, Locker
from extensions import db
from func.mqtt_service import * 
from func.mqtt_service import get_last_scan as mqtt_get_last_scan

mqtt_client = init_mqtt_client()

@app.route('/badges')
def list_badges():
    if 'paired_mac' not in session:
        return redirect(url_for('pairing'))
    
    badges = Badge.query.all()
    return render_template('badges.html', badges=badges)

@app.route('/badges/add', methods=['POST'])
def add_badge():
    if 'paired_mac' not in session:
        return jsonify({"success": False, "error": "Non appairé"}), 401
    
    try:
        data = request.json
        if 'start_scan' in data:
            set_adding_badge_mode(data['start_scan'])
            return jsonify({
                "success": True, 
                "message": "Mode scan " + ("activé" if data['start_scan'] else "désactivé")
            })
        
        uid = data.get('uid')
        name = data.get('name')
        is_authorized = data.get('is_authorized', True)
        
        if not uid:
            return jsonify({"success": False, "error": "UID requis"}), 400
            
        badge = Badge(uid=uid, name=name, is_authorized=is_authorized)
        db.session.add(badge)
        db.session.commit()
        
        return jsonify({"success": True, "message": "Badge ajouté avec succès"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/badges/<int:badge_id>/toggle', methods=['POST'])
def toggle_badge(badge_id):
    if 'paired_mac' not in session:
        return jsonify({"success": False, "error": "Non appairé"}), 401
    
    try:
        badge = Badge.query.get_or_404(badge_id)
        badge.is_authorized = not badge.is_authorized
        db.session.commit()
        return jsonify({"success": True, "is_authorized": badge.is_authorized})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/badges/<int:badge_id>/delete', methods=['POST'])
def delete_badge(badge_id):
    if 'paired_mac' not in session:
        return jsonify({"success": False, "error": "Non appairé"}), 401
    
    try:
        badge = Badge.query.get_or_404(badge_id)
        db.session.delete(badge)
        db.session.commit()
        return jsonify({"success": True, "message": "Badge supprimé avec succès"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/last_scan')
def get_last_scan():
    if 'paired_mac' not in session:
        return jsonify({"error": "Non appairé"}), 401
    
    last_scan = mqtt_get_last_scan()
    return jsonify({"uid": last_scan})

@app.route('/publish', methods=['POST'])
def publish_message():
    if 'paired_mac' not in session:
        return jsonify({"error": "Non appairé"}), 401
    
    try:
        data = request.json
        message = data.get('message')
        topic = data.get('topic', MQTT_TOPIC_SCAN)
        
        if not message:
            return jsonify({"error": "Message requis"}), 400
            
        mqtt_client.publish(topic, message)
        return jsonify({"success": True, "message": "Message publié avec succès"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/door/close', methods=['POST'])
def close_door():
    if 'paired_mac' not in session:
        return jsonify({"error": "Non appairé"}), 401
    
    try:
        mac_address = session.get('paired_mac')
        if not mac_address:
            return jsonify({"error": "Aucune adresse MAC disponible"}), 400
            
        response_topic = f"{MQTT_TOPIC_RESPONSE}/{mac_address}"
        mqtt_client.publish(response_topic, MQTT_MSG_CLOSE, qos=1)
        return jsonify({"success": True, "message": "Commande de fermeture envoyée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/door/open', methods=['POST'])
def open_door():
    if 'paired_mac' not in session:
        return jsonify({"error": "Non appairé"}), 401
    
    try:
        mac_address = session.get('paired_mac')
        if not mac_address:
            return jsonify({"error": "Aucune adresse MAC disponible"}), 400
            
        response_topic = f"{MQTT_TOPIC_RESPONSE}/{mac_address}"
        mqtt_client.publish(response_topic, MQTT_MSG_ALLOWED, qos=1)
        return jsonify({"success": True, "message": "Commande d'ouverture envoyée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/lockers', methods=['GET'])
def get_lockers():
    try:
        # Récupérer les lockers de la base de données
        db_lockers = Locker.query.all()
        db_macs = {locker.mac_address for locker in db_lockers}
        
        # Combiner avec les MACs détectées
        all_macs = list(db_macs.union(available_macs))
        
        return jsonify({
            'success': True,
            'lockers': all_macs
        })
    except Exception as e:
        print(f"Erreur lors de la récupération des lockers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500 