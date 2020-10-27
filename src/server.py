import os, pickle, json, secrets, time, sys
from glob import glob
from src.tool import *

class Server:
    def __init__(self, img_path, database_path="data", n_targets=66, n_filler=44, n_vigilence=12, debug=False):
        self.n_targets = n_targets
        self.n_filler = n_filler
        self.n_vigilence = n_vigilence
        self.n = n_targets*2 + n_filler + n_vigilence*2
        self.img_path = img_path
        self.database_path = database_path
        self.debug = debug
        if debug:
            self.log = []
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
                f.write("{},{}\n".format(k, v))

        if self.debug:
            with open(os.path.join(self.user_data_path, "debug.pkl"), 'wb') as f:
                pickle.dump([self.imgs, self.labels, self.log], f)

    def save_game(self):
        if not os.path.exists(self.user_data_path):
            os.makedirs(self.user_data_path)

        with open(os.path.join(self.user_data_path, time.strftime("game%Y%m%d%H%M.txt", time.localtime())), 'w') as f:
            f.write(",".join(self.imgs)+"\n")
            f.write(",".join([str(int(label)) for label in self.labels])+"\n")
            f.write(",".join([str(int(label)) for label in self.log]))

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
                    file_name, label = l.strip().split(",")
                    self.dataset[file_name] = label
        except:
            pass

        file_targets, file_filler, file_vigilence = get_files(self.imgs_file, self.marks, n_targets=self.n_targets, n_filler=self.n_filler, n_vigilence=self.n_vigilence)
        self.imgs, self.labels = get_sequence(file_targets, file_filler, file_vigilence) 

    def get_all(self):
        return [os.path.join(self.img_path,p) for p in self.imgs[:self.n]]

    def reset(self):
        self.load()

    def welcome(self):
        if len(self.scores) == 0:
            score_max = 0
        else:
            score_max = max(self.scores)
        return("Hi {}, you have played {} games. Your highest score is {}/100.".format(self.username, len(self.scores), score_max))           
