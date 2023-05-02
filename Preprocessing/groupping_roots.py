from root_allomorphs import root_allomorphs
import time
import json

# список списков (каждый элемент - группа алломорфных корней)
roots = []
# чередующиеся согласные на конце корня
consonants_alternations = [{'ц','т'}, {'к','ч'}, {'ц','ч'}, {'х','ш'}, {'г','ж'}, {'ж','з'}, {'д','ж'}, {'к','ц'}]
# наращения согласных на конце корня
consonants_augmentations = [{'ж','жд'}, {'д','жд'}, {'щ','ст'}, {'щ','ск'}, {'б','бл'}, {'п','пл'}, {'м','мл'}, {'в','вл'}, {'ф','фл'}]
# чередования гласных
vowels_alternations = [['о','а'], ['е','и']]
# группы корней для удаления
groups_to_remove = []
# группы корней для добавления
groups_to_append = []

# ф-ция выделения морфем в слове
def extract_morphs(line):
    s = line.split()
    morphs = dict()
    parsing = s[1].split('/')
    for elem in parsing:
        tmp = elem.split(':')
        morph_name = tmp[1]
        morph = tmp[0]
        if morph_name in morphs:
            morphs[morph_name].append(morph)
        else:
            morphs[morph_name] = [morph]
    return morphs

# ф-ция поиска группы алломорфных корней в готовом наборе
def has_allomorphs(root):
    for group in root_allomorphs:
        if root in group:
            return group
    return False

# ф-ция поиска чередующихся согласных на конце корня
def end_letters_search(root, groups):
        result = []
        common_part = root[:-1]
        for group in groups:
            if group not in groups_to_remove:
                for root1 in group:
                    if len(root) == len(root1) and root1.startswith(common_part):
                        if {root[-1], root1[-1]} in consonants_alternations:
                            groups_to_remove.append(group)
                            result = [*result, *group]
                            break
        return result

# ф-ция поиска наращений согласных на конце корня
def end_letters_search(root, groups):
        result = []
        for group in groups:
            if group not in groups_to_remove:
                for root1 in group:
                    if abs(len(root1)-len(root)) == 1:
                        if root1.startswith(root[:-1]):
                            if {root1[-2:], root[-1]} in consonants_augmentations:
                                groups_to_remove.append(group)
                                result = [*result, *group]
                                break
                        elif root.startswith(root1[:-1]):
                            if {root[-2:], root1[-1]} in consonants_augmentations:
                                groups_to_remove.append(group)
                                result = [*result, *group]
                                break
        return result

# ф-ция проверки чередования и-ы в начале корня
def start_search(root, groups, letter):
    for group in groups:
        if group not in groups_to_remove:
            for root1 in group:
                if root1[0] == letter and root1[1:] == root[1:]:
                    groups_to_remove.append(group)
                    return group
    return []

# ф-ция проверки чередований гласных в середине корня
def inner_search(ch, alt_ch, root, groups):
    len_root = len(root) - 1
    indexes = [i for i, c in enumerate(root) if c == ch]
    if 0 in indexes:
        indexes.remove(0)
    if len_root in indexes:
        indexes.remove(len_root)
    for i in indexes:
        alter_root = root[:i] + alt_ch + root[i+1:]
        for group in groups:
            if group not in groups_to_remove:
                for root1 in group:
                    if root1 == alter_root:
                        groups_to_remove.append(group)
                        return(group)
    return []

# ф-ция поиска чередования гласных в корне
def vowel_search(root, groups):
        result = []
        # проверка чередования и-ы в начале корня
        if root[0] == 'и':
            result = start_search(root, groups, 'ы')
        elif root[0] == 'ы':
            result = start_search(root, groups, 'и')
        if len(result) != 0:
            return result
        # проверка чередований о-а и е-и в середине корня
        for alternation in vowels_alternations:
            result = inner_search(alternation[0], alternation[1], root, groups)
            if len(result) != 0:
                return result
            result = inner_search(alternation[1], alternation[0], root, groups)
            if len(result) != 0:
                return result
        return result

# ф-ция печати корней в текстовый файл
def print_roots(file):
    s = ''
    roots.reverse()
    for group in roots:
        s += ', '.join(group)
        s += '\n'
    file.write(s)
    file.close()

# ф-ция обновления списка roots
def update_groups():
    for r in groups_to_remove:
        if r in roots:
            roots.remove(r)
    for r in groups_to_append:
        roots.append(r)

def main_processing_roots(data):
    start_time = time.time()
    print("Сбор групп алломорфных корней" + "\n")

    # 1. Выделение корней без алломорфов
    for line in data:
        morphs = extract_morphs(line)
        root = morphs['ROOT']
        if len(root) > 1:
            continue
        if root not in roots:
            roots.append(root)

    print("Шаг 1: Число уникальных корней (без учёта алломорфов): ", len(roots))

    # 2. Проверка алломорфов по КроссЛексике
    groups_to_remove = []
    groups_to_append = []

    for root in roots:
        if root not in groups_to_remove:
            group = has_allomorphs(root[0])
            if group:
                for r in group:
                    groups_to_remove.append([r])
                groups_to_append.append(group)

    update_groups()

    print("Шаг 2: Число групп алломорфных корней: ", len(roots))

    # 3. Сливаем корни по типу: автомобил - автомобиль и бактери - бактерий
    groups_to_remove = []
    groups_to_append = []

    for group in roots:
        if len(group) == 1:
            r = group[0]
            if r[-1] == 'ь' or  r.endswith('ий'):
                allomorph = r[:-1]
                if [allomorph] in roots:
                    groups_to_append.append([allomorph, r])
                    groups_to_remove.append([allomorph])
                    groups_to_remove.append(group)

    update_groups()

    print("Шаг 3: Число групп алломорфных корней: ", len(roots))

    # 4. Чередование согласных на конце корня 
    groups_to_remove = []
    groups_to_append = []

    for k in range(len(roots)-1):
        group = roots[k]
        if group not in groups_to_remove:
            group_to_append = group
            groups_to_remove.append(group)
            for root in group_to_append:
                group_to_append = [*group_to_append, *end_letters_search(root, roots[k:])]
            groups_to_append.append(group_to_append)

    update_groups()

    print("Шаг 4: Число групп алломорфных корней: ", len(roots))

    # 5. Наращивание согласной на конце корня
    groups_to_remove = []
    groups_to_append = []

    for k in range(len(roots)-1):
        group = roots[k]
        if group not in groups_to_remove:
            group_to_append = group
            groups_to_remove.append(group)
            for root in group_to_append:
                group_to_append = [*group_to_append, *end_letters_search(root, roots[k:])]
            groups_to_append.append(group_to_append)

    update_groups()

    print("Шаг 5: Число групп алломорфных корней: ", len(roots))

    # 6. Чередование гласных
    groups_to_remove = []
    groups_to_append = []

    for k in range(len(roots)-1):
        group = roots[k]
        if group not in groups_to_remove:
            group_to_append = group
            groups_to_remove.append(group)
            for root in group_to_append:
                group_to_append = [*group_to_append, *vowel_search(root, roots[k:])]
            groups_to_append.append(group_to_append)

    update_groups()
    
    print("Шаг 6: Число групп алломорфных корней: ", len(roots))

    filename = 'roots.json'
    with open(filename, 'w') as f:
        json.dump(roots, f)

    f_out = open('roots.txt', 'w')
    print_roots(f_out)

    print("--- %s seconds ---\n" % (time.time() - start_time))
    print("Сбор групп алломорфных корней закончен" + "\n")