from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_cors import cross_origin
import openai
import pandas as pd
from docx import Document
import json
import os

app = Flask(__name__)
cors = CORS(app, resources={r'/chatbot/*': {'origins':'*'}})

openai.api_key = os.getenv("OPENAIKEY")


# Função para carregar os dados (já definida anteriormente)
def carregar_dados(filepath):
    return pd.read_excel(filepath)

# Função para ler arquivo .docx e converter para DataFrame
def ler_docx_e_criar_dataframe(file_path):
    doc = Document(file_path)
    data = []
    for table in doc.tables:
        for row in table.rows:
            data.append([cell.text for cell in row.cells])
    df = pd.DataFrame(data[1:], columns=data[0])
    return df

def consultar_linha_por_ncm_uf(df, ncm, uf):
    filtro = (df['NCM'] == ncm) & (df['UF'] == uf)
    resultado = df[filtro]
    resultado_json = resultado.head(1).to_json(orient="records", force_ascii=False)
    # Converte a string JSON para um dicionário Python
    resultado_dict = json.loads(resultado_json)
    return resultado_dict


def processar_entrada_usuario(entrada_usuario):
    
    #Passo 1: Analisar a entrada do usuário com GPT-3 para extrair NCM e UF
    prompt = f"Extraia NCM e UF da seguinte pergunta: '{entrada_usuario}'"

    completion = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    
    parsed_input = completion.choices[0].message.content
    lines = parsed_input.split('\n')
    ncm_value = lines[0].replace("NCM: ", "") 
    uf_value = lines[1].replace("UF: ", "")
    
    # Carregar dados e realizar consulta
    #df = carregar_dados('aliquotas-2024-all.xlsx')
    
    # Execução da Consulta com entrada do usuário
    file_path = "ALIQUOTAS2024.docx"  # Certifique-se de que o caminho do arquivo esteja correto
    df = ler_docx_e_criar_dataframe(file_path)
    
    resultado_consulta = consultar_linha_por_ncm_uf(df, ncm_value, uf_value)
    return resultado_consulta

@app.get('/')
def index():
    return 'app renderizado'

@app.route('/chatbot/', methods=['POST'])
def chatbot():
    data = request.json
    entrada_usuario = data['mensagem']
    resposta = processar_entrada_usuario(entrada_usuario)
    return jsonify(resposta)

if __name__ == '__main__':
    app.run(debug=True)
