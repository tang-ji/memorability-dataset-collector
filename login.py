from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json, secrets, time, sys
from src.server import *
from src.tool import *
from src.nickname_generator import *

app = Flask(__name__)

@app.route('/')
def home():
    if 'logged_in' not in session:
        session['logged_in'] = False
    html_list = score_html(return_highest_score("data", dataset_list, 3))
    if not session.get('logged_in'):
        return render_template('login.html', board=html_list)
    else:
        server_class[session['username']].load()
        labels = list(server_class[session['username']].get_all())
        labels.append(server_class[session['username']].welcome())
        if debug:
            return render_template('game_debug.html', labels=labels, board=html_list[session['dataset_name']], debugs=list(server_class[session['username']].labels))
        return render_template('game.html', labels=labels, board=html_list[session['dataset_name']])

@app.route('/get_nickname')
def get_nickname():
    username_list = get_username_list("data")
    name_generated = generate(min_length=8, max_length=15, items=[color, adjective, animal], p=[0.5, 0.5, 1])
    while name_generated in username_list:
        name_generated = generate(min_length=8, max_length=15, items=[color, adjective, animal], p=[0.5, 0.5, 1])
    if not os.path.exists("log"):
        os.makedirs("log")
    with open(os.path.join("log", "log_nickname.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] New name generated.\n".format(name_generated.lower()))
    return jsonify(nickname=name_generated.lower())

@app.route('/get_info')
def get_info():
    username = ''.join(filter(valide_letter, request.args.get('username', "", type=str).lower()))
    dataset_name = request.args.get('dataset', "", type=str)
    session['dataset_name'] = dataset_name
    user_info_path = os.path.join("data", username)
    user_data_path = os.path.join(user_info_path, dataset_name)
    no_info = False
    if not os.path.exists(user_info_path):
        no_info = True
    try:
        [_, scores, marks] = pickle.load(open(os.path.join(user_data_path, "data.pkl"), 'rb'))
        max_scores = 0.0
        if len(scores) > 0:
            max_scores = max(scores)
    except:
        scores = []
        max_scores = 0.0
        marks = set()
        pass
    try:
        info = {}
        with open(os.path.join(user_info_path, "info.txt"), 'r') as f:
            ls = f.readlines()
            for l in ls:
                field, label = l.strip().split(",")
                info[field] = label
    except:
        no_info = True
        pass
    info["welcome"] = "Hi {}, you have played {} games based on {} dataset, your highest score is {}/100.".format(username, len(scores), dataset_name, max_scores)
    info["no_info"] = no_info
    session["no_info"] = no_info
    return jsonify(info=info)


@app.route('/answer')
def get_answer():
    answer = json.loads(request.args.get('answers'))
    server_class[session['username']].log = answer
    s = score(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer)
    server_class[session['username']].scores.append(s)
    server_class[session['username']].marks |= set(server_class[session['username']].imgs)
    e = evaluation(server_class[session['username']].labels, answer)
    server_class[session['username']].evaluations.append([e["correct_filler"], e["correct_target"], e["correct_target_rep"], e["correct_vigilence"], e["correct_vigilence_rep"]])
    with open(os.path.join("log", "log.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] [{}] Score: {}. ".format(session['username'], session['dataset_name'], s))
        f.write(return_result(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer))
        f.write("\n")
    with open(os.path.join("data/{}".format(session['username']), "log.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] [{}] Score: {}. ".format(session['username'], session['dataset_name'], s))
        f.write(return_result(server_class[session['username']].n_targets, server_class[session['username']].n_filler, server_class[session['username']].n_vigilence, server_class[session['username']].labels, answer))
        f.write("\n")

    for i in range(len(answer)):
        if server_class[session['username']].labels[i] == 2:
            server_class[session['username']].dataset[server_class[session['username']].imgs[i]] = answer[i]
    server_class[session['username']].save()
    server_class[session['username']].save_game()
    return jsonify(score=s)

@app.route('/login', methods=['POST', 'GET'])
def do_admin_login():
    if 'logged_in' not in session or session['logged_in'] == True:
        return home()
    username = ''.join(filter(valide_letter, request.form['username'].lower()))
    server_class[username] = Server(session['dataset_name'], debug=debug)
    server_class[username].login(username)
    if session["no_info"]:
        info = request.form.to_dict(flat=True)
        if not os.path.exists("log"):
            os.makedirs("log")
        with open(os.path.join("log", "login.txt"), 'a+') as f_log:
            f_log.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
            f_log.write("[{}] New user info: ".format(username))
            with open(os.path.join(os.path.join("data", username), "info.txt"), 'w') as f:
                for k, v in info.items():
                    f.write("{},{}\n".format(k, v))
                    f_log.write("{}: {}; ".format(k, v))
            f_log.write("\n")
    session['logged_in'] = True
    session['username'] = username
    if not os.path.exists("log"):
        os.makedirs("log")
    with open(os.path.join("log", "login.txt"), 'a+') as f:
        f.write(time.strftime("[%Y-%m-%d %H:%M:%S] ", time.localtime()))
        f.write("[{}] [{}] Log in.\n".format(server_class[session['username']].username, server_class[session['username']].dataset_name))
    return home()   

@app.route("/logout", methods=['POST', 'GET'])
def logout():
    if not session.get('logged_in'):
        return home()
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
    dataset_list = ["SUN", "Webpages", "Webpages_blured", "Posters", "Products"]
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=5000)
