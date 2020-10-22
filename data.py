import numpy as np

def get_files(imgs, marked, n_targets=66, n_filler=22, n_vigilence=12):
    imgs_new = [img for img in imgs if img not in marked]
    files = np.random.choice(imgs_new, n_targets + n_filler + n_vigilence, replace=False)
    return files[:n_targets], files[n_targets: n_targets + n_filler], files[n_targets + n_filler: n_targets + n_filler + n_vigilence]

    
def next_vig(available, i, max_vigilence):
    l = []
    for j in range(i+1, len(available)):
        if available[j] - available[i] > 3:
            if available[j] - available[i] <= max_vigilence:
                l.append(j)
            else:
                break
    if len(l) == 0:
        return None
    return np.random.choice(l, 1)[0]

def next_target(labels, target, target_gap):
    temp_gap = 0; this_gap = 0
    while True:
        if labels[target + target_gap + temp_gap] == 0:
            this_gap = target_gap + temp_gap
            break
        if labels[target + target_gap - temp_gap] == 0:
            this_gap = target_gap - temp_gap
            break
        temp_gap += 1
    return this_gap

def set_target_reps(labels, files,file_targets, targets, target_gap):
    for i, target in enumerate(targets):  
        this_gap = next_target(labels, target, target_gap)
        labels[target+this_gap] = 2
        files[target+this_gap] = file_targets[i]

def get_sequence(file_targets, file_filler, file_vigilence, target_gap=80, max_vigilence=10):
    label_list = ["filler", "target", "target_rep", "vigilence", "vigilence_rep"]
    n_targets, n_filler, n_vigilence = len(file_targets), len(file_filler), len(file_vigilence)
    # shuffle
    np.random.shuffle(file_targets)
    np.random.shuffle(file_filler)
    np.random.shuffle(file_vigilence)
    n = n_targets*2 + n_filler + n_vigilence*2
    labels = np.zeros(n)
    files = np.array([file_targets[0]]*n)
    targets = np.random.choice(n-target_gap, n_targets, replace=False)
    labels[targets] = 1
    files[targets] = file_targets
    set_target_reps(labels, files,file_targets, targets, target_gap)
    available = np.array(range(n))[labels == 0]
    current_vigilence = 0
    for i in range(n_vigilence*2):
        s = np.random.choice(len(available), 1)[0]
        s_next = next_vig(available, s, max_vigilence)
        if s_next is None:
            continue
        labels[available[s]] = 3  
        files[available[s]] = file_vigilence[current_vigilence]
        labels[available[s_next]] = 4
        files[available[s_next]] = file_vigilence[current_vigilence]
        available = np.delete(available, s_next)
        available = np.delete(available, s)
        current_vigilence += 1
        if current_vigilence == n_vigilence:
            break

    files[available] = file_filler
    return files, labels

def evaluation(labels, answers):
    labels = np.array(labels)
    answers = np.array(answers)
    results = {}
    results["correct_filler"] = sum(answers[labels==0]==0)
    results["correct_target"] = sum(answers[labels==1]==0)
    results["correct_target_rep"] = sum(answers[labels==2]==1)
    results["correct_vigilence"] = sum(answers[labels==3]==0)
    results["correct_vigilence_rep"] = sum(answers[labels==4]==1)
    return results

def score(n_targets, n_filler, n_vigilence, labels, answers):
    e = evaluation(labels, answers)
    s_max = n_targets*3+n_filler+n_vigilence*2
    s = e["correct_filler"]+e["correct_target"]+2*e["correct_target_rep"]+e["correct_vigilence"]+e["correct_vigilence_rep"] 
    return int(np.sqrt(s)/np.sqrt(s_max)*100)

def return_result(n_targets, n_filler, n_vigilence, labels, answers):
    e = evaluation(labels, answers)
    return("filler accuracy: {:.1f}%, target accuracy: {:.1f}%, vigilence accuracy: {:.1f}%".format(e['correct_filler']/n_filler*100, 
                                                                                               (e['correct_target']+e['correct_target_rep'])/(2*n_targets)*100, 
                                                                                               (e['correct_vigilence']+e['correct_vigilence_rep'])/(2*n_vigilence)*100))