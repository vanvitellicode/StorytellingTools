#get all individuals of class QueryResult from ww2.owl
import owlready2
from owlready2 import *
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.cluster import KMeans
onto = get_ontology("./extended_mara_with_poi/ww2.owl").load()


#get all individuals of class QueryResult
results = list(onto.search(type = onto.QueryResult))

#create a dictionary with the queryresults individuals as key and the hasConcept individuals as values
queryresults_concepts = {}
for result in results:
    queryresults_concepts[result] = list(result.hasConcept)

#convert all in string
for key in queryresults_concepts:
    for i in range(len(queryresults_concepts[key])):
        queryresults_concepts[key][i] = str(queryresults_concepts[key][i])



#cluster the queryresults based on the concepts
from sklearn.cluster import KMeans
import numpy as np

df = pd.DataFrame.from_dict(queryresults_concepts, orient='index', columns=['feature1', 'feature2', 'feature3', 'feature4'])

# Reset dell'indice per ottenere 'name' come colonna
df.reset_index(inplace=True)
df.rename(columns={'index': 'name'}, inplace=True)

# Unificazione delle feature in un unico vettore
df['features'] = df[['feature1', 'feature2', 'feature3', 'feature4']].apply(lambda x: [i for i in x if i is not None], axis=1)
df.drop(columns=['feature1', 'feature2', 'feature3', 'feature4'], inplace=True)


#drop elements with no features
df = df[df['features'].map(len) > 0]

#remove None from df




print(df)
mlb = MultiLabelBinarizer()
vec = mlb.fit_transform(df['features'])
vectors = pd.DataFrame(vec, columns=mlb.classes_)


tfidf = TfidfVectorizer()
vec = tfidf.fit_transform(df['features'].apply(' '.join).to_list())
vectors = pd.DataFrame(vec.todense(), columns=tfidf.get_feature_names())

lda = LatentDirichletAllocation(n_components=3, verbose=0)
lda_features = lda.fit_transform(vec)


print(pd.DataFrame(lda.components_, 
             index=['topic1', 'topic2', 'topic3'], 
             columns=tfidf.get_feature_names()).round(1))

kmeans = KMeans(n_clusters=3)
kmeans.fit(vec)
df['pred'] = kmeans.predict(vec)
print(df)



import matplotlib.pyplot as plt

# Creazione del grafico di dispersione
plt.figure(figsize=(8, 6))
plt.scatter(df.index, df['pred'], c=df['pred'], cmap='viridis', s=50)
plt.xlabel('Individui')
plt.ylabel('Cluster Predetti')
plt.title('Clustering degli individui dell\'ontologia')
plt.xticks(rotation=45)
plt.grid(True)
plt.colorbar(label='Cluster')
plt.tight_layout()
plt.show()



import plotly.graph_objects as go

# Creazione del grafico interattivo
fig = go.Figure()

# Aggiungi le tracce per i cluster
for cluster_id in df['pred'].unique():
    cluster_data = df[df['pred'] == cluster_id]
    fig.add_trace(go.Scatter(x=cluster_data.index, y=[cluster_id] * len(cluster_data),
                             mode='markers', marker=dict(size=10),
                             name=f'Cluster {cluster_id}'))

# Aggiungi informazioni sui concetti associati quando si passa sopra un punto
hover_text = []
for index, row in df.iterrows():
    hover_text.append(f'<b>{row["name"]}</b><br><br>' +
                      '<br>'.join([f'Concept {i+1}: {concept}' for i, concept in enumerate(row["features"])]))

fig.update_traces(text=hover_text, hoverinfo='text')

# Aggiungi layout e titoli
fig.update_layout(title='Clustering degli individui dell\'ontologia',
                  xaxis_title='Individui',
                  yaxis_title='Cluster Predetti',
                  hovermode='closest',
                  xaxis=dict(tickangle=45),
                  yaxis=dict(dtick=1))

fig.show()