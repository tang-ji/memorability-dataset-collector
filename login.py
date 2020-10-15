from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
import os
from glob import glob

app = Flask(__name__)

class server:
    def __init__(self, img_paths=None):
        self.imgs = ["https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/howto/img_mountains.jpg"]
        if img_paths is not None:
            self.imgs = glob("{}/*jpg".format(img_paths))
        self.i = 0
        self.username = None
        self.log = {}
    def get(self):
        self.i += 1
        if self.i >= len(self.imgs):
            self.i = 0
        return self.imgs[self.i]
    def last(self):
        return self.imgs[self.i]
    def reset(self):
        self.i = 0

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('test.html')

@app.route('/img_url')
def img_url():
    answer = request.args.get('answer', 0, type=int);
    if answer == 2:
        server_class.log = {}
        server_class.reset()
    else:
        if server_class.username not in server_class.log:
            server_class.log[server_class.username] = {}
        image_name = os.path.split(server_class.last())[1]
        server_class.log[server_class.username][image_name] = answer
    return jsonify(url=server_class.get())

@app.route('/login', methods=['POST'])
def do_admin_login():
    server_class.username = request.form['username']
    session['logged_in'] = True
    return home()   

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return home()

if __name__ == "__main__":
    server_class = server("static/imgs")
    try:
        app.secret_key = os.urandom(12)
        app.run(host='0.0.0.0', port=5000)
    finally:
        print(server_class.username, server_class.log)