from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json, secrets, time
from glob import glob
from src.tool import *
from src.nickname_generator import *

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
            if not os.path.exists("log"):
                os.makedirs("log")
            with open(os.path.join("log", "login.txt"), 'a+') as f:
                f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
                f.write("[{}] New user.\n".format(self.username))
        self.load()

    def save(self):
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)

        with open(os.path.join(self.user_data_path, "data.pkl"), 'wb') as f:
            pickle.dump([self.evaluations, self.scores, self.marks], f)

        with open(os.path.join(self.user_data_path, "labels.txt"), 'w') as f:
            for k, v in self.dataset.items():
                f.write("{} {}\n".format(k, v))

    def load(self):
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)
        try:
            [self.evaluations, self.scores, self.marks] = pickle.load(open(os.path.join(self.user_data_path, "data.pkl"), 'rb'))
        except:
            self.evaluations = []
            self.scores = []
            self.marks = set()
            pass
        try:
            self.dataset = {}
            with open(os.path.join(self.user_data_path, "labels.txt"), 'r') as f:
                ls = f.readlines()
                for l in ls:
                    file_name, label = l.strip().split(" ")
                    self.dataset[file_name] = label
        except:
            self.dataset = {}
            pass

        file_targets, file_filler, file_vigilence = get_files(self.imgs_file, self.marks, n_targets=self.n_targets, n_filler=self.n_filler, n_vigilence=self.n_vigilence)
        self.imgs, self.labels = get_sequence(file_targets, file_filler, file_vigilence) 
    def get_all(self):
        if debug:
            self.labels = [0]*10
            return [os.path.join(self.img_path,p) for p in self.imgs[:10]]
        return [os.path.join(self.img_path,p) for p in self.imgs[:self.n]]
    def reset(self):
        self.load()

    def welcome(self):
        if len(self.scores) == 0:
            score_max = 0
        else:
            score_max = max(self.scores)
        return("Hi {}, you have already marked {} images. Your highest score is {}/100.".format(self.username, len(self.marks), score_max))           

def return_highest_score(data_path, n):
    data = glob(os.path.join(data_path, "*/data.pkl"))
    l = []
    for d in data:
        user_name = d.split(os.path.sep)[-2]
        [_, scores, _] = pickle.load(open(d, 'rb'))
        score_m = max(scores)
        l.append([user_name, score_m])
    return sorted(l, key=lambda x:-x[1])[:n]

def get_username_list(data_path):
    data = glob(os.path.join(data_path, "*"))
    return set([os.path.split(x)[1] for x in data])

def score_html(score_list):
    l = ""
    for i, item in enumerate(score_list):
        l+="<l2><p>{:>2}. {:<30s}{:>5.1f}</p></l2>".format(i+1, item[0], item[1])

    return l

def valide_letter(s):
    if s.isalpha() or s.isdigit() or s == " ":
        return True
    return False

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html', board=score_html(return_highest_score("data", 3)))
    else:
        server_class[session['username']].load()
        labels = list(server_class[session['username']].get_all())
        labels.append(server_class[session['username']].welcome())
        return render_template('game.html', labels=labels, board=score_html(return_highest_score("data", 3)))

@app.route('/get_nickname')
def get_nickname():
    username_list = get_username_list("data")
    name_generated = generate(min_length=8, max_length=15, items=[color, adjective, animal], p=[0.5, 0.5, 1])
    while name_generated in username_list:
        name_generated = generate(min_length=8, max_length=15, items=[color, adjective, animal], p=[0.5, 0.5, 1])
    return jsonify(nickname=name_generated.lower())

@app.route('/answer')
def get_answer():
    answer = json.loads(request.args.get('answers'))
    s = score(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer)
    server_class[session['username']].scores.append(s)
    server_class[session['username']].marks |= set(server_class[session['username']].imgs)
    e = evaluation(server_class[session['username']].labels, answer)
    server_class[session['username']].evaluations.append([e["correct_filler"], e["correct_target"], e["correct_target_rep"], e["correct_vigilence"], e["correct_vigilence_rep"]])
    with open(os.path.join("log", "log.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] Score: {}. ".format(session['username'], s))
        f.write(return_result(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer))
        f.write("\n")

    for i in range(len(answer)):
        if server_class[session['username']].labels[i] == 2:
            server_class[session['username']].dataset[server_class[session['username']].imgs[i]] = answer[i]
    server_class[session['username']].save()
    return jsonify(score=s)

@app.route('/login', methods=['POST'])
def do_admin_login():
    username = ''.join(filter(valide_letter, request.form['username'].lower()))
    server_class[username] = server("static/imgs")
    server_class[username].login(username)
    session['logged_in'] = True
    session['username'] = username
    if not os.path.exists("log"):
        os.makedirs("log")
    with open(os.path.join("log", "login.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] Log in.\n".format(server_class[session['username']].username))
    return home()   

@app.route("/logout", methods=['POST'])
def logout():
    session['logged_in'] = False
    if not os.path.exists("log"):
        os.makedirs("log")
    with open(os.path.join("log", "login.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] Log out.\n".format(server_class[session['username']].username))
    server_class.pop(session['username'], None)
    
    return home()


if __name__ == "__main__":
    debug = True
    server_class = {}
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=5000)
