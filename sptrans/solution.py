import os
import requests
import folium
from dotenv import load_dotenv

# Procura o .env ao lado do script ou na subpasta usada para guardar a configuracao.
pasta_do_script = os.path.dirname(os.path.abspath(__file__))
arquivos_env = [
    os.path.join(pasta_do_script, ".env"),
    os.path.join(pasta_do_script, "Nova pasta", ".env"),
]
arquivo_env = next((caminho for caminho in arquivos_env if os.path.isfile(caminho)), None)
if arquivo_env:
    load_dotenv(arquivo_env)

# A SPTrans passou a usar HTTPS (com http o POST pode ser redirecionado e falhar)
URL_BASE = "https://api.olhovivo.sptrans.com.br/v2.1"
LINHA_DOS_SLIDES = 2506  

token = os.getenv("SPTRANS_TOKEN", "").strip()

if not token:
    print("Não encontrei SPTRANS_TOKEN no ambiente ou nos arquivos .env esperados:")
    for caminho in arquivos_env:
        print(f"- {caminho}")
    raise SystemExit

s = requests.Session()
res = s.post(f"{URL_BASE}/Login/Autenticar", params={"token": token})

if res.text.strip().lower() != "true":
    print("Não consegui autenticar.")
    print("Status HTTP:", res.status_code)
    print("Resposta da SPTrans:", res.text[:200])
    raise SystemExit

print("Autenticado com sucesso!")

res = s.get(f"{URL_BASE}/Linha/Buscar?termosBusca=Lapa")
linhas = res.json()
print(f"Encontrei {len(linhas)} linhas")

codigo_linha = None
nome_linha = ""
onibus = []
paradas = []

# Pego a primeira linha (diferente da dos slides) que tenha ônibus rodando
# E paradas cadastradas, porque algumas linhas vêm vazias da API
for linha in linhas[:30]:
    if linha["cl"] == LINHA_DOS_SLIDES:
        continue

    res = s.get(f"{URL_BASE}/Posicao/Linha?codigoLinha={linha['cl']}")
    veiculos = res.json().get("vs") or []
    if not veiculos:
        continue

    res = s.get(f"{URL_BASE}/Parada/BuscarParadasPorLinha?codigoLinha={linha['cl']}")
    lista_paradas = res.json()
    if not lista_paradas:
        continue

    codigo_linha = linha["cl"]
    nome_linha = f"{linha['lt']} - {linha['tp']} / {linha['ts']}"
    onibus = veiculos
    paradas = lista_paradas
    break

if codigo_linha is None:
    print("Nenhuma linha com ônibus e paradas agora. Tente mais tarde.")
    raise SystemExit

print(f"Linha escolhida: {nome_linha} (código {codigo_linha})")
print(f"Ônibus em circulação: {len(onibus)}")
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