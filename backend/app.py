from dotenv import load_dotenv
load_dotenv() 

import os
import hashlib
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS 

from google import genai
from google.genai import types

# Inicialização do Cliente Gemini (Lê a chave do .env)
client = None
try:
    # Obtém a chave da variável de ambiente
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não está configurada no .env")
        
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"ERRO DE CONFIGURAÇÃO DA IA: Não foi possível inicializar o cliente Gemini. Detalhe: {e}")
    
# Configuração do Servidor Flask
app = Flask(__name__)
CORS(app) 

# Rota de teste
@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Servidor PhishingGuard AI está online!"})

# app.py - Parte 2: Lógica de Checagem Segura (HIBP)

def check_password_pwned(password):
    # 1. Gera o hash SHA-1 da senha
    sha1password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    # 2. Separa o prefixo (5 primeiros caracteres) e o sufixo
    prefix = sha1password[:5]
    suffix = sha1password[5:]
    
    # URL da API do HIBP (Consulta o prefixo)
    url = f'https://api.pwnedpasswords.com/range/{prefix}'
    
    # Faz a requisição à API
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Erro ao buscar a API do HIBP: Status {response.status_code}')

    # Procura o sufixo na resposta
    hashes = (line.split(':') for line in response.text.splitlines())
    
    for h, count in hashes:
        if h == suffix:
            return int(count)
    return 0 

# app.py - Parte 3: Lógica da IA (Geração de Recomendações)

def generate_security_recommendation(password, count_pwned):
    if not client:
        return "Módulo de IA indisponível. Recomendações: Troque sua senha imediatamente e ative 2FA."
    
    # O Ponto-Chave: O Prompt Engineering
    prompt = f"""
    Sua função é atuar como um especialista em cibersegurança, adotando um tom sério, mas acessível.
    A seguinte senha foi encontrada em {count_pwned} vazamentos de dados públicos.
    
    Gere um parágrafo (máximo 4 frases) com:
    1. Uma descrição formal e de alto risco da situação.
    2. Duas recomendações imediatas e específicas de segurança (ex: trocar a senha, usar 2FA, usar gerenciador de senhas).
    3. Uma frase final de alerta sobre a reutilização de senhas.
    
    A resposta deve ser clara, focada em mitigar o risco de 'account takeover' e não deve ter formatações adicionais (listas, títulos).
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    
    except Exception as e:
        print(f"Erro na chamada da API do Gemini: {e}")
        return "Não foi possível gerar as recomendações automáticas devido a um erro de comunicação. Siga as recomendações manuais: troque sua senha e use 2FA."

# app.py - Parte 4: Rota Principal

@app.route('/check-password', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('credential') 
    
    if not password:
        return jsonify({"error": "Senha não fornecida."}), 400

    try:
        count = check_password_pwned(password)
        
        if count > 0:
            # --- CHAMA A IA ---
            recommendation_text = generate_security_recommendation(password, count)
            # --- FIM IA ---
            
            return jsonify({
                "status": "compromised",
                "is_compromised": True,
                "count": count,
                "message": f"SUA SENHA FOI COMPROMETIDA. Foi encontrada em {count} vazamentos de dados públicos.",
                "recommendation": recommendation_text 
            })
        else:
            # Resposta para senhas seguras
            return jsonify({
                "status": "secure",
                "is_compromised": False,
                "count": 0,
                "message": "A senha não foi encontrada em vazamentos conhecidos. Parabéns!",
                "recommendation": "Lembre-se de manter as boas práticas: use sempre senhas únicas e ative a autenticação de dois fatores (2FA) em todos os serviços importantes."
            })
            
    except Exception as e:
        # Erro geral de processamento
        return jsonify({"error": "Ocorreu um erro interno no servidor.", "details": str(e)}), 500

# Adicione esta linha no final do seu app.py (Se ainda não tiver)
if __name__ == '__main__':
    app.run(debug=True, port=5000)   
