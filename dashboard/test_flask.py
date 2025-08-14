#!/usr/bin/env python3
"""
Teste simples do Flask
"""

from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, Flask is working!'

@app.route('/test')
def test():
    return 'Test endpoint working!'

if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask de teste...")
    print("🌐 Acesse: http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=False)
