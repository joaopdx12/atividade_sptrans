import os
import requests
import folium
from dotenv import load_dotenv

load_dotenv(".env")

URL_BASE = "http://api.olhovivo.sptrans.com.br/v2.1"
LINHA_DOS_SLIDES = 2506  

s = requests.Session()
res = s.post(f"{URL_BASE}/Login/Autenticar?token={os.getenv('SPTRANS_TOKEN')}")

if res.text != "true":
    print("Não consegui autenticar. Confira o SPTRANS_TOKEN no arquivo .env")
    raise SystemExit

print("Autenticado com sucesso!")

res = s.get(f"{URL_BASE}/Linha/Buscar?termosBusca=Lapa")
linhas = res.json()
print(f"Encontrei {len(linhas)} linhas")

codigo_linha = None
nome_linha = ""
onibus = []

for linha in linhas[:15]:
    if linha["cl"] == LINHA_DOS_SLIDES:
        continue

    res = s.get(f"{URL_BASE}/Posicao/Linha?codigoLinha={linha['cl']}")
    dados = res.json()

    if dados.get("vs"):
        codigo_linha = linha["cl"]
        nome_linha = f"{linha['lt']} - {linha['tp']} / {linha['ts']}"
        onibus = dados["vs"]
        break

if codigo_linha is None:
    print("Nenhuma linha com ônibus em circulação agora. Tente mais tarde.")
    raise SystemExit

print(f"Linha escolhida: {nome_linha} (código {codigo_linha})")
print(f"Ônibus em circulação: {len(onibus)}")

res = s.get(f"{URL_BASE}/Parada/BuscarParadasPorLinha?codigoLinha={codigo_linha}")
paradas = res.json()
print(f"Paradas encontradas: {len(paradas)}")

m = folium.Map(location=[paradas[0]["py"], paradas[0]["px"]], zoom_start=13)

for parada in paradas:
    folium.Marker(
        location=[parada["py"], parada["px"]],
        popup=parada["np"],
        icon=folium.Icon(color="blue", icon="info-sign"),
    ).add_to(m)

for bus in onibus:
    folium.Marker(
        location=[bus["py"], bus["px"]],
        popup=f"Ônibus {bus['p']}",
        icon=folium.Icon(color="red", icon="bus", prefix="fa"),
    ).add_to(m)

m.save("mapa_onibus.html")
print("Mapa salvo em mapa_onibus.html")