import pandas as pd
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np
import requests
import speech_recognition as sr

df = pd.read_excel('RemédioseFarmáciasJuntos.xlsx')
df_pharmacy = pd.read_excel('Farmácias.xlsx')
df_medicine = 'RemédiosPortuguês.xlsx'

def clusterize_remedios(file_path, num_clusters=5):
    # Lê o arquivo Excel
    df_cluster = pd.read_excel(file_path)

    # Selecionar colunas relevantes para clusterização
    features = df_cluster[["Nome", "Descrição", "Forma de Uso", "Efeitos Colaterais"]]

    # Pré-processamento dos textos
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(features["Descrição"])

    # Clusterização com K-means
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    df_cluster["Cluster"] = kmeans.fit_predict(tfidf_matrix.toarray())

    return df_cluster

# Clusteriza os remédios
remedios_clusterizados = clusterize_remedios(df_medicine)
# Resultado
#print(remedios_clusterizados[["Nome", "Cluster"]])

# Função para pesquisar por nome
def search_by_name(df, nome):
    return df[df["Nome"].str.contains(nome, case=False)]

# Função para corrigir o nome digitado pelo usuário
def corrigir_nome_digitado(nome_digitado, nomes_disponiveis):
    nome_digitado = nome_digitado.lower()  # Converte para minúsculas
    nomes_disponiveis_lower = [nome.lower() for nome in nomes_disponiveis]  # Converte todos os nomes para minúsculas
    nome_corrigido, score = process.extractOne(nome_digitado, nomes_disponiveis_lower)
    return nome_corrigido, score

def get_pharmacy_id_by_product_id(search_id,df):
  pharmacy_id_list = list(df[(df['RemedioID'] == search_id) & (df['Quantidade'] > 0)]['FarmaciaID'])
  pharmacy_price_list = list(df[(df['RemedioID'] == search_id) & (df['Quantidade'] > 0)]['Preço'])
  return list(zip(pharmacy_id_list, pharmacy_price_list))
def get_pharmacy_names_by_ids(pharmacy_ids, df_pharmacy):
    nomes_das_farmacias = []

    for id in pharmacy_ids:
        # Verifique se o ID existe no DataFrame antes de acessar o nome
        filtro = df_pharmacy['ID'] == id
        if not df_pharmacy[filtro].empty:
            nome_da_farmacia = df_pharmacy.loc[filtro, 'Name'].values[0]
            nomes_das_farmacias.append(nome_da_farmacia)

    return nomes_das_farmacias



def get_user_location(api_key):
    try:
        response = requests.post(f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}")
        data = response.json()
        return (data["location"]["lat"], data["location"]["lng"])
    except Exception as e:
        print("Erro ao obter a localização:", e)
        return None

def get_nearby_pharmacies_by_ids(user_location, radius_km, pharmacies_data, pharmacy_id):
    pharmacies_with_distances = []

    for _, pharmacy in pharmacies_data.iterrows():
        pharmacy_location = (pharmacy['Latitude'], pharmacy['Longitude'])
        distance = haversine(user_location, pharmacy_location)
        if distance <= radius_km and pharmacy['ID'] in pharmacy_id:
            pharmacies_with_distances.append({"id": pharmacy['ID'], "name": pharmacy['Name'], "distance": distance})

    pharmacies_with_distances.sort(key=lambda x: x['distance'])

    return pharmacies_with_distances

def haversine(coord1, coord2):
    import math

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371  # Raio da Terra em quilômetros

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c

    return distance

# Função para capturar entrada de voz do usuário
def get_user_input():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Escolha como deseja fornecer o nome do remédio:")
        print("1. Falar (Diga 'falar')")
        print("2. Digitar (Digite 'digitar')")

        choice = input().lower()

        if choice == 'falar':
            print("Fale o nome do remédio desejado:")
            try:
                audio = recognizer.listen(source, timeout=5)
                user_input = recognizer.recognize_google(audio, language='pt-BR', show_all=True)
                if 'alternative' in user_input:
                    # Obtém a palavra reconhecida com maior confiança
                    recognized_word = user_input['alternative'][0]['transcript']
                    print(f"Entendi: {recognized_word}")  # Mostra a palavra reconhecida
                    return recognized_word
                return None
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
        elif choice == 'digitar':
            print("Digite o nome do remédio desejado:")
            return input()
        else:
            print("Escolha inválida. Escolha 'falar' ou 'digitar'.")
            return None

def main():
    # Solicita ao usuário o nome do remédio desejado
    nome_remedio_desejado = get_user_input()
    nomes_disponiveis = remedios_clusterizados["Nome"].tolist()

    # Verifica se o nome digitado ou falado corresponde exatamente a um nome na tabela (insensível a maiúsculas e minúsculas)
    if nome_remedio_desejado and nome_remedio_desejado.lower() in [nome.lower() for nome in nomes_disponiveis]:
        resultado_nome = search_by_name(remedios_clusterizados, nome_remedio_desejado)

        print("Pesquisa por Nome:")
        print(resultado_nome.drop("Cluster", axis=1))
    else:
        nome_corrigido, score = corrigir_nome_digitado(nome_remedio_desejado, nomes_disponiveis)

        if nome_remedio_desejado.lower() != nome_corrigido.lower():
            # Verifica se o nome corrigido é diferente do nome digitado ou falado
            while True:
                print(f"Você quis dizer '{nome_corrigido}'? (S/N)")
                resposta = input().lower()

                if resposta == 's':
                    # Resultado
                    resultado_nome = search_by_name(remedios_clusterizados, nome_corrigido)
                    print("Pesquisa por Nome:")
                    print(resultado_nome.drop("Cluster", axis=1)[["Nome", "Descrição", "Forma de Uso", "Efeitos Colaterais"]].to_string(index=False))
                    break
                elif resposta == 'n':
                    nome_remedio_desejado = get_user_input()
                    nome_corrigido, score = corrigir_nome_digitado(nome_remedio_desejado, nomes_disponiveis)
                else:
                    print("Resposta inválida. Responda S para Sim e N para Não.")
        else:
            # Nome reconhecido corretamente, apenas mostrar o resultado
            resultado_nome = search_by_name(remedios_clusterizados, nome_remedio_desejado)
            print("Pesquisa por Nome:")
            print(resultado_nome.drop("Cluster", axis=1)[["Nome", "Descrição", "Forma de Uso", "Efeitos Colaterais"]].to_string(index=False))


    pharmacy_ids_prices = get_pharmacy_id_by_product_id(resultado_nome['ID'].iloc[0],df)
    pharmacy_ids = map(lambda x: x[0], pharmacy_ids_prices)
    nomes_farmácias = get_pharmacy_names_by_ids(pharmacy_ids, df_pharmacy)
    resposta = map(lambda x, y: f'{x} R${y[1]}', nomes_farmácias, pharmacy_ids_prices)

    if nomes_farmácias:
        print(f"\nEsse remédio pode ser encontrado na(s) seguinte(s) farmácia(s): {', '.join(resposta)}")
    else:
        print("\nNenhuma farmácia encontrada com esse remédio")
    api_key = 'AIzaSyApThPkV_jw1ErOzFYNMWS626vu_-9Sd2s'
    user_location = get_user_location(api_key)

    if user_location:
        radius_km = 5 # Defina o raio desejado em quilômetros

        try:
            pharmacies_data = pd.read_excel("Farmácias.xlsx")  # Certifique-se de que o arquivo está no mesmo diretório do código
        except FileNotFoundError:
            print("O arquivo Farmácias.xlsx não foi encontrado.")
            return

        pharmacies = get_nearby_pharmacies_by_ids(user_location, radius_km, pharmacies_data,pharmacy_ids)

        if pharmacies:
            print("\nFarmácias encontradas dentro do raio:")
            for idx, pharmacy in enumerate(pharmacies, start=1):
                print(f"{idx}. {pharmacy['name']} - Distância: {pharmacy['distance']:.2f} km")

        else:
            print("Nenhuma farmácia encontrada dentro do raio.")
    else:
        print("Não foi possível obter sua localização.")





if __name__ == "__main__":
    main()

