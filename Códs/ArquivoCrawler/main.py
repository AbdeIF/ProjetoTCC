# Cabeçalho
"""
Este script coleta comentários de produtos da Amazon e Mercado Livre, os traduz para o inglês e realiza uma análise de sentimentos neles.
"""

# Imports
from urllib.request import urlopen
from bs4 import BeautifulSoup
from textblob import TextBlob
from googletrans import Translator
import requests
import json

# Configuration dictionary to map site URLs to CSS classes
site_configs = {
  #Amazon
  "https://www.amazon.com.br/": {
    "class_teg": "span",
    "title_teg": "a",
    "title_class": "a-link-normal",
    "review_class": "a-size-base review-text review-text-content"
  },
  #Mercado Livre
  "https://www.mercadolivre.com.br/": {
    "class_teg": "p",
    "title_teg": "h1",
    "title_class": "ui-pdp-title",
    "review_class": "ui-review-capability-comments__comment__content"
  },
}

# Define the list of URLs to analyze
urls = [
  #Amazon
  "https://www.amazon.com.br/Controle-Dualshock-PlayStation-4-Preto/product-reviews/B07FN1MZBH/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
  "https://www.amazon.com.br/Max-Titanium-1-Creatina-300gr/product-reviews/B07DVJC66X/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
  "https://www.amazon.com.br/Olympikus-ULTRALEVE-T%C3%AAnis-Masculino-Marinho/product-reviews/B09CHJPK4F/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
  "https://www.amazon.com.br/Intelig%C3%AAncia-social-ci%C3%AAncia-revolucion%C3%A1ria-rela%C3%A7%C3%B5es-ebook/product-reviews/B07T1DFVRS/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
  "https://www.amazon.com.br/Doce-Leite-Pastoso-Souvenir-800Gr/product-reviews/B08T7J418Y/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
  #Mercado Livre
  "https://www.mercadolivre.com.br/cerveja-heineken-premium-puro-malte-350ml-caixa-12-unidades/p/MLB19535785#reviews",
  "https://www.mercadolivre.com.br/xiaomi-mi-smart-band-5-11-caixa-de-plastico-pc-preta-pulseira-black-xmsh10hm/p/MLB15963018#reviews",
  "https://www.mercadolivre.com.br/coturnos-de-sintetico-cano-curto-moleca-5338103-design-liso-preto-01preto-01-39-br-para-feminino/p/MLB19061227#reviews",
  "https://www.mercadolivre.com.br/fone-de-ouvido-on-ear-sem-fio-jbl-tune-520bt-blt520bt/p/MLB23238148?pdp_filters=deal:MLB779362-1&hide_psmb=true#reviews",
  "https://www.mercadolivre.com.br/air-fryer-35-litros-com-visor-digital-mondial-1500w-fritadeira-eletrica-sem-oleo-af-30-di-preto-com-cinza-para-cozinhar-fritar-e-assar-alimentos-como-batata-frita-frango-carnes/p/MLB19768380?pdp_filters=deal:MLB779362-1&hide_psmb=true#reviews",
]


# Função para verificar se uma avaliação já existe na lista de avaliações
def avaliacao_existe(avaliacao, lista_avaliacoes):
  for item in lista_avaliacoes:
    if item["Avaliação"] == avaliacao:
      return True
  return False


# Lista para armazenar as avaliações
avaliacoes = []

# Contadores para as avaliações
positivas = 0
negativas = 0
neutras = 0

# Carrega o conteúdo atual do arquivo JSON, se existir
try:
  with open("avaliacoes.json", "r", encoding="utf-8") as file:
    avaliacoes_existentes = json.load(file)
except FileNotFoundError:
  avaliacoes_existentes = []

# Cria um loop para coletar as avaliações de cada URL
for url in urls:
  try:
    # Verifica se o site está disponível
    requests.get(url)
  except requests.exceptions.RequestException as e:
    print(f"Erro: {e}")
    continue

  # Abre a página da URL e coleta o HTML
  html = urlopen(url)

  # Cria um objeto BeautifulSoup para realizar a análise do HTML
  soup = BeautifulSoup(html, "html.parser")

  # Find site-specific configuration based on the URL
  site_config = next(
    (config for site, config in site_configs.items() if site in url), None)

  if not site_config:
    print(f"Configuração para o site {url} não encontrada.")
    continue

  # Encontra o título do produto
  titulo = soup.find(site_config["title_teg"],
                     {"class": site_config["title_class"]})
  nome_produto = titulo.get_text(
    strip=True) if titulo else "Título não encontrado"

  # Adicionando a informação da loja correspondente às avaliações
  loja = next(
    (loja for loja, config in site_configs.items() if site_config == config),
    None)

  # Encontra as avaliações do produto na página usando uma classe CSS específica
  comentarios = soup.find_all(site_config["class_teg"],
                              {"class": site_config["review_class"]})

  # Cria um loop para analisar cada avaliação
  for comentario in comentarios:
    # Extrai o texto do parágrafo dentro da avaliação
    texto = comentario.get_text(strip=True)

    # Verifica se a avaliação já existe na lista de avaliações
    if avaliacao_existe(texto, avaliacoes_existentes):
      continue

    # Traduzindo texto
    tradutor = Translator()
    try:
      texto_traduzido = tradutor.translate(str(texto), dest="en")
    except Exception as e:
      print(f"Erro na tradução: {e}")
      continue

    # Realiza a análise de sentimentos usando o TextBlob
    sentiment = TextBlob(texto_traduzido.text).sentiment

    # Dicionário para armazenar a avaliação
    avaliacao = {
      "loja": loja,  # Adiciona a informação da loja à avaliação
      "produto": nome_produto,
      "Avaliação": str(texto),
      "sentimento": sentiment.polarity,
      "emoção": sentiment.subjectivity
    }

    # Adiciona a avaliação à lista de avaliações
    avaliacoes.append(avaliacao)

    # Incrementa os contadores com base na polaridade da avaliação
    if sentiment.polarity > 0:
      positivas += 1
    elif sentiment.polarity < 0:
      negativas += 1
    else:
      neutras += 1

    # Imprime o resultado da análise
    print("Loja: ", loja)
    print("Produto: ", nome_produto)
    print("Avaliação: ", texto)
    print("Sentimento: ", sentiment.polarity)
    print("Emoção: ", sentiment.subjectivity)
    print("----------------------------------")

# Combinar as avaliações existentes com as novas avaliações
avaliacoes_atualizadas = avaliacoes_existentes + avaliacoes

# Salva as avaliações atualizadas no arquivo JSON
with open("avaliacoes.json", "w", encoding="utf-8") as file:
  json.dump(avaliacoes_atualizadas, file, ensure_ascii=False, indent=2)

# Imprime o total de avaliações positivas, negativas e neutras
print("Total de avaliações positivas:", positivas)
print("Total de avaliações negativas:", negativas)
print("Total de avaliações neutras:", neutras)
