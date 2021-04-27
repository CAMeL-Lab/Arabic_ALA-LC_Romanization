from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from app import app
from app.forms import RomanizeForm
from src.predict.mle_predict import apply_mle_translit_simple_backoff, load_mle_model
from src.predict import translit_rules


mle_model = load_mle_model(mle_model_tsv='models/mle/size1.0.tsv')

mappings = translit_rules.load_loc_mappings()
exceptional = translit_rules.load_exceptional_spellings()



@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')



@app.route('/romanize', methods=['GET'])
def romanize():
    txt = request.args.get('txt','')
    output_text = []
    for line in txt.split('\n'):
        output_text.append(apply_mle_translit_simple_backoff(line,mle_model,mappings,exceptional))
    req = request.get_json()
    print(req)
    return '\n'.join(output_text)


