import json
import random
from datetime import datetime
from paho.mqtt import client as mqtt_client
import pandas as pd
import os

# Configurazione del broker MQTT e del topic
broker = 'test.mosquitto.org'
port = 1883
topic = "beaconData"
client_id = f'subscribe-{random.randint(0, 100)}'
Qos = 0
keep_alive = 20

# Dizionario per memorizzare i dati ricevuti
mac_rssi_data = {}

# Mappa delle posizioni con le relative coordinate x, y
# Parametri iniziali
start_x = -0.6
start_y = 0.83
incremento_x = 0.10
incremento_y = 0.10
posizioni_per_gruppo = 20

# Mappa delle posizioni
position_map = {}

# Costruzione della mappa delle posizioni fino a 580
try:
    for i in range(1, 581):  # fino alla posizione 551 inclusa
        gruppo = (i - 1) // posizioni_per_gruppo
        x = start_x + gruppo * incremento_x

        if i <= posizioni_per_gruppo:
            y = start_y + (i - 1) * incremento_y
        else:
            y = position_map[i - posizioni_per_gruppo][1]  # Utilizza il valore di y delle prime 20 posizioni

        y = round(y, 2)
        x = round(x, 2)

        position_map[i] = (x, y)

    # Stampa la mappa aggiornata
    # for key, value in position_map.items():
    #   print(f"{key}: {value}")

except Exception as e:
    print(f"Errore durante la costruzione della mappa delle posizioni: {e}")


# Funzione per connettersi al broker MQTT
def connect_mqtt() -> mqtt_client.Client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connesso al broker MQTT!")
        else:
            print(f"Connessione fallita, codice di ritorno {rc}\n")

    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port, keep_alive)
    return client


# Funzione per sanificare i nomi dei file (sostituendo i caratteri non validi)
def sanitize_filename(filename):
    invalid_chars = ':'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


# Funzione per gestire la sottoscrizione e il ricevimento dei messaggi
def subscribe(client: mqtt_client.Client):
    def on_message(client, userdata, msg):
        payload = msg.payload.decode()

        try:
            payload_json = json.loads(payload)
        except json.JSONDecodeError:
            print("Errore nella decodifica del JSON")
            return

        # Se il payload è una lista, iterare attraverso di essa
        if isinstance(payload_json, list):
            for item in payload_json:
                process_payload(item)
        # Se il payload è un singolo oggetto JSON, processarlo direttamente
        else:
            process_payload(payload_json)

    client.subscribe(topic, Qos)
    client.on_message = on_message


# Funzione per processare ciascun oggetto JSON nel payload
def process_payload(payload_json):
    mac_address = payload_json.get("macAddress")
    rssi = payload_json.get("RSSI")
    data_to_send = payload_json.get("timestamp")
    posizione = payload_json.get("Posizione")

    if mac_address and rssi and data_to_send and posizione:
        timestamp = datetime.now().isoformat()
        print(f"Ricevuto `{json.dumps(payload_json)}` al tempo '{timestamp}'")

        if mac_address not in mac_rssi_data:
            mac_rssi_data[mac_address] = {}

        if posizione not in mac_rssi_data[mac_address]:
            mac_rssi_data[mac_address][posizione] = []

        mac_rssi_data[mac_address][posizione].append({
            "Posizione": posizione,
            "mac": mac_address,
            "RSSI": rssi,
            "dataToSend": data_to_send
        })

        # Aggiorna il CSV per questo mac_address e posizione
        update_rssi_csv(mac_address, timestamp, posizione, rssi)

        # Ottieni le coordinate x, y dalla mappa delle posizioni
        x, y = position_map.get(posizione, (None, None))
        if x is not None and y is not None:
            # Aggiorna il DataFrame e salva in Excel
            update_excel(posizione, x, y)
        else:
            print(f"Posizione {posizione} non trovata nella mappa delle posizioni")
    else:
        print("Il payload non contiene tutti i campi necessari (mac, rssi, dataToSend, Posizione)")


# Funzione per aggiornare il CSV per un mac_address e posizione
def update_rssi_csv(mac_address, timestamp, posizione, rssi):
    sanitized_mac_address = sanitize_filename(mac_address)  # Sanifica il nome del file
    filename = f'{sanitized_mac_address}_pos_{posizione}_rssi_data.csv'
    new_row = {'timestamp': timestamp, 'macAddress': mac_address, 'Posizione': posizione, 'RSSI': rssi}

    # Se il file esiste, appendi la nuova riga; altrimenti, crealo
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        df = pd.DataFrame([new_row])

    df.to_csv(filename, index=False)


# Funzione per aggiornare il DataFrame e salvare i dati in un file Excel
def update_excel(position, x, y):
    filename = 'beacon_data1.xlsx'
    if os.path.exists(filename):
        df = pd.read_excel(filename)
    else:
        df = pd.DataFrame(columns=['Position', 'x', 'y'])

    # Trova il punto corrente o crea un nuovo punto
    point_row = df[(df['x'] == x) & (df['y'] == y)]
    if point_row.empty:
        point = df.shape[0] + 1
        new_row = {'Position': position, 'x': x, 'y': y}
        # Escludi le voci rilevanti prima della concatenazione
        new_row = {k: v for k, v in new_row.items() if v is not None}
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    else:
        point = point_row.index[0] + 1

    # Calcola il valore medio di RSSI per questa posizione e aggiorna il DataFrame
    for mac_address, pos_data in mac_rssi_data.items():
        if position in pos_data:
            rssi_values = [entry['RSSI'] for entry in pos_data[position]]
            mean_rssi = sum(rssi_values) / len(rssi_values)
            # Converti il valore medio di RSSI in intero
            mean_rssi = int(mean_rssi)
            df.loc[point - 1, mac_address] = mean_rssi

    # Salva il DataFrame aggiornato nel file Excel
    try:
        df.to_excel(filename, index=False)
    except PermissionError:
        print(
            f"Errore di permessi: impossibile scrivere il file '{filename}'. Assicurati che il file non sia aperto in un altro programma.")


# Funzione principale per eseguire il client MQTT
def run():
    client = connect_mqtt()
    subscribe(client)
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        print("Interruzione manuale del programma")


if __name__ == '__main__':
    run()
