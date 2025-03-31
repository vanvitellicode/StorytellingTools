import joblib
import pandas as pd
from sklearn.preprocessing import StandardScaler
from MQTT_Client.Posizionamento.Algoritmi.Point import ReferencePoint


def load_and_preprocess_data(file_path):
    data = pd.read_csv(file_path)

    # Estrazione delle features (RSSI) e delle coordinate (x, y)
    features = data.iloc[:, 3:].values
    x_values = data['x'].values  # coordinata x
    y_values = data['y'].values  # coordinata y

    # Applicazione dello scaling alle features (RSSI)
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # Salvataggio dello scaler per riutilizzo successivo lo faccio una sola volta
    # joblib.dump(scaler, 'scaler.pkl')

    # Creazione dei ReferencePoint utilizzando le scaled_features, x_values e y_values
    rps = []
    for i in range(len(scaled_features)):
        rp = ReferencePoint(scaled_features[i], [x_values[i], y_values[i]])
        rps.append(rp)

    return rps

# # TODO controllare le coordinate degli AP
#    # Lista di punti di accesso beacon
#    ap1 = AccessPoint(0, 0)  # blu
#    ap2 = AccessPoint(0, 2.2)  # verde
#    ap3 = AccessPoint(3.18, 0)  # nero
#    aps = [ap1, ap2, ap3]
