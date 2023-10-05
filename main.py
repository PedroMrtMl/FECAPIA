from reconhecimento import find_name
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/remedio',methods=['POST'])
    def get_remedio():
        try:
            data = request.get_json()
            nome = data['nome']

            if not isinstance(nome, str):
                return jsonifiy({"error": "Nome inválido"}), 400
        except:
            pass
      