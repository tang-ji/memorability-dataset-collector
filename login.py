from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify
import os

app = Flask(__name__)

class imgs:
    def __init__(self):
        self.imgs = ["https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/css/img_fjords.jpg", "https://www.w3schools.com/howto/img_mountains.jpg"]
        self.i = 0
    def get(self):
        self.i += 1
        if self.i >= len(self.imgs):
            self.i = 0
        return self.imgs[self.i]

imgs_class = imgs()
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
    return jsonify(url=imgs_class.get(), answer=answers)

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
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=5000)