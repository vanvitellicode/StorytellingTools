import requests


from owlready2 import *

# Load the ontology file
onto = get_ontology("./extended_mara_with_poi/ww.owl").load()

api_key="titterso"

with onto:
    class painting_technique(Thing):
        pass
    class QueryResult(Thing):
        pass
    class Art(Thing):
        pass
    class Documents(Thing):
        pass
    class Book(Thing):
        pass
    class Event(Thing):
        pass
    class War(Thing):
        pass
    class Material(Thing):
        pass
    class Metal(Thing):
        pass
    class Topic(Thing):
        pass
    class Movie(Thing):
        pass
    class People(Thing):
        pass
    class Place(Thing):
        pass
    class Wearable(Thing):
        pass
    
    class hasConcept(ObjectProperty):
        domain = [QueryResult]


url = "https://api.europeana.eu/record/v2/search.json"
query_params = {
    "query": "world war",
    "media": "true",
    "rows": "100",
    "wskey": api_key
}

response = requests.get(url, params=query_params)
concept_list=[]

if response.status_code == 200:
    data = response.json()
    for single_data in data:
        if single_data == "items":
            for item in data[single_data]:
                print("---------------------------------------------")

                print(item["title"])
                if("Licourt Military World War I" not in str(item["title"]) and "Világháborús emlékmű" not in str(item["title"])):
                    response_item = requests.get(item["link"])
                    data_item = response_item.json()
                    for single_data_item in data_item:
                        try:
                            for name in data_item["object"]['concepts']:
                                try:
                                    if(name["prefLabel"]["en"] not in concept_list):
                                        item["title"] = list(dict.fromkeys(item["title"]))
                                        #create instance of QueryResult in ontology 

                                        #create instance of QueryResult in ontology
                                        #delete special chars from item["title"]
                                        item["title"] = str(item["title"]).replace("['","").replace("']","").replace("', '","").replace(" ", "_").replace('["','').replace('"]','').replace(",',_",'').replace('"','').replace("'", "").replace("\'", "")
                                        query_result = QueryResult(item["title"])

                                        #create instance of QueryResult in ontology
                                        #delete special chars from item["title"]
                                        #check if name["preflabel"]["en"] is in utf-8
                                        
                                        file2 = open('items2.txt','w')

                                        file2.write(str(name["prefLabel"]["en"])+"\n")

                                        file2.close()


                                        name["prefLabel"]["en"] = str(name["prefLabel"]["en"]).replace("['","").replace("']","").replace("', '","").replace(" ", "_").replace("\'", "")
                                        added = True
                                        if("Oil painting" in  name["prefLabel"]["en"]):
                                            concept = painting_technique( name["prefLabel"]["en"])
                                        elif("Print" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("World War" in name["prefLabel"]["en"]):
                                            concept = War( name["prefLabel"]["en"])
                                        elif("History" in name["prefLabel"]["en"]):
                                            concept = Topic( name["prefLabel"]["en"])
                                        elif("Poem" in name["prefLabel"]["en"]):
                                            concept = Book( name["prefLabel"]["en"])
                                        elif("Iron" in name["prefLabel"]["en"]):
                                            concept = Metal( name["prefLabel"]["en"])
                                        elif("Silver" in name["prefLabel"]["en"]):
                                            concept = Metal( name["prefLabel"]["en"])
                                        elif("Fine art" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("Art of painting" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("Monograph" in name["prefLabel"]["en"]):
                                            concept = Book( name["prefLabel"]["en"])
                                        elif("Photograph" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("interviewees" in name["prefLabel"]["en"]):
                                            concept = Documents( name["prefLabel"]["en"])
                                        elif("film" in name["prefLabel"]["en"]):
                                            concept = Movie( name["prefLabel"]["en"])
                                        elif("Soldiers" in name["prefLabel"]["en"]):
                                            concept = People( name["prefLabel"]["en"])
                                        elif("memorials" in name["prefLabel"]["en"]):
                                            concept = Place( name["prefLabel"]["en"])
                                        elif("Mausoleum" in name["prefLabel"]["en"]):
                                            concept = Place( name["prefLabel"]["en"])
                                        elif("Chapter" in name["prefLabel"]["en"]):
                                            concept = Book( name["prefLabel"]["en"])
                                        elif("censorship" in name["prefLabel"]["en"]):
                                            concept = Documents( name["prefLabel"]["en"])
                                        elif("official documents" in name["prefLabel"]["en"]):
                                            concept = Documents( name["prefLabel"]["en"])
                                        elif("documents" in name["prefLabel"]["en"]):
                                            concept = Documents( name["prefLabel"]["en"])
                                        elif("ootwear" in name["prefLabel"]["en"]):
                                            concept = Wearable( name["prefLabel"]["en"])
                                        elif("Sandal" in name["prefLabel"]["en"]):
                                            concept = Wearable( name["prefLabel"]["en"])
                                        elif("Drawing" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("art" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("Drawing" in name["prefLabel"]["en"]):
                                            concept = Art( name["prefLabel"]["en"])
                                        elif("Uniform" in name["prefLabel"]["en"]):
                                            concept = Wearable( name["prefLabel"]["en"])
                                        elif("Ruins" in name["prefLabel"]["en"]):
                                            concept = Place( name["prefLabel"]["en"])
                                        else:
                                            added = False
                                        if(added == True):
                                            query_result.hasConcept.append(concept) 
                                        concept_list.append(str([item["title"], name["prefLabel"]["en"]]))
                                        print(name["prefLabel"]["en"])
                                except Exception as e:
                                    print(e)
                        except Exception as e:
                            print(e)
    # Process the data as needed
else:
    print("Error occurred while calling the API:", response.status_code)

#delete duplicates of concept_list
concept_list = list(dict.fromkeys(concept_list))


#write in file concept_list
file = open('items.txt','w')
for item in concept_list:
    print(item)
    file.write(str(item)+"\n")

file.close()


#save the ontology
onto.save(file = "./extended_mara_with_poi/ww2.owl", format = "rdfxml")

