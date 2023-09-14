
import speech_recognition as sr
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np

# Caminho para o arquivo Excel
caminho_arquivo = 'RemédiosPortuguês.xlsx'

def clusterize_remedios(file_path, num_clusters=5):
    # Lê o arquivo Excel
    df = pd.read_excel(file_path)

    # Selecionar colunas relevantes para clusterização
    features = df[["Nome", "Descrição", "Forma de Uso", "Efeitos Colaterais", "Preço (R$)"]]

    # Pré-processamento dos textos
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf_vectorizer.fit_transform(features["Descrição"])

    # Padronizar os preços
    scaler = StandardScaler()
    price_scaled = scaler.fit_transform(features[["Preço (R$)"]])

    # Combinar os dados transformados
    combined_features = np.hstack((tfidf_matrix.toarray(), price_scaled))

    # Clusterização com K-means
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    df["Cluster"] = kmeans.fit_predict(combined_features)

    return df

# Clusteriza os remédios
remedios_clusterizados = clusterize_remedios(caminho_arquivo)
# Resultado
print(remedios_clusterizados[["Nome", "Cluster"]])


# Função para pesquisar por nome
def search_by_name(df, nome):
    return df[df["Nome"].str.contains(nome, case=False)]

# Função para corrigir o nome digitado pelo usuário
def corrigir_nome_digitado(nome_digitado, nomes_disponiveis):
    nome_digitado = nome_digitado.lower()  # Converte para minúsculas
    nomes_disponiveis_lower = [nome.lower() for nome in nomes_disponiveis]  # Converte todos os nomes para minúsculas
    nome_corrigido, score = process.extractOne(nome_digitado, nomes_disponiveis_lower)
    return nome_corrigido, score


# Função para capturar entrada de voz do usuário
def get_user_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Fale o nome do remédio desejado:")
        try:
            audio = recognizer.listen(source, timeout=5)
            user_input = recognizer.recognize_google(audio, language='pt-BR')
            return user_input
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None

# Captura o nome do remédio por voz e aplica correção se necessário
while True:
    nome_remedio_desejado = get_user_input()

    if nome_remedio_desejado:
        nome_corrigido, score = corrigir_nome_digitado(nome_remedio_desejado, remedios_clusterizados["Nome"].tolist())

        print(f"Você disse: '{nome_remedio_desejado}'.")
        print(f"Você quis dizer: '{nome_corrigido}'? (S/N)")
        resposta = input().lower()

        if resposta == 's':
            break
    else:
        print("Não foi possível capturar a fala. Tente novamente.")

# Resultado
resultado_nome = search_by_name(remedios_clusterizados, nome_corrigido)
print("Pesquisa por Nome:")
print(resultado_nome.drop("Cluster", axis=1))
