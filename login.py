from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
import os
from glob import glob

app = Flask(__name__)

class imgs:
    def __init__(self, img_paths=None):
        self.imgs = ["https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/howto/img_mountains.jpg"]
        if img_paths is not None:
            self.imgs = glob("{}/*jpg".format(img_paths))
        self.i = 0
    def get(self):
        self.i += 1
        if self.i >= len(self.imgs):
            self.i = 0
        return self.imgs[self.i]
    def last(self):
        return self.imgs[self.i]

imgs_class = imgs("static/imgs")
username = None
log = {}
answers = []

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('test.html')

@app.route('/img_url')
def get_img_url():
    answers.append(request.args.get('answer', 0, type=int))
    if username not in log:
        log[username] = {}
    image_name = os.path.split(imgs_class.last())[1]
    log[username][image_name] = request.args.get('answer', 0, type=int)
    return jsonify(url=imgs_class.get())

@app.route('/login', methods=['POST'])
def do_admin_login():
    session['username'] = request.form['username']
    session['logged_in'] = True
    return home()   

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    try:
        app.secret_key = os.urandom(12)
        app.run(host='0.0.0.0', port=5000)
    finally:
        print(username, log)