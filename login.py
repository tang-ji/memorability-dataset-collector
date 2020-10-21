from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json
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
        labels = list(server_class.get_all())
        labels.append(server_class.welcome())
        return render_template('test.html', labels=labels)

@app.route('/img_url')
def img_url():
    answer = request.args.get('answer', 0, type=int)
    if answer == 2:
        server_class.reset()
    elif answer == 3:
        server_class.marks |= set(server_class.get_all())
        print_result(server_class.n_targets, server_class.n_filler, server_class.n_vigilence, server_class.labels, server_class.log)

        for i in range(len(server_class.log)):
            if server_class.labels[i] == 2:
                server_class.dataset[server_class.imgs[i]] = server_class.log[i]
        server_class.save()
    return jsonify(url=server_class.get())

@app.route('/answer')
def get_answer():
    answer = json.loads(request.args.get('answers'))
    server_class.log = answer
    s = score(server_class.n_targets, server_class.n_filler, server_class.n_vigilence, server_class.labels, answer)
    server_class.scores.append(s)
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
    server_class = server("static/imgs")
    try:
        app.secret_key = os.urandom(12)
        app.run(host='0.0.0.0', port=5000)
    finally:
        print("user:{} data saved. ({} images marked)".format(server_class.username, len(server_class.marks)))
