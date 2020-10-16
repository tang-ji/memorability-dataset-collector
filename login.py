from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle
from glob import glob

app = Flask(__name__)

class server:
    def __init__(self, img_paths=None):
        self.imgs = ["https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/howto/img_mountains.jpg"]
        if img_paths is not None:
            self.imgs = glob("{}/*.jpg".format(img_paths))
        self.i = 0
        self.username = None
        self.log = {}
        self.logs = {}
    def login(self, username):
        self.username = username
        if username in self.logs:
            self.log = self.logs[username]
        else:
            self.logs[username] = {}
        self.i = len(self.log)
    def get(self):
        self.i += 1
        if self.i >= len(self.imgs):
            self.i = 0
        return self.imgs[self.i]
    def get_all(self):
        return self.imgs[self.i:self.i+198]
    def last(self):
        return self.imgs[self.i]
    def reset(self):
        self.i = len(self.logs[self.username])
    def welcome(self):
        return("Hi {}, you have already marked {} images.".format(self.username, self.i))

def reset():
    server_class.log = {}
    server_class.reset()

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        labels = server_class.get_all()
        labels.append(server_class.welcome())
        return render_template('test.html', labels=labels)

@app.route('/img_url')
def img_url():
    answer = request.args.get('answer', 0, type=int);
    if answer == 2:
        reset()
    elif answer == 3:
        server_class.logs[server_class.username] = server_class.log
    else:
        image_name = os.path.split(server_class.last())[1]
        server_class.log[image_name] = answer
    return jsonify(url=server_class.get())

@app.route('/login', methods=['POST'])
def do_admin_login():
    server_class.login(request.form['username'])
    session['logged_in'] = True
    return home()   

@app.route("/logout", methods=['POST'])
def logout():
    reset()
    session['logged_in'] = False
    return home()


if __name__ == "__main__":
    try:
        server_class = server("static/imgs")
    except:
        server_class = pickle.load(open("logs.pkl", "rb"))
    try:
        app.secret_key = os.urandom(12)
        app.run(host='0.0.0.0', port=5000)
    finally:
        pickle.dump(server_class, open("logs.pkl", "wb"))
        print(server_class.logs)