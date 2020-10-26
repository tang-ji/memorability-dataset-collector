from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, make_response
import os, pickle, json, secrets, time, sys
from src.server import *
from src.tool import *
from src.nickname_generator import *

app = Flask(__name__)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html', board=score_html(return_highest_score("data", 3)))
    else:
        server_class[session['username']].load()
        labels = list(server_class[session['username']].get_all())
        labels.append(server_class[session['username']].welcome())
        if debug:
            return render_template('game_debug.html', labels=labels, board=score_html(return_highest_score("data", 3)), debugs=list(server_class[session['username']].labels))
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
    if debug:
        server_class[session['username']].log = answer
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
    server_class[username] = Server("static/imgs", debug=debug)
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
    debug = False
    server_class = {}
    app.secret_key = os.urandom(12)
    app.run(host='0.0.0.0', port=5000)
