import os
import pickle

import nltk
nltk.download('all')
nltk.download("stopwords")
nltk.download("punkt")
import torch
from deployment_model.seq_model import SeqModel
from flask import Flask, redirect, render_template, request, url_for
from nltk.tokenize import word_tokenize
from torchtext import vocab
from torchtext.legacy import vocab as VOCAB
from torchtext.legacy.data import Field, Pipeline
from utils.preprocessing_helper import *
from wordcloud import STOPWORDS

try:
    vocab._default_unk_index
except AttributeError:
    def _default_unk_index():
        return 0
    vocab._default_unk_index = _default_unk_index

# from flask_bootstrap import Bootstrap


# sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
TEMPLATE_DIR = os.path.abspath(r"D:\255\CMPE255_project\web_app\templates")
STATIC_DIR = os.path.abspath(r"D:\255\CMPE255_project\web_app\static")

app = Flask(__name__, template_folder=TEMPLATE_DIR, static_folder=STATIC_DIR)

RESULT = None

pre_pipeline = Pipeline(lemmatize)
pre_pipeline.add_before(preprocessing)
TEXT = Field(
    sequential=True,
    tokenize=word_tokenize,
    lower=True,
    stop_words=STOPWORDS,
    preprocessing=pre_pipeline,
)
LABELS = ["Neutral", "Negative", "Positive"]
VOCAB = {}
with open(r"D:\255\CMPE255_project\web_app\models\file.pkl", "rb") as f:
    VOCAB = pickle.load(f)

best_config = {
    "hidden_size": 302,
    "lr": 0.00010769630091763721,
    "l2": 2.5888680371842294e-05,
    "nonlin": "tanh",
    "dropout": 0.1,
    "num_layers": 2,
    "mode": 0,
    "optimizer": "Adam",
    "momentum": 0.1,
}

best_model = SeqModel(
    embedding_size=100,
    vocab_size=len(VOCAB),
    output_size=3,
    hidden_size=best_config["hidden_size"],
    num_layers=best_config["num_layers"],
    nonlin=best_config["nonlin"],
    dropout_rate=best_config["dropout"],
    mode=best_config["mode"],
    unit="gru",
    more_features=False,
)
best_model.load_state_dict(torch.load(r"D:\255\CMPE255_project\web_app\models\model_deploy.pt"))


@app.route("/", methods=["POST", "GET"])
def index():
    return render_template("index.html")


@app.route("/resultspage", methods=["POST", "GET"])
def resultspage():
    tweet = request.form["search"]
    RESULT = predict_sentiment(best_model, {"tweet": tweet})[0]
    return render_template("resultspage.html", value=RESULT)


def preprocess(tweet):
    return [VOCAB.get(token, 0) for token in TEXT.preprocess(tweet)]


def predict_sentiment(model, input_json):
    tweet = input_json["tweet"]
    num_input = preprocess(tweet)
    model_outputs = best_model(torch.LongTensor(num_input).reshape((-1, 1)))
    probabilities, predicted = torch.max(model_outputs.cpu().data, 1)
    pred_labels = LABELS[predicted]
    return pred_labels, probabilities


if __name__ == "__main__":
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
