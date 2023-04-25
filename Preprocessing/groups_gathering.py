import json
import re
import time

# функция выделения всех корней в слове
def extract_roots(word):
    roots = []
    pattern = "\w+:ROOT"
    tmp = re.findall(pattern, word)
    for t in tmp:
        t1 = t.find(':')
        root = t[:t1]
        roots.append(root)
    return roots

def main_processing_words(data):
    start_time = time.time()
    print("Сбор групп слов одного корня" + "\n")

    filename = 'roots.json'
    with open(filename) as f:
        roots = json.load(f)

    #список списков - группы однокоренных слов, порядок совпадает с порядком групп алломорфных корней в roots
    words_groups = []

    for group in roots:
        words_group = []
        for line in data:
            word = line.split()[1]
            word_roots = extract_roots(word)
            if len(word_roots) != 1:
                continue
            else:
                if word_roots[0] in group:
                    words_group.append(word)
        if len(words_group) != 0:
            words_groups.append(words_group)

    filename = 'groupped_words.json'
    with open(filename, 'w') as f:
        json.dump(words_groups, f)

    s = ''
    for group in words_groups:
        for word in group:
            s += word + '\n'
        s += '------------------------' + '\n'

    f_out2 = open('groupped_words.txt', 'w')
    f_out2.write(s)
    f_out2.close()

    print("--- %s seconds ---\n" % (time.time() - start_time))
    print("Сбор групп слов одного корня закончен" + "\n")