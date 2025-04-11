import paho.mqtt.client as mqtt
import time

# Configuration MQTT
MQTT_BROKER = "localhost"  # Adresse du broker MQTT
MQTT_PORT = 1883  # Port MQTT par défaut
FIXED_MAC = "00:11:22:33:44:55"  # Adresse MAC fixe

def on_connect(client, userdata, flags, rc):
    print("Connecté au broker MQTT avec le code:", rc)

def main():
    # Création du client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    
    # Connexion au broker
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()
    
    # Envoi du message initial sur le topic 'pair'
    client.publish("pair", FIXED_MAC)
    print(f"Message envoyé sur le topic 'pair': {FIXED_MAC}")
    
    while True:
        print("\nQue souhaitez-vous faire ?")
        print("1. Envoyer un message sur le topic 'scan'")
        print("2. Envoyer un message sur le topic 'door'")
        print("3. Quitter")
        
        choice = input("Votre choix (1-3): ")
        
        if choice == "1":
            uid = input("Entrez l'UID (2 caractères): ")
            message = f"{FIXED_MAC}|{uid}"
            client.publish("scan", message)
            print(f"Message envoyé sur le topic 'scan': {message}")
            
        elif choice == "2":
            client.publish("door", "close")
            print("Message 'close' envoyé sur le topic 'door'")
            
        elif choice == "3":
            break
            
        else:
            print("Choix invalide. Veuillez réessayer.")
        
        time.sleep(1)
    
    client.loop_stop()
    client.disconnect()

if __name__ == "__main__":
    main() 