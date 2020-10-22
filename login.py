from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json, secrets
from glob import glob
from data import *

app = Flask(__name__)

class server:
    def __init__(self, img_path, database_path="data", n_targets=66, n_filler=44, n_vigilence=12):
        self.n_targets = n_targets
        self.n_filler = n_filler
        self.n_vigilence = n_vigilence
        self.n = n_targets*2 + n_filler + n_vigilence*2
        self.img_path = img_path
        self.database_path = database_path
        if not os.path.exists(database_path):
            os.makedirs(database_path)
        self.imgs_file = [os.path.split(p)[1] for p in glob(os.path.join(img_path, "*.jpg"))]

        self.username = None
        
    def login(self, username):
        self.username = username
        self.user_data_path = os.path.join(self.database_path, username)
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)

        self.load()

    def save(self):
        print("Saving dataset for user: {}".format(self.username))
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)

        with open(os.path.join(self.user_data_path, "data.pkl"), 'wb') as f:
            pickle.dump([self.log, self.scores, self.marks], f)

        with open(os.path.join(self.user_data_path, "labels.txt"), 'w') as f:
            for k, v in self.dataset.items():
                f.write("{} {}\n".format(k, v))
        print("User: {} data saved.".format(self.username))

    def load(self):
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)
        try:
            [self.log, self.scores, self.marks] = pickle.load(open(os.path.join(self.user_data_path, "data.pkl"), 'rb'))
        except:
            print("No data found for user: {}, create new dataset.".format(self.username))
            self.log = []
            self.scores = []
            self.marks = set()
            pass
        try:
            self.dataset = {}
            with open(os.path.join(self.user_data_path, "labels.txt"), 'rb') as f:
                ls = f.readlines()
                for l in ls:
                    file_name, label = l.strip().split(" ")
                    self.dataset[file_name] = label
        except:
            self.dataset = {}
            pass

        file_targets, file_filler, file_vigilence = get_files(self.imgs_file, self.marks, n_targets=self.n_targets, n_filler=self.n_filler, n_vigilence=self.n_vigilence)
        self.imgs, self.labels = get_sequence(file_targets, file_filler, file_vigilence) 

        
    # def get(self):
    #     self.i += 1
    #     if self.i >= len(self.imgs):
    #         self.i = 0
    #     return os.path.join(img_paths,self.imgs[self.i])
    def get_all(self):
        if debug:
            self.labels = [0]*10
            return [os.path.join(self.img_path,p) for p in self.imgs[:10]]
        return [os.path.join(self.img_path,p) for p in self.imgs[:self.n]]
    # def last(self):
    #     return self.imgs[self.i]
    def reset(self):
        self.load()

    def welcome(self):
        if len(self.scores) == 0:
            score_max = 0
        else:
            score_max = max(self.scores)
        return("Hi {}, you have already marked {} images. Your highest score is {}/100.".format(self.username, len(self.marks), score_max))           
               
@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        server_class[session['username']].load()
        labels = list(server_class[session['username']].get_all())
        labels.append(server_class[session['username']].welcome())
        return render_template('test.html', labels=labels)

@app.route('/answer')
def get_answer():
    answer = json.loads(request.args.get('answers'))
    server_class[session['username']].log = answer
    s = score(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer)
    server_class[session['username']].scores.append(s)
    server_class[session['username']].marks |= set(server_class[session['username']].get_all())
    print("User: {} result: {}".format(session['username'], s))

    for i in range(len(server_class[session['username']].log)):
        if server_class[session['username']].labels[i] == 2:
            server_class[session['username']].dataset[server_class[session['username']].imgs[i]] = server_class[session['username']].log[i]
    server_class[session['username']].save()
    return jsonify(score=s)

@app.route('/login', methods=['POST'])
def do_admin_login():
    username = request.form['username'].lower()
    server_class[username] = server("static/imgs")
    server_class[username].login(username)
    session['logged_in'] = True
    session['username'] = username
    print("User:{} log in.".format(server_class[session['username']].username))
    return home()   

@app.route("/logout", methods=['POST'])
def logout():
    session['logged_in'] = False
    print("User:{} log out.".format(server_class[session['username']].username))
    server_class.pop(session['username'], None)
    
    return home()


if __name__ == "__main__":
    debug = True
    server_class = {}
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=5000)
