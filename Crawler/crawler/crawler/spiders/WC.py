import scrapy
from textblob import TextBlob
from googletrans import Translator
import json

class WcSpider(scrapy.Spider):
    name = "WC"
    # allowed_domains = ["amazon.com.br", "mercadolivre.com.br"]
    start_urls = [
        "https://www.amazon.com.br/Adaptador-Notebook-Ideapad-Conector-Compat%C3%ADvel/product-reviews/B0BKKJ614C/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews",
        "https://www.mercadolivre.com.br/cerveja-heineken-premium-puro-malte-350ml-caixa-12-unidades/p/MLB19535785?pdp_filters=deal:MLB19162#reviews",
    ]

    def parse(self, response):
        # Extract site-specific configuration based on the URL
        site_config = self.get_site_config(response.url)

        if not site_config:
            self.logger.error(f"Configuração para o site {response.url} não encontrada.")
            return

        # Extract the product title
        title_teg = response.css(site_config["title_teg"] + "." + site_config["title_class"])
        nome_produto = title_teg.get() if title_teg else "Título não encontrado"

        # Extract product reviews using the specific CSS class
        comentarios = response.css(site_config["class_teg"] + "." + site_config["review_class"])

        # Loop through each review
        for comentario in comentarios:
            # Extract the text of the review
            texto = comentario.get()

            # Check if the review already exists in the list of existing reviews
            if self.avaliacao_existe(texto):
                continue

            # Translate the text to English
            tradutor = Translator()
            try:
                texto_traduzido = tradutor.translate(texto, dest="en").text
            except Exception as e:
                self.logger.error(f"Erro na tradução: {e}")
                continue

            # Perform sentiment analysis using TextBlob
            sentiment = TextBlob(texto_traduzido).sentiment

            # Create a dictionary to store the review
            avaliacao = {
                "produto": nome_produto,
                "Avaliação": texto,
                "sentimento": sentiment.polarity,
                "emoção": sentiment.subjectivity
            }

            # Save the review to the list of reviews
            self.avaliacoes.append(avaliacao)

            # Increment the counters based on the review's polarity
            if sentiment.polarity > 0:
                self.positivas += 1
            elif sentiment.polarity < 0:
                self.negativas += 1
            else:
                self.neutras += 1

            # Print the result of the analysis
            self.logger.info("Produto: %s", nome_produto)
            self.logger.info("Avaliação: %s", texto)
            self.logger.info("Sentimento: %s", sentiment.polarity)
            self.logger.info("Emoção: %s", sentiment.subjectivity)
            self.logger.info("----------------------------------")

    def get_site_config(self, url):
        # Configuration dictionary to map site URLs to CSS classes
        site_configs = {
            "https://www.amazon.com.br/": {
                "class_teg": "span",
                "title_teg": "a",
                "title_class": "a-link-normal",
                "review_class": "a-size-base review-text review-text-content"
            },
            "https://www.mercadolivre.com.br/": {
                "class_teg": "p",
                "title_teg": "h1",
                "title_class": "ui-pdp-title",
                "review_class": "ui-review-capability-comments__comment__content"
            },
        }
        return site_configs.get(url)

    def avaliacao_existe(self, avaliacao):
        for item in self.avaliacoes:
            if item["Avaliação"] == avaliacao:
                return True
        return False

    def __init__(self, *args, **kwargs):
        super(WcSpider, self).__init__(*args, **kwargs)
        self.avaliacoes = []
        self.positivas = 0
        self.negativas = 0
        self.neutras = 0

    def closed(self, reason):
        # Combine existing reviews with new reviews
        avaliacoes_existentes = []
        try:
            with open("avaliacoes.json", "r", encoding="utf-8") as file:
                avaliacoes_existentes = json.load(file)
        except FileNotFoundError:
            pass

        avaliacoes_atualizadas = avaliacoes_existentes + self.avaliacoes

        # Save the updated reviews to the JSON file
        with open("avaliacoes.json", "w", encoding="utf-8") as file:
            json.dump(avaliacoes_atualizadas, file, ensure_ascii=False, indent=2)

        # Print the total number of positive, negative, and neutral reviews
        self.logger.info("Total de avaliações positivas: %s", self.positivas)
        self.logger.info("Total de avaliações negativas: %s", self.negativas)
        self.logger.info("Total de avaliações neutras: %s", self.neutras)
