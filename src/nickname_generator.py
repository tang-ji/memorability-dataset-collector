from src.dictionary_en import *
import numpy as np

def generate(min_length, max_length, items, p, seperator=' '):
    count = 0
    while True:
        animal_rand = np.random.randint(0, len(animal)-1)
        adjective_rand = np.random.randint(0, len(adjective)-1)
        color_rand = np.random.randint(0, len(color)-1)
        seq = []
        for i, item in enumerate(items):
            if np.random.rand()<=p[i]:
                seq.append(item[np.random.randint(0, len(item)-1)])
        name = seperator.join(seq)        
        if len(name) <= max_length and len(name) >= min_length:
            return name
        count = count + 1
        if count > 10000:
            raise ValueError('No available name found')