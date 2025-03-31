import joblib
from MQTT_Client.Posizionamento.Algoritmi.Preprocessing import load_and_preprocess_data  # Usa la tua funzione di preprocessing
from MQTT_Client.Posizionamento.Algoritmi.Positioning import Positioning  # Classe Positioning dal file positioning.py
import argparse


# Funzione per addestrare e salvare il modello
def train_and_save_model(csv_file, model_file, model_type, optimize, **model_params):
    """
       Addestra e salva un modello di posizionamento.

       :param csv_file: File CSV con i dati
       :param model_file: File di output per salvare il modello
       :param model_type: Tipo di modello ('knn', 'gradient', 'svr', 'xgboost')
       :param optimize: Se abilitare l'ottimizzazione del modello
       :param model_params: Parametri specifici per il modello
       """

    # Carica e preprocessa i dati
    rps = load_and_preprocess_data(csv_file)

    # Inizializza l'oggetto Positioning con il tipo di modello scelto
    positioning = Positioning(model_type=model_type, optimize=optimize, **model_params)

    # Addestra il modello
    positioning.train(rps)

    # Salva il modello addestrato

    # Crea un dizionario per i modelli x e y
    models_dict = {
        'model_x': positioning.model_x,
        'model_y': positioning.model_y
    }

    # Salva il dizionario contenente i modelli in un unico file
    joblib.dump(models_dict, model_file)

    # joblib.dump(positioning, model_file)
    # print(f"Modello {model_type} salvato come {model_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Addestra un modello di posizionamento.')
    parser.add_argument('--model', type=str, default='knn',
                        help="Tipo di modello ('knn', , 'svr', 'rf', ecc.)")
    parser.add_argument('--csv', type=str, required=True, help='Percorso al file CSV con i dati')
    parser.add_argument('--output', type=str, default='modello.pkl', help='Nome del file per il modello salvato')
    parser.add_argument('--optimize', action='store_true', help='Ottimizzare i parametri del modello')
    parser.add_argument('--n_neighbors', type=int, default=5, help='Numero di vicini per KNN')
    parser.add_argument('--p', type=int, default=1, help='p per KNN')
    parser.add_argument('--C', type=float, default=1.0, help="Parametro C per modelli come SVR")
    parser.add_argument('--kernel', type=str, default='rbf', help="Kernel per SVR")
    parser.add_argument('--max_depth', type=int, default=3, help="Max depth perRandom Forest")
    parser.add_argument('--n_estimators', type=int, default=100,
                        help="Numero di stimatori per Random Forest")

    args = parser.parse_args()

    # Parametri specifici per il modello
    model_params = {}
    if args.model == 'knn':
        model_params['n_neighbors'] = args.n_neighbors
    elif args.model == 'svr':
        model_params['C'] = args.C
        model_params['kernel'] = args.kernel
    elif args.model in ['rf']:
        model_params['max_depth'] = args.max_depth
        model_params['n_estimators'] = args.n_estimators

    # Esegui l'addestramento e salva il modello, passa 'optimize' come argomento
    train_and_save_model(args.csv, args.output, args.model, args.optimize, **model_params)
