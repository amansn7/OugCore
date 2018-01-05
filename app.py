# -*- coding: utf-8 -*-
"""
Created on Sat Sep 23 11:52:07 2017

@author: abinashasim
"""

from flask import Flask
from flask import flash, redirect, render_template, request, session, abort,url_for, send_from_directory
import os
from werkzeug import secure_filename
import pandas as pd
import json
import numpy as np
import pytesseract as pt
from PIL import Image
import validators
import requests

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = '/home/abinashasim/OCR/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['jpg','jpeg','png'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']
           

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('upload.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin@technosoftcorp.com':
        session['logged_in'] = True
        return  render_template('upload.html')
    else:
        flash('wrong password!')
    return home()

@app.route("/url")
def endpoint():
    return render_template('main.html')

@app.route('/result', methods=['POST'])
def result():
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            filenames.append(filename)
    tess_op = []
    for file in filenames:
        op = pt.image_to_string(Image.open(os.path.join(app.config['UPLOAD_FOLDER'], file)))
        op = op.replace('\n',' ')
        tess_op.append(op)
    return render_template('check.html', output=tess_op, files=filenames)

@app.route('/result_image', methods=['POST'])
def result_image():
    uploaded_file = request.form['url']
    filenames = []
    img_data = requests.get(uploaded_file).content
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'temp.jpg'), 'wb') as handler:
        handler.write(img_data)
    op = pt.image_to_string(Image.open(os.path.join(app.config['UPLOAD_FOLDER'], 'temp.jpg')))
    op = op.replace('\n',' ')
    tess_op= [op]
	
    return render_template('check.html', output=tess_op, count = len(tess_op))



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],filename)

@app.route('/process', methods=['POST'])
def process():
    to_process = request.form.getlist('toprocess[]')
    tess_op = []
    for file in to_process:
        tess_op.append(pt.image_to_string(Image.open(os.path.join(app.config['UPLOAD_FOLDER'], file))))
    
    return render_template('check.html',output=tess_op)

if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=8888)