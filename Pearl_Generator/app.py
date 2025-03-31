import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, jsonify
from werkzeug.exceptions import abort
from owlready2 import *
import requests
import types
import networkx as nx
from pyvis.network import Network

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn




app = Flask(__name__, static_url_path='', static_folder='static')
app.config['SECRET_KEY'] = 'your secret key'
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
actual_ontology = None
api_key="titterso"
ontology_name = ''

def getAllClasses():
    global actual_ontology
    if actual_ontology is not None:
        onto = actual_ontology
        return list(onto.classes())
    return None

def fill_selections_homepage():
    global actual_ontology
    if actual_ontology is not None:
        onto = actual_ontology
        with onto:
            class pearl(Thing):
                pass
        pearls = list(onto.search(type = pearl))
        
        #convert all elements of pearls to string
        pearls = [str(pearl) for pearl in pearls]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT pearl_name, class_name, weight FROM pearls_to_classes')
        pairs = cursor.fetchall()
        conn.close()
        tree = {}
        dict_ = convert_ontology_to_tree(onto)

        for k,v in dict_.items():
            n = tree_find(k, tree)
            (tree if not n else n)[k] = {e:{} for e in v}
        return pearls, tree , pairs
    return render_template('index.html')


def fill_selections_concepts_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT concept_name FROM concepts')
    concepts = cursor.fetchall()
    global actual_ontology
    classes = []
    if actual_ontology is not None:
        onto = actual_ontology
        classes = list(onto.classes())
    cursor = conn.cursor()
    cursor.execute('SELECT concept_name, class_name FROM concepts_to_classes')
    pairs = cursor.fetchall()
    conn.close()
    concepts_found = []
    tree = {}
    if actual_ontology is not None:
        dict_ = convert_ontology_to_tree(onto)

        for k,v in dict_.items():
            n = tree_find(k, tree)
            (tree if not n else n)[k] = {e:{} for e in v}

    for coppia in pairs:
        concetto = coppia[0]
        if concetto not in concepts_found:
            concepts_found.append(concetto)  
    if(len(concepts) == 0):
        return concepts,tree, pairs, '0'

    return concepts,tree, pairs, str(round(len(concepts_found)*100/len(concepts),1))



@app.route('/')
def index():
    global actual_ontology
    if actual_ontology is not None:
        pearls, tree, pairs = fill_selections_homepage() 
        return render_template('index.html', pearls = pearls, tree=tree, pairs=pairs)
    else:
        tree = {}
        pearls = []
        pairs = []
        return render_template('index.html', pearls = pearls, tree=tree, pairs=pairs)




@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "Nessun file trovato"
    file = request.files['file']
    if file.filename == '':
        return "Nome del file vuoto"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    global actual_ontology
    global ontology_name
    ontology_name = file.filename
    actual_ontology = get_ontology(file_path).load()
    pearls, tree, pairs = fill_selections_homepage() 
    return render_template('index.html', pearls = pearls, tree=tree, pairs=pairs)

@app.route('/create_pearl', methods=['POST'])
def create_pearl():
    global actual_ontology
    with actual_ontology:
        class pearl(Thing):
            pass
    pearl_names = [ind.name for ind in actual_ontology.search(type=actual_ontology.pearl)]
    for i in range(1, len(pearl_names) + 2):
        if "pearl" + str(i) not in pearl_names:
            new_pearl_name = "pearl" + str(i)
            break    
    concept = pearl(new_pearl_name)
    pearls, tree, pairs = fill_selections_homepage() 
    return render_template('index.html', pearls = pearls, tree = tree, pairs=pairs)

@app.route('/delete', methods=['POST'])
def delete_pearl():
    data = request.json
    selected_value = data['selectedValue']
    global actual_ontology
    with actual_ontology:
        #search for an individual named selected_value
        individuals = list(actual_ontology.search(iri="*"+selected_value.split(".")[1]))
        destroy_entity(individuals[0])
    pearls, tree, pairs = fill_selections_homepage()

    return render_template('index.html', pearls = pearls, tree = tree, pairs=pairs)


@app.route('/associatePearlToClass', methods=['POST'])
def associatePearlToClass():
    global ontology_name
    #get name of actual ontology
    print(ontology_name)
    data = request.json
    selected_pearl = data['selectedValuePearl']
    selected_class = data['selectedValueClass']
    print(selected_class)
    weight = 1
    conn = get_db_connection()
    for classs in selected_class:
        classname = "uploads\\"+ontology_name.split("owl")[0]+classs.split("______")[0]
        conn.execute('INSERT INTO pearls_to_classes (pearl_name, class_name, weight) VALUES (?, ?,?)', (selected_pearl, classname, weight))
        conn.commit()
    conn.close()
    pearls, tree, pairs = fill_selections_homepage()
    return render_template('index.html', pearls = pearls, tree = tree, pairs=pairs)


@app.route('/disassociatePearlToClass', methods=['POST'])
def disassociatePearlToClass():
    data = request.json
    conn = get_db_connection()
    for element in data['selectedCheckboxIds']:
        conn.execute('DELETE FROM pearls_to_classes WHERE pearl_name = ? AND class_name = ?', (element.split("_____")[0], element.split("_____")[1]))
    conn.commit()
    conn.close()
    pearls, tree, pairs = fill_selections_homepage()
    return render_template('index.html', pearls = pearls, tree = tree, pairs=pairs)

@app.route('/content_index', methods=['GET'])
def content_index():
    concepts, tree, pairs, percentage = fill_selections_concepts_page()
    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs, percentage = percentage)

@app.route('/search', methods=['POST'])
def search():
    global api_key
    data = request.json
    searchString = data["searchingValue"]
    url = "https://api.europeana.eu/record/v2/search.json"
    query_params = {
        "query": searchString,
        "media": "true",
        "rows": "100",
        "wskey": api_key
    }
    response = requests.get(url, params=query_params)
    concept_list=[]
    conn = get_db_connection()

    if response.status_code == 200:
        data = response.json()
        for single_data in data:
            if single_data == "items":
                for item in data[single_data]:
                    if("Licourt Military World War I" not in str(item["title"]) and "Világháborús emlékmű" not in str(item["title"])):
                        response_item = requests.get(item["link"])
                        data_item = response_item.json()
                        for single_data_item in data_item:
                            try:
                                for name in data_item["object"]['concepts']:
                                    try:
                                        if(name["prefLabel"]["en"] not in concept_list):
                                            item["title"] = list(dict.fromkeys(item["title"]))
                                            item["title"] = str(item["title"]).replace("['","").replace("']","").replace("', '","").replace(" ", "_").replace('["','').replace('"]','').replace(",',_",'').replace('"','').replace("'", "").replace("\'", "")
                                            name["prefLabel"]["en"] = str(name["prefLabel"]["en"]).replace("['","").replace("']","").replace("', '","").replace(" ", "_").replace("\'", "")
                                            concept_name = name["prefLabel"]["en"]
                                            content_name = item["title"]
                                            cursor = conn.cursor()
                                            cursor.execute("SELECT 1 FROM concepts WHERE concept_name = ?", (concept_name,))
                                            if not cursor.fetchone():  
                                                cursor.execute("INSERT INTO concepts (concept_name) VALUES (?)", (concept_name,))
                                                conn.commit()
                                            cursor = conn.cursor()
                                            cursor.execute("SELECT 1 FROM contents WHERE content_name = ?", (content_name,))
                                            if not cursor.fetchone():  
                                                cursor.execute("INSERT INTO contents (content_name) VALUES (?)", (content_name,))
                                                conn.commit()
                                            cursor = conn.cursor()
                                            cursor.execute("SELECT 1 FROM contents_to_concepts WHERE concept_name = ? AND content_name = ?", (concept_name, content_name))
                                            if not cursor.fetchone():  
                                                cursor.execute("INSERT INTO contents_to_concepts (concept_name, content_name) VALUES (?, ?)", (concept_name, content_name))
                                                conn.commit()
                                    except Exception as e:
                                        print(e)
                            except Exception as e:
                                print(e)
        # Process the data as needed
    
    else:
        print("Error occurred while calling the API:", response.status_code)
    concepts, tree, pairs, percentage = fill_selections_concepts_page()
    conn.close()

    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs,  percentage = percentage)


@app.route('/test', methods=['GET'])
def deleteConcept():
    return render_template('test.html')


@app.route('/associateConceptToClass', methods=['POST'])
def associateConceptToClass():
    data = request.json

    concepts = data['selectedValuesConcept']
    classes = data['selectedValuesClass']
    conn = get_db_connection()
    print(concepts)
    print(classes)
    for concept in concepts:
        for classs in classes:
            classs = classs.split("______")[0]
            conn.execute('INSERT INTO concepts_to_classes (concept_name, class_name) VALUES (?, ?)', (concept, classs))
    conn.commit()
    conn.close()

    concepts, tree, pairs, percentage = fill_selections_concepts_page()

    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs,  percentage = percentage)


@app.route('/deleteConceptToClass', methods=['POST'])
def deleteConceptToClass():
    data = request.json
    conn = get_db_connection()
    for element in data['selectedCheckboxIds']:
        conn.execute('DELETE FROM concepts_to_classes WHERE concept_name = ? AND class_name = ?', (element.split("_____")[0], element.split("_____")[1]))
    conn.commit()
    conn.close()
    concepts, tree, pairs, percentage = fill_selections_concepts_page()

    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs,  percentage = percentage)




@app.route('/confirmIstancies', methods=['POST'])
def confirmIstancies():
    global actual_ontology
    onto = actual_ontology
    classDict = {}
    with onto:
        for class_name in list(onto.classes()) :
            classDict[str(class_name).split(".")[1]] = types.new_class(str(class_name).split(".")[1], (Thing,))

    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT concept_name, class_name FROM concepts_to_classes')
    pairs = cursor.fetchall()

    concept_name_to_obj = {}
    for pair in pairs:
        with onto:
            concept = classDict[str(pair[1])](pair[0])
            concept_name_to_obj[pair[0]] = concept
    
    with onto:
        class hasConcept(ObjectProperty):
            domain = [classDict["Multimedia_Content"]]
        class belongToPearl(ObjectProperty):
            domain = [classDict["Multimedia_Content"]]
            range = [classDict["pearl"]]
    cursor = conn.cursor()
    cursor.execute('SELECT content_name FROM contents')
    contents = cursor.fetchall()
    cursor = conn.cursor()
    cursor.execute('SELECT pearl_name, class_name, weight FROM pearls_to_classes')
    pearl_to_class = cursor.fetchall()
    #convert pearl_to_class to a dictionary where the value are lists of pearls
    pearl_to_class_dict = {}
    pearls = list(onto.search(type = onto.pearl))
    #create a dict where the key is the pearl parsed to string and the value is the pearl_to_class
    pearl_to_class_dict_string = {}
    for pearl in pearls:
        pearl_to_class_dict_string[str(pearl)] = pearl

    for pair in pearl_to_class:
        if pair[1] in pearl_to_class_dict:
            pearl_to_class_dict[pair[1]].append([pearl_to_class_dict_string[pair[0]], pair[2]])
        else:
            pearl_to_class_dict[pair[1]] = [[pearl_to_class_dict_string[pair[0]],pair[2]]]
    #get all pearls from ontology
    content_to_pearl_weight = {}
    pearl_to_str = {}
    for content in contents:
        content_to_pearl_weight[content[0]] = {}
        with onto:
            content_item = classDict["Multimedia_Content"](content[0])
            cursor.execute('SELECT concept_name FROM contents_to_concepts WHERE content_name = ?', (content[0],))
            concepts = cursor.fetchall()
            for concept in concepts:
                print(concept[0])
                if(concept[0] in concept_name_to_obj.keys()):
                    content_item.hasConcept.append(concept_name_to_obj[concept[0]])
                cursor.execute('SELECT class_name FROM concepts_to_classes WHERE concept_name = ?', (concept[0],))
                classes = cursor.fetchall()
                
                for classs in classes:
                    if( "uploads\\"+ontology_name.split("owl")[0]+classs[0] in pearl_to_class_dict.keys()):
                        for x in pearl_to_class_dict["uploads\\"+ontology_name.split("owl")[0]+classs[0]]:
                            if(x[0] in content_to_pearl_weight[content[0]].keys()):
                                content_to_pearl_weight[content[0]][x[0]] += x[1]
                            else:
                                content_to_pearl_weight[content[0]][x[0]] = x[1]
                            pearl_to_str[str(x[0]).split('.')[-1]] = x[0]
                            content_item.belongToPearl.append(x[0])

    concepts, tree, pairs, percentage = fill_selections_concepts_page()

    conn.close()
    onto.save(file = "./uploads/ww2.owl", format = "rdfxml")
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "ww2.owl")
    onto = get_ontology(file_path).load()
    pearls = []
    multimedia_contents = []
    for i in onto.classes():
        if "pearl" in str(i):
            pearls = i.instances()
        if "Multimedia_Content" in str(i):
            multimedia_contents = i.instances()
    #create a graph with the number of contents for each pearl
    G = nx.DiGraph()
    contents_in_pearls_count = {}
    total_number_of_contents = len(multimedia_contents)
    numb_of_con_in_diff_pearl = 0
    contents_without_pearl = 0
    content_with_at_least_one_pearl = 0
    num_of_pearl = 2
    for content in multimedia_contents:
        alert = 1
        G.add_node(content.name, size=5, title=content.name, group=1)
        for pearl in content.belongToPearl:
            if(alert == 1):
                content_with_at_least_one_pearl += 1
                alert = 0
            if pearl in pearls:
                #check if the node is already in the graph
                if(pearl.name not in G.nodes):
                    G.add_node(pearl.name, size=20, title=pearl.name, group=num_of_pearl)
                    num_of_pearl += 1
                if(pearl.name in contents_in_pearls_count.keys()):
                    contents_in_pearls_count[pearl.name] += 1
                else:
                    contents_in_pearls_count[pearl.name] = 1
                numb_of_con_in_diff_pearl += 1
                G.add_edge(pearl.name, content.name,  title="weight = "+ str(content_to_pearl_weight[content.name][pearl_to_str[pearl.name]]), value = content_to_pearl_weight[content.name][pearl_to_str[pearl.name]]/10, weigth = content_to_pearl_weight[content.name][pearl_to_str[pearl.name]])
    contents_without_pearl = total_number_of_contents - content_with_at_least_one_pearl
    nt = Network('550px', '910px')
    nt.from_nx(G, show_edge_weights=True)
    nt.save_graph('templates/graph.html')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "graph.graphml")

    nx.write_graphml_lxml(G, file_path)

    #create a bar chart with the number of contents for each pearl using plotly
    import plotly
    import plotly.graph_objs as go
    contents_in_pearls_count['Content Without pearls'] = contents_without_pearl
    contents_in_pearls_count['Total Number of Contents'] = total_number_of_contents
    contents_in_pearls_count['Contents with at least one pearl'] = content_with_at_least_one_pearl
    contents_in_pearls_count['Conflicts'] = numb_of_con_in_diff_pearl - content_with_at_least_one_pearl
    fig = go.Figure([go.Bar(x=list(contents_in_pearls_count.keys()), y=list(contents_in_pearls_count.values()))])
    plotly.offline.plot(fig, filename='templates/bar_chart.html', auto_open=False)

    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs,  percentage = percentage)



def find_distance_classes(class1, class2):
    # Funzione per trovare il percorso tra una classe e la radice dell'ontologia
    global actual_ontology 
    onto = actual_ontology
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


@app.route('/adjustConflicts', methods=['POST'])
def adjustConflicts():
    global actual_ontology
    onto = actual_ontology
    classDict = {}
    with onto:
        for class_name in list(onto.classes()) :
            classDict[str(class_name).split(".")[1]] = types.new_class(str(class_name).split(".")[1], (Thing,))
    #delete ./uploads/ww2.owl
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT concept_name, class_name FROM concepts_to_classes')
    pairs = cursor.fetchall()

    concept_name_to_obj = {}
    for pair in pairs:
        with onto:
            concept = classDict[str(pair[1])](pair[0])
            concept_name_to_obj[pair[0]] = concept
    
    with onto:
        class hasConcept(ObjectProperty):
            domain = [classDict["Multimedia_Content"]]
        class belongToPearl(ObjectProperty):
            domain = [classDict["Multimedia_Content"]]
            range = [classDict["pearl"]]
    cursor = conn.cursor()
    cursor.execute('SELECT content_name FROM contents')
    contents = cursor.fetchall()
    cursor = conn.cursor()
    cursor.execute('SELECT pearl_name, class_name, weight FROM pearls_to_classes')
    pearl_to_class = cursor.fetchall()
    #convert pearl_to_class to a dictionary where the value are lists of pearls
    pearl_to_class_dict = {}
    pearls = list(onto.search(type = onto.pearl))
    #create a dict where the key is the pearl parsed to string and the value is the pearl_to_class
    pearl_to_class_dict_string = {}
    for pearl in pearls:
        pearl_to_class_dict_string[str(pearl)] = pearl

    for pair in pearl_to_class:
        if pair[1] in pearl_to_class_dict:
            pearl_to_class_dict[pair[1]].append([pearl_to_class_dict_string[pair[0]], pair[2]])
        else:
            pearl_to_class_dict[pair[1]] = [[pearl_to_class_dict_string[pair[0]],pair[2]]]
    #get all pearls from ontology
    content_to_pearl_weight = {}
    pearl_to_str= {}
    for content in contents:
        concept_distance_from_pearl_classes = {}
        content_to_pearl_weight[content[0]] = {}
        with onto:
            content_item = classDict["Multimedia_Content"](content[0])
            cursor.execute('SELECT concept_name FROM contents_to_concepts WHERE content_name = ?', (content[0],))
            concepts = cursor.fetchall()
            for concept in concepts:
                if(concept[0] in concept_name_to_obj.keys()):
                    content_item.hasConcept.append(concept_name_to_obj[concept[0]])
                cursor.execute('SELECT class_name FROM concepts_to_classes WHERE concept_name = ?', (concept[0],))
                classes = cursor.fetchall()
                
                for classs in classes:
                    if( "uploads\\"+ontology_name.split("owl")[0]+classs[0] in pearl_to_class_dict.keys()):
                        for x in pearl_to_class_dict["uploads\\"+ontology_name.split("owl")[0]+classs[0]]:
                            if(x[0] in content_to_pearl_weight[content[0]].keys()):
                                content_to_pearl_weight[content[0]][x[0]] += x[1]
                            else:
                                content_to_pearl_weight[content[0]][x[0]] = x[1]
                            pearl_to_str[str(x[0]).split('.')[-1]] = x[0]
                    else:
                        if(classs[0] not in concept_distance_from_pearl_classes.keys()):
                            concept_distance_from_pearl_classes[classs[0]] = {}
                            for key in pearl_to_class_dict.keys():
                                class1_name = onto.search(iri = "*"+classs[0])[0]
                                class2_name =   onto.search(iri = "*"+key.split('.')[-1])[0]

                                distance = find_distance_classes(class1_name, class2_name)
                                for pearl_found in pearl_to_class_dict[key]:
                                    if(pearl_found[0] not in concept_distance_from_pearl_classes[classs[0]].keys()):
                                        concept_distance_from_pearl_classes[classs[0]][pearl_found[0]] = [distance, pearl_found[1]]
                                    if(concept_distance_from_pearl_classes[classs[0]][pearl_found[0]][0] > distance or (concept_distance_from_pearl_classes[classs[0]][pearl_found[0]][0] == distance and concept_distance_from_pearl_classes[classs[0]][pearl_found[0]][1] < pearl_found[1])):
                                        concept_distance_from_pearl_classes[classs[0]] = [distance, pearl_found[1]]

            #find key of max of content_to_pearl_weight[content[0]]
            if(len(content_to_pearl_weight[content[0]]) != 0):
                #remove all objectproperty belongToPearl from content
                content_item.belongToPearl = []
                max_key = max(content_to_pearl_weight[content[0]], key=content_to_pearl_weight[content[0]].get)
                content_item.belongToPearl.append(max_key)
            else:
                content_item.belongToPearl = []
                result = {}
                print(concept_distance_from_pearl_classes)
                for key, value in concept_distance_from_pearl_classes.items():
                    min_value = float('inf')
                    min_key = None
                    max_second_value = float('-inf')

                    for inner_key, inner_value in value.items():
                        first_value, second_value = inner_value
                        if first_value < min_value:
                            min_value = first_value
                            min_key = inner_key
                            max_second_value = second_value
                        elif first_value == min_value:
                            max_second_value = max(max_second_value, second_value)

                    result[key] = {min_key: [min_value, max_second_value]}
                    content_to_pearl_weight[content[0]][min_key] = max_second_value
                    content_item.belongToPearl.append(min_key)


    concepts, tree, pairs, percentage = fill_selections_concepts_page()

    conn.close()
    print(concept_distance_from_pearl_classes)



    onto.save(file = "./uploads/ww2.owl", format = "rdfxml")


    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "ww2.owl")
    onto = get_ontology(file_path).load()
    pearls = []
    multimedia_contents = []
    for i in onto.classes():
        if "pearl" in str(i):
            pearls = i.instances()
        if "Multimedia_Content" in str(i):
            multimedia_contents = i.instances()
    #create a graph with the number of contents for each pearl
    G = nx.DiGraph()
    contents_in_pearls_count = {}
    total_number_of_contents = len(multimedia_contents)
    numb_of_con_in_diff_pearl = 0
    contents_without_pearl = 0
    content_with_at_least_one_pearl = 0
    num_of_pearl = 2
    for content in multimedia_contents:
        alert = 1
        G.add_node(content.name, size=5, title=content.name, group=1)

        for pearl in content.belongToPearl:
            if(alert == 1):
                content_with_at_least_one_pearl += 1
                alert = 0
            if pearl in pearls:
                #check if the node is already in the graph
                if(pearl.name not in G.nodes):
                    G.add_node(pearl.name, size=20, title=pearl.name, group=num_of_pearl)
                    num_of_pearl += 1
                if(pearl.name in contents_in_pearls_count.keys()):
                    contents_in_pearls_count[pearl.name] += 1
                else:
                    contents_in_pearls_count[pearl.name] = 1
                numb_of_con_in_diff_pearl += 1
                G.add_edge(pearl.name, content.name,  title="weight = "+ str(content_to_pearl_weight[content.name][pearl_to_str[pearl.name]]), value = content_to_pearl_weight[content.name][pearl_to_str[pearl.name]]/10, weigth = content_to_pearl_weight[content.name][pearl_to_str[pearl.name]])
    contents_without_pearl = total_number_of_contents - content_with_at_least_one_pearl
    nt = Network('550px', '910px')
    nt.from_nx(G, show_edge_weights=True)
    nt.save_graph('templates/graph.html')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], "graph.graphml")

    nx.write_graphml_lxml(G, file_path)

    #create a bar chart with the number of contents for each pearl using plotly
    import plotly
    import plotly.graph_objs as go
    contents_in_pearls_count['Content Without pearls'] = contents_without_pearl
    contents_in_pearls_count['Total Number of Contents'] = total_number_of_contents
    contents_in_pearls_count['Contents with at least one pearl'] = content_with_at_least_one_pearl
    contents_in_pearls_count['Conflicts'] = numb_of_con_in_diff_pearl - content_with_at_least_one_pearl
    fig = go.Figure([go.Bar(x=list(contents_in_pearls_count.keys()), y=list(contents_in_pearls_count.values()))])
    plotly.offline.plot(fig, filename='templates/bar_chart.html', auto_open=False)

    return render_template('concepts.html', concepts = concepts, tree = tree, pairs = pairs,  percentage = percentage)











@app.route('/visualizePearls', methods=['GET'])
def view_charts():

    return render_template('visualization.html')

@app.route('/getChart', methods=['GET'])
def getChart():

    return render_template('graph.html')

@app.route('/getBarChart', methods=['GET'])
def getBarChart():

    return render_template('bar_chart.html')


@app.route('/changeWeights', methods=['POST'])
def changeWeight():
    data = request.json
    conn = get_db_connection()

    for value in data['selectedWeightIds']:
        if(value.split("____")[0] != "numberPick"):
            conn.execute('UPDATE pearls_to_classes SET weight = ? WHERE pearl_name = ? AND class_name = ?', (value.split("____")[-1], value.split("_____")[0], value.split("_____")[1]))
    conn.commit()
    conn.close()
    #return index using the same function
    pearls, tree, pairs = fill_selections_homepage()
    return render_template('index.html', pearls = pearls, tree = tree, pairs=pairs)



def tree_find(e, t):
    if e in t:
        return t
    for v in t.values():
        r = tree_find(e, v)
        if r:
            return r
    return None


def convert_ontology_to_tree(onto):
    # Carica l'ontologia

    # Inizializza il dizionario dell'albero
    tree = {}

    # Definisci una funzione ricorsiva per esplorare le classi dell'ontologia
    def explore_class(cls, parent_key=None):
        class_name = cls.name
        children = []
        
        # Aggiungi le sottoclassi di questa classe come figli
        for subclass in cls.subclasses():
            explore_class(subclass, parent_key=class_name)
            children.append(subclass.name)
        if(len(children) != 0):
            tree[class_name] = children

    superclasses = []
    for root_class in onto.classes():
        if(len(root_class.ancestors()) == 2):
            superclasses.append(root_class.name.split('.')[-1])

    tree['Thing'] = superclasses
    for root_class in onto.classes():
        if(len(root_class.ancestors()) == 2):
            explore_class(root_class)
    return tree



app.run(debug=True)


