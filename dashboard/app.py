#!/usr/bin/env python3
"""
Dashboard Web para o Bot Garimpeiro Geek
Aplicação Flask para visualizar e administrar as ofertas publicadas pelo bot.
"""

import sys
import os
from datetime import datetime
from flask import Flask, render_template
import sqlite3
from typing import List, Dict, Any

# Adiciona o diretório raiz ao path para importar módulos do projeto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importa o módulo database do projeto principal
try:
    import database
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Aviso: Não foi possível importar o módulo database: {e}")
    DATABASE_AVAILABLE = False

app = Flask(__name__)

def get_ofertas_recentes() -> List[Dict[str, Any]]:
    """
    Obtém as 50 ofertas mais recentes do banco de dados.
    
    Returns:
        Lista de dicionários com os dados das ofertas
    """
    if not DATABASE_AVAILABLE:
        return []
    
    try:
        # Conecta ao banco de dados (caminho relativo ao diretório raiz)
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Consulta para obter todas as colunas das 50 ofertas mais recentes
        cursor.execute('''
            SELECT * FROM ofertas 
            ORDER BY data_postagem DESC 
            LIMIT 50
        ''')
        
        # Obtém os nomes das colunas
        colunas = [desc[0] for desc in cursor.description]
        
        ofertas = []
        for row in cursor.fetchall():
            oferta = dict(zip(colunas, row))
            ofertas.append(oferta)
        
        conn.close()
        return ofertas
        
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return []

def formatar_data(data_str: str) -> str:
    """
    Formata a data para exibição mais amigável.
    
    Args:
        data_str: String da data no formato do banco
        
    Returns:
        Data formatada para exibição
    """
    try:
        if not data_str:
            return "Data não disponível"
        
        # Tenta diferentes formatos de data
        for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S']:
            try:
                dt = datetime.strptime(data_str, fmt)
                return dt.strftime('%d/%m/%Y %H:%M')
            except ValueError:
                continue
        
        return data_str
    except Exception:
        return data_str

def formatar_preco(preco) -> str:
    """
    Formata o preço para exibição em reais.
    
    Args:
        preco: Valor do preço (pode ser string ou float)
        
    Returns:
        Preço formatado em reais
    """
    try:
        if preco is None:
            return "Preço não disponível"
        
        # Se for string, remove vírgulas e converte para float
        if isinstance(preco, str):
            preco = preco.replace(',', '.')
        
        preco_float = float(preco)
        return f"R$ {preco_float:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return "Preço não disponível"

def get_total_ofertas() -> int:
    """
    Retorna o número total de ofertas na tabela.
    
    Returns:
        Número total de ofertas
    """
    if not DATABASE_AVAILABLE:
        return 0
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM ofertas')
        total = cursor.fetchone()[0]
        
        conn.close()
        return total
        
    except Exception as e:
        print(f"Erro ao obter total de ofertas: {e}")
        return 0

def get_ofertas_hoje() -> int:
    """
    Retorna o número de ofertas adicionadas nas últimas 24 horas.
    
    Returns:
        Número de ofertas de hoje
    """
    if not DATABASE_AVAILABLE:
        return 0
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        hoje = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM ofertas WHERE DATE(data_postagem) = ?', (hoje,))
        total = cursor.fetchone()[0]
        
        conn.close()
        return total
        
    except Exception as e:
        print(f"Erro ao obter ofertas de hoje: {e}")
        return 0

def get_lojas_ativas() -> List[Dict[str, Any]]:
    """
    Retorna uma lista de lojas únicas com a contagem de ofertas para cada uma.
    
    Returns:
        Lista de dicionários com nome da loja e contagem
    """
    if not DATABASE_AVAILABLE:
        return []
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT loja, COUNT(*) as contagem 
            FROM ofertas 
            WHERE loja IS NOT NULL 
            GROUP BY loja 
            ORDER BY contagem DESC
        ''')
        
        lojas = []
        for row in cursor.fetchall():
            lojas.append({
                'nome': row[0] or 'Loja não identificada',
                'contagem': row[1]
            })
        
        conn.close()
        return lojas
        
    except Exception as e:
        print(f"Erro ao obter lojas ativas: {e}")
        return []

def get_preco_medio() -> float:
    """
    Retorna o preço médio de todas as ofertas.
    
    Returns:
        Preço médio das ofertas
    """
    if not DATABASE_AVAILABLE:
        return 0.0
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT preco FROM ofertas WHERE preco IS NOT NULL')
        precos = cursor.fetchall()
        
        if not precos:
            conn.close()
            return 0.0
        
        # Converte preços para float
        precos_float = []
        for (preco,) in precos:
            try:
                if isinstance(preco, str):
                    preco_limpo = preco.replace(',', '.')
                    precos_float.append(float(preco_limpo))
                else:
                    precos_float.append(float(preco))
            except (ValueError, TypeError):
                continue
        
        conn.close()
        
        if not precos_float:
            return 0.0
        
        return round(sum(precos_float) / len(precos_float), 2)
        
    except Exception as e:
        print(f"Erro ao obter preço médio: {e}")
        return 0.0

def get_estatisticas_gerais() -> Dict[str, Any]:
    """
    Obtém estatísticas gerais sobre as ofertas.
    
    Returns:
        Dicionário com estatísticas
    """
    if not DATABASE_AVAILABLE:
        return {}
    
    try:
        db_path = os.path.join(os.path.dirname(__file__), '..', 'ofertas.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total de ofertas
        cursor.execute('SELECT COUNT(*) FROM ofertas')
        total_ofertas = cursor.fetchone()[0]
        
        # Ofertas de hoje
        hoje = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('SELECT COUNT(*) FROM ofertas WHERE DATE(data_postagem) = ?', (hoje,))
        ofertas_hoje = cursor.fetchone()[0]
        
        # Lojas únicas
        cursor.execute('SELECT COUNT(DISTINCT loja) FROM ofertas')
        total_lojas = cursor.fetchone()[0]
        
        # Preço médio, máximo e mínimo
        cursor.execute('SELECT preco FROM ofertas WHERE preco IS NOT NULL')
        precos = cursor.fetchall()
        
        precos_float = []
        for (preco,) in precos:
            try:
                if isinstance(preco, str):
                    preco_limpo = preco.replace(',', '.')
                    precos_float.append(float(preco_limpo))
                else:
                    precos_float.append(float(preco))
            except (ValueError, TypeError):
                continue
        
        if precos_float:
            preco_medio = sum(precos_float) / len(precos_float)
            preco_max = max(precos_float)
            preco_min = min(precos_float)
        else:
            preco_medio = preco_max = preco_min = 0
        
        conn.close()
        
        return {
            'total_ofertas': total_ofertas,
            'ofertas_hoje': ofertas_hoje,
            'total_lojas': total_lojas,
            'preco_medio': round(float(preco_medio), 2) if preco_medio else 0,
            'preco_max': round(float(preco_max), 2) if preco_max else 0,
            'preco_min': round(float(preco_min), 2) if preco_min else 0
        }
        
    except Exception as e:
        print(f"Erro ao obter estatísticas: {e}")
        return {}

@app.route('/')
def index():
    """
    Rota principal que exibe o dashboard com as ofertas.
    """
    ofertas = get_ofertas_recentes()
    estatisticas = get_estatisticas_gerais()
    
    # Formata os dados para exibição
    for oferta in ofertas:
        oferta['data_formatada'] = formatar_data(oferta['data_postagem'])
        oferta['preco_formatado'] = formatar_preco(oferta['preco'])
        
        # Calcula o desconto se houver preço original
        try:
            if oferta.get('preco_original') and oferta.get('preco'):
                preco_atual_str = str(oferta['preco']).replace(',', '.')
                preco_orig_str = str(oferta['preco_original']).replace(',', '.')
                
                preco_atual = float(preco_atual_str)
                preco_orig = float(preco_orig_str)
                
                if preco_orig > preco_atual:
                    desconto = int(((preco_orig - preco_atual) / preco_orig) * 100)
                    oferta['desconto_formatado'] = f"{desconto}%"
                else:
                    oferta['desconto_formatado'] = "N/A"
            else:
                oferta['desconto_formatado'] = "N/A"
        except (ValueError, TypeError):
            oferta['desconto_formatado'] = "N/A"
        
        # Usa a fonte como avaliação (já que não temos avaliação real)
        oferta['fonte_formatada'] = oferta.get('fonte') or "N/A"
    
    return render_template('index.html', 
                         ofertas=ofertas, 
                         total_ofertas=len(ofertas),
                         estatisticas=estatisticas)

@app.route('/health')
def health_check():
    """
    Rota para verificar a saúde da aplicação.
    """
    return {
        'status': 'healthy',
        'database_available': DATABASE_AVAILABLE,
        'timestamp': datetime.now().isoformat()
    }

@app.route('/lojas')
def lojas():
    """
    Rota para exibir detalhes das lojas ativas.
    """
    lojas_ativas = get_lojas_ativas()
    total_lojas = len(lojas_ativas)
    
    return render_template('lojas.html', 
                         lojas=lojas_ativas, 
                         total_lojas=total_lojas)

@app.route('/ofertas-hoje')
def ofertas_hoje():
    """
    Rota para exibir ofertas das últimas 24 horas.
    """
    ofertas = get_ofertas_recentes()
    
    # Filtra apenas ofertas de hoje
    hoje = datetime.now().strftime('%Y-%m-%d')
    ofertas_hoje = []
    
    for oferta in ofertas:
        if oferta.get('data_postagem') and hoje in str(oferta['data_postagem']):
            # Formata os dados para exibição
            oferta['data_formatada'] = formatar_data(oferta['data_postagem'])
            oferta['preco_formatado'] = formatar_preco(oferta['preco'])
            
            # Calcula o desconto se houver preço original
            try:
                if oferta.get('preco_original') and oferta.get('preco'):
                    preco_atual_str = str(oferta['preco']).replace(',', '.')
                    preco_orig_str = str(oferta['preco_original']).replace(',', '.')
                    
                    preco_atual = float(preco_atual_str)
                    preco_orig = float(preco_orig_str)
                    
                    if preco_orig > preco_atual:
                        desconto = int(((preco_orig - preco_atual) / preco_orig) * 100)
                        oferta['desconto_formatado'] = f"{desconto}%"
                    else:
                        oferta['desconto_formatado'] = "N/A"
                else:
                    oferta['desconto_formatado'] = "N/A"
            except (ValueError, TypeError):
                oferta['desconto_formatado'] = "N/A"
            
            # Usa a fonte como avaliação
            oferta['fonte_formatada'] = oferta.get('fonte') or "N/A"
            ofertas_hoje.append(oferta)
    
    return render_template('ofertas_hoje.html', 
                         ofertas=ofertas_hoje, 
                         total_ofertas=len(ofertas_hoje))

@app.route('/estatisticas')
def estatisticas():
    """
    Rota para exibir estatísticas detalhadas.
    """
    stats = get_estatisticas_gerais()
    
    return render_template('estatisticas.html', 
                         estatisticas=stats)

if __name__ == '__main__':
    print("🚀 Iniciando Dashboard do Garimpeiro Geek...")
    print(f"📊 Banco de dados disponível: {DATABASE_AVAILABLE}")
    
    if DATABASE_AVAILABLE:
        ofertas = get_ofertas_recentes()
        print(f"📋 Total de ofertas encontradas: {len(ofertas)}")
    
    print("🌐 Acesse: http://127.0.0.1:5000")
    print("🔍 Health check: http://127.0.0.1:5000/health")
    
    app.run(debug=True, host='127.0.0.1', port=5000)
