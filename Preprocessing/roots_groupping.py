from RuRoots_Allomorphs import root_allomorphs
import time
import json

# чередующиеся согласные на конце корня
consonants_alternations = [{'ц','т'}, {'к','ч'}, {'ц','ч'}, {'х','ш'}, {'г','ж'}, {'ж','з'}, {'д','ж'}, {'к','ц'}]
# наращения согласных на конце корня
consonants_augmentations = [{'ж','жд'}, {'д','жд'}, {'щ','ст'}, {'щ','ск'}, {'б','бл'}, {'п','пл'}, {'м','мл'}, {'в','вл'}, {'ф','фл'}]
# чередования гласных
vowels_alternations = [['о','а'], ['е','и']]

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
def end_alternations_search(root, groups, remove_groups):
        result = []
        common_part = root[:-1]
        for group in groups:
            if group not in remove_groups:
                for root1 in group:
                    if len(root) == len(root1) and root1.startswith(common_part):
                        if {root[-1], root1[-1]} in consonants_alternations:
                            remove_groups.append(group)
                            result = [*result, *group]
                            break
        return result

# ф-ция поиска наращений согласных на конце корня
def end_augmentations_search(root, groups, remove_groups):
        result = []
        for group in groups:
            if group not in remove_groups:
                for root1 in group:
                    if abs(len(root1)-len(root)) == 1:
                        if root1.startswith(root[:-1]):
                            if {root1[-2:], root[-1]} in consonants_augmentations:
                                remove_groups.append(group)
                                result = [*result, *group]
                                break
                        elif root.startswith(root1[:-1]):
                            if {root[-2:], root1[-1]} in consonants_augmentations:
                                remove_groups.append(group)
                                result = [*result, *group]
                                break
        return result

# ф-ция проверки чередования и-ы в начале корня
def start_search(root, groups, letter, remove_groups):
    for group in groups:
        if group not in remove_groups:
            for root1 in group:
                if root1[0] == letter and root1[1:] == root[1:]:
                    remove_groups.append(group)
                    return group
    return []

# ф-ция проверки чередований гласных в середине корня
def inner_search(ch, alt_ch, root, groups, remove_groups):
    len_root = len(root) - 1
    indexes = [i for i, c in enumerate(root) if c == ch]
    if 0 in indexes:
        indexes.remove(0)
    if len_root in indexes:
        indexes.remove(len_root)
    for i in indexes:
        alter_root = root[:i] + alt_ch + root[i+1:]
        for group in groups:
            if group not in remove_groups:
                for root1 in group:
                    if root1 == alter_root:
                        remove_groups.append(group)
                        return(group)
    return []

# ф-ция поиска чередования гласных в корне
def vowel_search(root, groups, remove_groups):
        result = []
        # проверка чередования и-ы в начале корня
        if root[0] == 'и':
            result = start_search(root, groups, 'ы', remove_groups)
        elif root[0] == 'ы':
            result = start_search(root, groups, 'и', remove_groups)
        if len(result) != 0:
            return result
        # проверка чередований о-а и е-и в середине корня
        for alternation in vowels_alternations:
            result = inner_search(alternation[0], alternation[1], root, groups, remove_groups)
            if len(result) != 0:
                return result
            result = inner_search(alternation[1], alternation[0], root, groups, remove_groups)
            if len(result) != 0:
                return result
        return result

# ф-ция печати корней в текстовый файл
def print_roots(roots):
    filename = 'roots.json'
    with open(filename, 'w') as f:
        json.dump(roots, f)
    f_out_txt = open('roots.txt', 'w')
    s = ''
    roots.reverse()
    for group in roots:
        s += ', '.join(group)
        s += '\n'
    f_out_txt.write(s)
    f_out_txt.close()


# ф-ция обновления списка roots
def update_groups(remove_groups, append_groups, roots):
    for r in remove_groups:
        if r in roots:
            roots.remove(r)
    for r in append_groups:
        roots.append(r)

# ф-ция основного прохода для шагов 4-6
def groups_processing(roots, remove_groups, append_groups, func):
    for k in range(len(roots)-1):
        group = roots[k]
        if group not in remove_groups:
            append_group = group
            remove_groups.append(group)
            for root in append_group:
                append_group = [*append_group, *func(root, roots[k:], remove_groups)]
            append_groups.append(append_group)

# ф-ция поиска алломорфов с мягким знаком и -й- на конце
def end_letter_allomorphs(remove_groups, append_groups, roots):
    for group in roots:
        if len(group) == 1:
            r = group[0]
            if r[-1] == 'ь' or  r.endswith('ий'):
                allomorph = r[:-1]
                if [allomorph] in roots:
                    append_groups.append([allomorph, r])
                    remove_groups.append([allomorph])
                    remove_groups.append(group)

# ф-ция поиска уникальных корней
def unique_roots(data):
    res = []
    for line in data:
        morphs = extract_morphs(line)
        root = morphs['ROOT']
        if len(root) > 1:
            continue
        if root not in res:
            res.append(root)
    return res

def main_processing_roots(data):
    # список списков (каждый элемент - группа алломорфных корней)
    roots = []
    # группы корней для удаления
    remove_groups = []
    # группы корней для добавления
    append_groups = []

    start_time = time.time()
    print("Сбор групп алломорфных корней" + "\n")

    # 1. Выделение корней без алломорфов
    roots = unique_roots(data)

    print("Шаг 1: Число уникальных корней (без учёта алломорфов): ", len(roots))

    # 2. Проверка алломорфов по набору RuRoots_Allmorphs
    for root in roots:
        if root not in remove_groups:
            group = has_allomorphs(root[0])
            if group:
                for r in group:
                    remove_groups.append([r])
                append_groups.append(group)

    update_groups(remove_groups, append_groups, roots)

    print("Шаг 2: Число групп алломорфных корней: ", len(roots))

    # 3. Поиск корней по типу: автомобил - автомобиль и бактери - бактерий
    remove_groups = []
    append_groups = []

    end_letter_allomorphs(remove_groups, append_groups, roots)

    update_groups(remove_groups, append_groups, roots)

    print("Шаг 3: Число групп алломорфных корней: ", len(roots))

    # 4. Чередование согласных на конце корня 
    remove_groups = []
    append_groups = []

    groups_processing(roots, remove_groups, append_groups, end_alternations_search)
    update_groups(remove_groups, append_groups, roots)

    print("Шаг 4: Число групп алломорфных корней: ", len(roots))

    # 5. Наращивание согласной на конце корня
    remove_groups = []
    append_groups = []

    groups_processing(roots, remove_groups, append_groups, end_augmentations_search)
    update_groups(remove_groups, append_groups, roots)

    print("Шаг 5: Число групп алломорфных корней: ", len(roots))

    # 6. Чередование гласных
    remove_groups = []
    append_groups = []

    groups_processing(roots, remove_groups, append_groups, vowel_search)
    update_groups(remove_groups, append_groups, roots)
    
    print("Шаг 6: Число групп алломорфных корней: ", len(roots))

    print_roots(roots)

    print("--- %s seconds ---\n" % (time.time() - start_time))
    print("Сбор групп алломорфных корней закончен" + "\n")