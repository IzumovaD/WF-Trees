import json

f_in = open('groupped_words_test.txt', 'r')
data = f_in.readlines()

groups = []
group = []

for line in data:
    if '---' in line:
        groups.append(group)
        group = []
    else:
        if '\n' in line:
            line = line.replace('\n', '')
        group.append(line)

f_out = 'groupped_words_test.json'
with open(f_out, 'w') as f:
    json.dump(groups, f)