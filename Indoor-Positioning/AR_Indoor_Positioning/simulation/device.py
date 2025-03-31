import paho.mqtt.client as mqttClient
import json
import pandas as pd
import paho
from datetime import datetime
import time

if __name__ == "__main__":

    df =pd.read_csv(r'C:/Users/terry/Desktop/blepositioning-main/data/test/4_Circonferenza.csv')
    print(df.head())
    

    if paho.mqtt.__version__[0] > '1':
        client = mqttClient.Client(mqttClient.CallbackAPIVersion.VERSION1)
    else:

        client = mqttClient.Client()

    client.username_pw_set("iotrobotic", "iotrobotic")
    #client.tls_set('root.ca', certfile='c1.crt', keyfile='c1.key')
    client.connect("127.0.0.1", 1883, 60)
    
    timestamp = 0
    while True:
        for index, row in df.iterrows():
#            dt = datetime.strptime(row.iloc[0], "%Y-%m-%dT%H:%M:%S.%f")
           # epoch = dt.timestamp()
            payload = {
                "mac": row[1],
                "RSSI": row[2],
                "timestamp": timestamp
                }
            client.publish("rssi/1", json.dumps(payload))
            print(f"Published {json.dumps(payload)}")
            timestamp += 1
            time.sleep(0.5)
   
    
    