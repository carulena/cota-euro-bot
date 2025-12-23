import os
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import pandas as pd

URI = os.environ.get("URI_MONGO_DB")
cliente = MongoClient(URI, serverSelectionTimeoutMS=5000)

db = cliente['CotaEuro_servehope']

def criaColecao(nome):
    try: 
        if(nome not in db.list_collection_names()):
            #Cria EuroHora
            db.create_collection(
                nome,
                validator={
                    "$jsonSchema": {
                        "bsonType": "object",
                        "required": ["dataHora", "valor"],
                        "properties": {
                            "dataHora": {
                                "bsonType": "date",
                                "description": "dataHora deve ser Date"
                            },
                            "valor": {
                                "bsonType": "number",
                                "description": "valor deve ser um numero"
                            }
                        }
                    }
                }
            )
        print(f"a colecao {nome} está criada" )
    
    except Exception as e:
        print("Erro de conexão:", e)
        
def insereDados(data, valor, colecao):
    try: 
        cl = db[colecao]
        
        dados = {
            "dataHora": data,
            "valor": valor
        }
        
        resultado = cl.insert_one(dados)
        print("Documento inserido com _id:", resultado.inserted_id)
    except Exception as e:
        print("Erro de conexão:", e)
        
        
def deletaDados():
    try: 
        if db.euroHora.count_documents({}) > 0:
            db.euroHora.delete_many({})
            print("Coleção limpa com sucesso")
        else:
            print("Coleção já está vazia")
            
    except Exception as e:
        print("Erro de conexão:", e)
        
                
def criaRelatorio(dias, colecao):
    agora = datetime.now(timezone.utc)
    inicio = agora - timedelta(days=dias)
    
    resultados = db[colecao].find({
        "dataHora": {
            "$gte": inicio,
            "$lte": agora
        }
    }).sort("data", 1)
    return pd.DataFrame(list(resultados))
    
        
def colecao_tem_dados(colecao):
    return db[colecao].find_one() is not None