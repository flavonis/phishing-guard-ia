from dotenv import load_dotenv
load_dotenv() 

import os
import hashlib
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS 

from google import genai
from google.genai import types


client = None
try:
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não está configurada no .env")
        
    client = genai.Client(api_key=api_key)
except Exception as e:
    print(f"ERRO DE CONFIGURAÇÃO DA IA: Não foi possível inicializar o cliente Gemini. Detalhe: {e}")
    

app = Flask(__name__)
CORS(app) 


@app.route('/', methods=['GET'])
def home():
    return jsonify({"status": "Servidor PhishingGuard AI está online!"})



def check_password_pwned(password):
   
    sha1password = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
    
    
    prefix = sha1password[:5]
    suffix = sha1password[5:]
    
    
    url = f'https://api.pwnedpasswords.com/range/{prefix}'
    
    
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(f'Erro ao buscar a API do HIBP: Status {response.status_code}')

    
    hashes = (line.split(':') for line in response.text.splitlines())
    
    for h, count in hashes:
        if h == suffix:
            return int(count)
    return 0 



def generate_security_recommendation(password, count_pwned):
    if not client:
        return "Módulo de IA indisponível. Recomendações: Troque sua senha imediatamente e ative 2FA."
    
    
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



@app.route('/check-password', methods=['POST'])
def check_password():
    data = request.get_json()
    password = data.get('credential') 
    
    if not password:
        return jsonify({"error": "Senha não fornecida."}), 400

    try:
        count = check_password_pwned(password)
        
        if count > 0:
            
            recommendation_text = generate_security_recommendation(password, count)
            
            
            return jsonify({
                "status": "compromised",
                "is_compromised": True,
                "count": count,
                "message": f"SUA SENHA FOI COMPROMETIDA. Foi encontrada em {count} vazamentos de dados públicos.",
                "recommendation": recommendation_text 
            })
        else:
            
            return jsonify({
                "status": "secure",
                "is_compromised": False,
                "count": 0,
                "message": "A senha não foi encontrada em vazamentos conhecidos. Parabéns!",
                "recommendation": "Lembre-se de manter as boas práticas: use sempre senhas únicas e ative a autenticação de dois fatores (2FA) em todos os serviços importantes."
            })
            
    except Exception as e:
        
        return jsonify({"error": "Ocorreu um erro interno no servidor.", "details": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)   
