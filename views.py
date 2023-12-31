import random
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Chat
from . import db
from bs4 import BeautifulSoup
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration
import re
import gdown
import os
import json

views = Blueprint('views', __name__)

def load_json_answers():
    location = "C:/Users/harsi/OneDrive/Desktop/Chatbot/Flask_Web_Application_V1/website/"
    with open(location + 'data.json', 'r') as file:
        data = json.load(file)

        return data

# Load the model
tokenizer = T5Tokenizer.from_pretrained('t5-base', model_max_length=50)

def download_trained_model_file(file):
    file_path = 'website/' + file  # Specify the path and filename

    if os.path.exists(file_path):
        print("Trained Model file already exists!")
    else:
        # file_id = '1u2F284nH_5JJ0A8BPH8d5juj9pW4LIFx'
        # https://drive.google.com/file/d/1Dwvzpjci6s0q3NMPAX7UVtcoOvD1ydda/view?usp=sharing
        # https://drive.google.com/file/d/1-LJEJYLy0DqJRJ7AH0s9Mg8GC7gkP1Yj/view?usp=drive_link
        file_id = '1-LJEJYLy0DqJRJ7AH0s9Mg8GC7gkP1Yj'
        gdown.download(f'//drive.google.com/file/d/{file_id}/view?usp=drive_link', file_path, quiet=False)
        print("File Downloaded successfully.")
    
    return file_path

file_path = download_trained_model_file('pytorch_model.bin')

state_dict = torch.load(file_path, map_location=torch.device('cpu'))

# Load the state dict into the model
model = T5ForConditionalGeneration.from_pretrained('t5-base')
model.load_state_dict(state_dict)
model.eval()  # set the model to evaluation mode


@views.route('/',methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        print("Nothing")
    else:
        db.session.commit()

    return render_home()

def generate_answer(question):
    input_text = "question: " + question + " answer:"
    inputs = tokenizer.encode(input_text, return_tensors='pt')
    outputs = model.generate(inputs, max_length=128, num_beams=4, early_stopping=True)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer

def render_home():
    return render_template("home.html", user=current_user)

@views.route('/clearChats',methods=['POST'])
def clearChats():
    Chat.query.filter_by(source_user_id=current_user.id).delete()
    db.session.commit()

    return redirect(url_for('views.home'))

@views.route('/msg',methods=['POST'])
def sendMsg():
    msg = request.form.get('msg')
    chat = Chat(data=msg, source_user_id=current_user.id, target_user_id=0)
    db.session.add(chat)
    db.session.commit()

    json_data = load_json_answers()
    json_msg = msg.lower()
    if re.search(r'\b(Bye|Goodbye|Ciao|Cya|GoodBye|bye|See you soon!)\b', msg, re.IGNORECASE):
        resp = 'See you Soon!'
    elif re.search(r'\b(Hi|Hello|Howdy|Hiya|Hi!!)\b', msg, re.IGNORECASE):
        resp = 'Hi I\'m SpartanGPT, How Can I help you?'
    elif re.search(r'\b(who developed you?| who is your developer?)\b', msg, re.IGNORECASE):
        resp = 'I\'m a Developed by Harshith Uppula, Harsimran Kaur, Mounica Ayalasomayajula, Richa Sharma & Shwetarani'
    elif json_msg in json_data:
            resp = json_data[json_msg]
    else:   
        resp = generate_answer(msg)
    
    chat = Chat(data=resp, source_user_id=current_user.id, target_user_id=current_user.id)
    db.session.add(chat)
    db.session.commit()

    return redirect(url_for('views.home'))