import paho.mqtt
import paho.mqtt.client as mqttClient
import json
import argparse
import logging
import math
import sys
from pathlib import Path
from positioning import Positioning
import joblib
import requests
import Node

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root))


class RSSIPredictor:
    ready = False
    rssi = {}
    positioning = None

    time_range = 25  # Definisce la finestra temporale in secondi
    last_prediction_timestamp = None  # Timestamp dell'ultima previsione

    def __init__(self, aimodel):
        self.ready = True
        self.scaler = joblib.load('C:/Users/terry/Desktop/blepositioning-main/predictor/aimodels/scaler.pkl')
        self.positioning = Positioning(model_type=aimodel, optimize=False)
        model = joblib.load(f'C:/Users/terry/Desktop/blepositioning-main/predictor/aimodels/{aimodel}_model.pkl')
        self.positioning.model_x = model['model_x']
        self.positioning.model_y = model['model_y']
        self.nh = None
        self.nc = None
        self.cts = 0

    def addrssi(self, rssi, mac, update=True, js=None):

        # Aggiungi un nuovo nodo se necessario
        if self.nh is None:
            self.nh = Node.Node(rssi)
            self.cts = rssi["timestamp"]
            # print(f"Debug - Primo dato ricevuto: timestamp={rssi['timestamp']}, cts={self.cts}, mac={mac},rssi={rssi}")
            return
        elif rssi["timestamp"] - self.cts > 0:
            self.nh = self.nh.nadd(rssi)
            self.cts = math.floor(rssi["timestamp"])
        elif math.floor(self.cts - rssi["timestamp"]) < self.time_range:
            self.nh = self.nh.nadd(rssi)

        # Inizializza variabili di calcolo
        nc = self.nh
        macs = []
        sum = {}
        csum = {}
        media = {}
        #print("START")
        #print(f"cts= {self.cts}")

        # Variabile per tracciare l'ultimo timestamp valido
        last_node_timestamp = 0

        # Itera sui nodi per calcolare media e somma all'interno della finestra temporale
        while nc is not None and not nc.is_last_next():
            node_data = nc.nget()
            tmac = node_data["mac"]
            node_timestamp = node_data["timestamp"]
            windows = node_timestamp

            # Considera i nodi all'interno della finestra temporale
            # print(
            #    f"In finestra Differenza tempo locale e precedente :{math.floor(self.cts - windows)} "
            #   f"con MAC :{node_data["mac"]} ed rssi:{node_data["RSSI"]}"
            #    f"con timestamp ricevuto:{self.cts} ed timestamp_finestra:{windows}")

            # Gestione dei nodi obsoleti (fuori dalla finestra temporale)
            if math.floor(self.cts - windows) > self.time_range:
                if tmac in macs:
                    sum[tmac] -= node_data["RSSI"]
                    csum[tmac] -= 1
                nc = nc.next  # Passa al prossimo nodo senza eliminare il nodo attuale
                continue

            if tmac not in macs:
                # print("Aggiungo nuovo MAC")
                macs.append(tmac)
                sum[tmac] = node_data["RSSI"]
                csum[tmac] = 1
            else:
                sum[tmac] += node_data["RSSI"]
                csum[tmac] += 1

            # Salva l'ultimo timestamp valido (nodo dentro la finestra)
            last_node_timestamp = self.cts
            # print(f"Ultimo valore valido finestra:{last_node_timestamp}")

            # Passa al nodo successivo
            nc = nc.next

        # Calcola la media per ciascun MAC
        for mac in macs:
            if csum[mac] > 0:
                media[mac] = int(sum[mac] / csum[mac])
            #  print(f"Media per MAC {mac}: {media[mac]}")
            else:
                media[mac] = 0

        # Prepara media_list per la funzione predict
        #for mac, value in media.items():
        #print(f"mac: {mac}, value: {value}")

        valid_media = [(mac, media[mac]) for mac in media.keys() if media[mac] != 0]
        # print(f"Media List per MAC {mac}: {valid_media}")

        # Chiama la funzione di predizione con media_list
        next_positions = self.predict(valid_media)

        # Controlla se la differenza tra self.cts e windows è maggiore di 6, e aggiorna windows
        # if math.floor(self.cts - windows) > 6:
        #     windows = self.cts  # aggiorna windows con l'ultimo cts ricevuto
        #     print(f"Windows aggiornato: {windows}")

        # Dopo la predizione, aggiorna windows
        if next_positions is not None and update:
            data = {'id': 1, 'x': next_positions[0], 'y': next_positions[1], 'z': 0}
            url = "http://localhost:5000/api-service/update"
            headers = {'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, data=json.dumps(data))

            self.cts = last_node_timestamp  # Aggiorna solo se la condizione è soddisfatta
            # print(f"Nuovo timestamp della finestra: {self.cts}")

            return data

        return next_positions

    def predict(self, media_list):
        # Definire l'ordine desiderato dei MAC
        mac_order = ['FF:FF:11:15:F5:9A', 'FF:FF:11:15:2D:C4', 'FF:FF:11:10:14:A0']

        # Ordinare media_list in base all'ordine desiderato dei MAC
        ordered_media_list = sorted(media_list,
                                    key=lambda x: mac_order.index(x[0]) if x[0] in mac_order else float('inf'))

        # Stampa o ritorna il risultato
        # print(f"Media finale: {ordered_media_list}")

        # Estrarre i valori medi ordinati
        avg_values = [media_value for mac, media_value in ordered_media_list]

        # Se ci sono almeno 3 valori medi, esegui la previsione
        if len(avg_values) >= 3:
            scaled_values = self.scaler.transform([avg_values])
            position = self.positioning.predict(scaled_values)[0]

            print(f"Posizione prevista: {position}")
            return position

        return None

    def getlastrssi(self, mac):
        if mac in self.rssi:
            return self.rssi[mac][-1]['timestamp']
        else:
            return None


class MqttClient:
    predictor = None

    def __init__(self, predictor):
        self.predictor = predictor

    # Funzione per processare il payload JSON
    def process_payload(self, id, payload_json):
        try:
            mac_address = payload_json.get("mac")
            rssi = payload_json.get("RSSI")
            timestamp = payload_json.get("timestamp")

            if mac_address and rssi is not None:
                # logging.info(f"Ricevuto {json.dumps(payload_json)} al tempo '{timestamp}'")
                # Controlla se il timestamp è più recente rispetto all'ultimo salvato
                last_timestamp = self.predictor.getlastrssi(mac_address)
                if last_timestamp is None or last_timestamp < timestamp:
                    self.predictor.addrssi(
                        {
                            "mac": mac_address,
                            "RSSI": rssi,
                            "timestamp": timestamp
                        },
                        mac_address)
                else:
                    logging.info(f"Scartato payload obsoleto per {mac_address}")
        except Exception as e:
            logging.error(f"Errore nel processare il payload: {e}")

    def on_message(self, mosq, obj, msg):
        # logger.info(f"Ricevuto messaggio: {msg.topic} {str(msg.payload)}")
        # collect rssi data from mesg and when ready computes the position
        try:
            # id should be taked by last part of topic
            id = msg.topic.split("/")[-1]

            msg = msg.payload.decode()
            payload_json = json.loads(msg)

            # Se il payload è una lista, iterare attraverso di essa
            if isinstance(payload_json, list):
                for item in payload_json:
                    self.process_payload(id, item)
            else:
                self.process_payload(id, payload_json)

        except Exception as e:
            logging.error(f"Errore nel processare il messaggio: {e}")
            logging.error(f"Payload: {msg}")
            pass


if __name__ == "__main__":
    aimodel = 'rf'
    pred = RSSIPredictor(aimodel)

    if paho.mqtt.__version__[0] > '1':
        client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1)
    else:
        client = mqttClient.Client()

    mqttClient = MqttClient(pred)
    client.on_message = mqttClient.on_message

    client.username_pw_set("iotrobotic", "iotrobotic")
    # client.tls_set('root.ca', certfile='c1.crt', keyfile='c1.key')
    client.connect("127.0.0.1", 1883, 60)
    client.subscribe(f"rssi/1", 0)

    client.loop_forever()
