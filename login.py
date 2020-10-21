from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json
from glob import glob
from data import *

app = Flask(__name__)

class server:
    def __init__(self, img_paths, n_targets=66, n_filler=44, n_vigilence=12):
        self.n_targets = n_targets
        self.n_filler = n_filler
        self.n_vigilence = n_vigilence
        self.n = n_targets*2 + n_filler + n_vigilence*2
        self.imgs_file = glob("{}/*.jpg".format(img_paths))
        self.i = 0
        self.score = []
        self.scores = {}
        self.username = None
        self.log = []
        self.logs = {}
        self.mark = set()
        self.marks = {}
        self.dataset = {}
        
    def login(self, username):
        self.username = username
        if username in self.logs:
            self.log = self.logs[username].copy()
            self.mark = self.marks[username].copy()
            self.score = self.scores[username].copy()
        else:
            self.logs[username] = []
            self.marks[username] = set()
            self.dataset[username] = {}
            self.scores[username] = []
        self.i = 0
        file_targets, file_filler, file_vigilence = get_files(self.imgs_file, self.mark, n_targets=self.n_targets, n_filler=self.n_filler, n_vigilence=self.n_vigilence)
        self.imgs, self.labels = get_sequence(file_targets, file_filler, file_vigilence) 
        self.mark |= set(self.imgs)
        
    def get(self):
        self.i += 1
        if self.i >= len(self.imgs):
            self.i = 0
        return self.imgs[self.i]
    def get_all(self):
        if debug:
            self.labels = [0]*10
            return self.imgs[self.i:self.i+10]
        return self.imgs[self.i:self.i+self.n]
    def last(self):
        return self.imgs[self.i]
    def reset(self):
        self.i = len(self.marks[self.username])
        self.log = []
    def welcome(self):
        if len(self.score) == 0:
            score_max = 0
        else:
            score_max = max(self.scores[self.username])
        return("Hi {}, you have already marked {} images. Your highest score is {}/100.".format(self.username, len(self.marks[self.username]), score_max))
               
               
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        labels = list(server_class.get_all())
        labels.append(server_class.welcome())
        return render_template('test.html', labels=labels)

@app.route('/img_url')
def img_url():
    answer = request.args.get('answer', 0, type=int)
    if answer == 2:
        server_class.reset()
    elif answer == 3:
        server_class.logs[server_class.username] = server_class.log
        server_class.scores[server_class.username] = server_class.score
        server_class.marks[server_class.username] |= server_class.mark
        print_result(server_class.n_targets, server_class.n_filler, server_class.n_vigilence, server_class.labels, server_class.log)
        for i in range(len(server_class.log)):
            image_name = os.path.split(server_class.imgs[i])[1]
            if server_class.labels[i] == 2:
                server_class.dataset[server_class.username][image_name] = server_class.log[i]
        pickle.dump(server_class, open("logs.pkl", "wb"))
    return jsonify(url=server_class.get())

@app.route('/answer')
def get_answer():
    answer = json.loads(request.args.get('answers'))
    server_class.log = answer
    s = score(server_class.n_targets, server_class.n_filler, server_class.n_vigilence, server_class.labels, answer)
    server_class.score.append(s)
    return jsonify(score=s)

@app.route('/login', methods=['POST'])
def do_admin_login():
    server_class.login(request.form['username'].lower())
    session['logged_in'] = True
    print("user:{} log in.".format(server_class.username))
    return home()   

@app.route("/logout", methods=['POST'])
def logout():
    server_class.reset()
    session['logged_in'] = False
    return home()


if __name__ == "__main__":
    debug = False
    if debug:
        server_class = server("static/imgs")
        app.secret_key = os.urandom(12)
        app.run(host='0.0.0.0', port=5000)
        print(server_class.logs)
    else:
        try:
            server_class = pickle.load(open("logs.pkl", "rb"))
        except:
            server_class = server("static/imgs")
        try:
            app.secret_key = os.urandom(12)
            app.run(host='0.0.0.0', port=5000)
        finally:
            pickle.dump(server_class, open("logs.pkl", "wb"))
            print("user:{} data saved. ({} images marked)".format(server_class.username, len(self.marks[self.username])))