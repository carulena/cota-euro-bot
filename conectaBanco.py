import os
from zoneinfo import ZoneInfo
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
URI = os.environ.get("URI_MONGO_DB")
cliente = MongoClient(URI, serverSelectionTimeoutMS=5000)
TZ_BRASIL = ZoneInfo("America/Sao_Paulo")
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
        
def insereDados(data: datetime, valor, colecao):
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
    try:
        agora = datetime.now(TZ_BRASIL)
        inicio = agora - timedelta(days=dias)
        
        resultados = db[colecao].find({
            "dataHora": {
                "$gte": inicio,
                "$lte": agora
            }
        }).sort("data", 1)
        return pd.DataFrame(list(resultados))
    except Exception as e:
        print("Erro de conexão:", e)
        
def gerar_grafico_euro(df, caminho="euro.png"):
    df["dataHora"] = pd.to_datetime(df["dataHora"], utc=True, dayfirst=True)
    df["dataHora"] = df["dataHora"].dt.tz_convert(TZ_BRASIL)
    df["valor"] = pd.to_numeric(df["valor"]).round(3)
    plt.figure(figsize=(20, 5))
    plt.plot(df["dataHora"], df["valor"], marker="o")
    ax = plt.gca() 
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m - %H:%M"))
    plt.xticks(df["dataHora"], rotation=45)
    plt.xlabel("Data")
    plt.ylabel("Euro (R$)")
    plt.title(f"Cotação do Euro")
    plt.gca().yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))
    for x, y in zip(df["dataHora"], df["valor"]):
        plt.annotate(f"R${y:.3f}", xy=(x, y), xytext=(0,5),textcoords="offset points", ha='center')
    plt.tight_layout()
    plt.savefig(caminho)
    plt.close()    
        
def colecao_tem_dados(colecao):
    return db[colecao].find_one() is not None