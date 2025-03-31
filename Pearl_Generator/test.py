from owlready2 import *

# Carica l'ontologia OWL
onto = get_ontology("./uploads/ww.owl").load()
# Funzione per trovare la distanza tra due classi nell'ontologia
def find_distance_classes(class1, class2):
    # Funzione per trovare il percorso tra una classe e la radice dell'ontologia

    def find_path_to_root(cls, root):
        path = []
        while cls != root:
            try:
                cls = cls.is_a[0]  # Considera solo la prima super-classe (la più specifica)
                path.append(cls)
            except:
                return path
        return path

    # Controlla se entrambe le classi esistono nell'ontologia
    if not class1 or not class2:
        return -1
    
    # Trova la radice dell'ontologia
    root = onto["Thing"]

    # Se una classe è una sotto-classe dell'altra, la distanza è 1
    if class1.is_a.first() == class2 or class2.is_a.first() == class1:
        return 1

    # Trova i percorsi di entrambe le classi fino alla radice
    path_to_class1 = find_path_to_root(class1, root)
    path_to_class2 = find_path_to_root(class2, root)

    # Trova il punto in comune tra i percorsi
    common_parent = None
    for parent in path_to_class1:
        if parent in path_to_class2:
            common_parent = parent
            break
    if("Thing" in str(common_parent)):
        return 1000
    # Se non c'è un punto in comune, non c'è nessun percorso tra le classi
    if not common_parent:
        return -1

    # Calcola la distanza
    distance = path_to_class1.index(common_parent) + path_to_class2.index(common_parent) + 2

    # Se una classe è genitore dell'altra
    if class1 in path_to_class2:
        distance += 1
    elif class2 in path_to_class1:
        distance += 1

    return distance
# Esempio di utilizzo
class1_name = onto.search(iri = "*painting_technique")[0]
class2_name =   onto.search(iri = "*Art")[0]

distance = find_distance_classes(class1_name, class2_name)
if distance != -1:
    print(f"The distance between {class1_name} and {class2_name} is {distance}.")
else:
    print(f"There is no connection between {class1_name} and {class2_name} in the ontology.")