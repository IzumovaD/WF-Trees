import time
import json
import pymorphy2

# суффиксы уменьшительно-ласкательных существительных
diminutive_nouns_suffs = ['еньк', 'оньк', 'ик', 'ек', 'к', 'ок', 'ец', 'иц', 'очк', 'ечк', 'ышк', 'ишк', 'ушк', 'юшк']
# суффиксы увеличительных существительных
magnifying_nouns_suffs = ['ищ', 'ин']
# суффиксы отвлечённых существительных
abstract_nouns_suffs = ['ость', 'ств', 'от', 'ени']
# суффиксы существительных, обозначающих названия лиц по действию
nouns_persons_by_action_suffs = ['тель', 'чик', 'ист']
# суффиксы уменьшительно-ласкательных прилагательных
diminutive_adjectives_suffs = ['еньк', 'оньк']
# суффиксы увеличительных прилагательных
magnifying_adjectives_suffs = ['ущ', 'ющ']
# суффиксы глаголов, обозначающих однократное действие
single_action_verbs_suffs = ['ну']
# суффиксы глаголов, обозначающих многократное действие
repeated_action_verbs_suffs = ['ива', 'ыва']
# приставки отрицания
negative_prefs = ['не', 'анти']
# постфиксы возвратных глаголов, причастий и деепричастий
reflexive_postfix = ['ся', 'сь']
# интерфиксы глаголов
infixes = ['а', 'я', 'е', 'и', 'о']
# формообразующие суффиксы инфинитивов
form_suffs = ['ти', 'ть', 'чь']

# функция выделения морфем в слове
def morph_selection(word, pos_tags):
    # игнорируем окончания, соединительные гласные и дефисы
    res = {"PREF": [], "ROOT": [], "SUFF": [], "POSTFIX": []}
    temp = word.split("/")
    for morph in temp:
        morph = morph.split(":")
        if "PREF" in morph[1]:
            res["PREF"].append(morph[0])
        if "ROOT" in morph[1]:
            res["ROOT"].append(morph[0])
        if "SUFF" in morph[1]:
            res["SUFF"].append(morph[0])
        if "POSTFIX" in morph[1]:
            res["POSTFIX"].append(morph[0])
    to_delete = -1
    # не учитываем интерфиксы
    for i in range(0, len(res["SUFF"])):
        if (res["SUFF"][i] in infixes) and (i != len(res["SUFF"]) - 1):
            to_delete = i
    if to_delete >= 0:
        del res["SUFF"][to_delete]
    # не учитываем формообразующие суффиксы у инфинитивов
    if pos_tags[word] == "VERB":
        if res["SUFF"][len(res["SUFF"])-1] in form_suffs:
            del res["SUFF"][len(res["SUFF"])-1]
    # удаление мягкого знака на конце суффикса (чередующиеся суффиксы - л/ль, ост/ость и т.д)
    for i in range(len(res["SUFF"])):
        if res["SUFF"][i][-1] == 'ь':
            res["SUFF"][i] = res["SUFF"][i][:-1]
    return res

# функция определения части речи слова
def search_pos(word, morph):
    all_poses = []
    tmp = morph.parse(word)
    for elem in tmp:
        all_poses.append(elem.tag.POS)
    if ("PRTF" in all_poses) or ("PRTS" in all_poses):
        # причастие
        return "PARTICIPLE"
    if "NUMR" in all_poses:
        # числительное
        return "NUMR"
    if "GRND" in all_poses:
        # деепричастие
        return "ADV PARTICIPLE"
    if ("ADJF" in all_poses) or ("ADJS" in all_poses):
        # прилагательное
        return "ADJ"
    if "NOUN" in all_poses:
        # существительное
        return "NOUN"
    if ("INFN" in all_poses) or ("VERB" in all_poses):
        # глагол
        return "VERB"
    # наречие в остальных случаях
    return "ADVERB"

# функция приведения слова к обычному виду (без разделения на морфемы)
def modify_word(word):
    word = word.replace("/", "")
    word = word.replace(":", "")
    for letter in [chr(x) for x in range(65,90)]:
        while letter in word:
            word = word.replace(letter,'')
    return word

# функция определения частей речи группы слов
def identify_pos(nest, morph):
    res = {}
    for elem in nest:
        word = modify_word(elem)
        res[elem] = search_pos(word, morph)
    return res

# функция, оставляющая только слова минимальной длины
def discard_applicants(words):
    min_len = 1
    # множество со словами минимальной длины
    res = set()
    while 1:
        for word in words:
            # приводим слово к обычному виду
            modif_word = modify_word(word)
            # не учитываем мягкий и твёрдый знаки
            modif_word = modif_word.replace("ь", "")
            modif_word = modif_word.replace("ъ", "")
            if len(modif_word) == min_len:
                res.add(word)
        if len(res) != 0:
            break
        min_len += 1
    return res

# функция отбора вершины СГ
def search_vertex(nest, pos_tags):
    # максимальное число морфем (окончание не считаем)
    max_morphs = 1
    # текущие претенденты на вершину СГ
    applicants = set()
    while 1:
        for word in nest:
            morphs = morph_selection(word, pos_tags)
            # если число морфем в слове минимально для данной группы
            if len(morphs["PREF"]) + len(morphs["ROOT"]) + len(morphs["SUFF"]) + len(morphs["POSTFIX"]) == max_morphs:
                applicants.add(word)
        if len(applicants) != 0:
            break
        max_morphs += 1
    # если нашёлся только один кандидат
    if len(applicants) == 1:
        return applicants.pop()
    # оставляем только кандидатов с наименьшим количеством букв
    applicants = discard_applicants(applicants)
    if len(applicants) == 1:
        return applicants.pop()
    # 1-й приоритет - глаголы
    for word in applicants:
        # берём случайный
        if pos_tags[word] == "VERB":
            return word
    # 2-й приоритет - существительные
    for word in applicants:
        if pos_tags[word] == "NOUN":
            return word
    # 3-й приоритет - прилагательные/причастия
    for word in applicants:
        if (pos_tags[word] == "ADJ" or
            pos_tags[word] == "PARTICIPLE"):
            return word
    # 4-й приоритет - наречия/деепричастия
    return applicants.pop()

# функция поиска простых слов по суффиксам
def search_words_by_suffs(nest, suffs, pos_tags, pos):
    res = []
    for word in nest:
        if pos_tags[word] == pos:
            morphs = morph_selection(word, pos_tags)
            for suff in suffs:
                if suff in morphs["SUFF"]:
                    res.append(word)
                    break
    return res

# функция поиска простых слов c префиксами отрицания
def search_negative_words(nest, pos_tags, pos):
    res = []
    for word in nest:
        if pos_tags[word] == pos:
            morphs = morph_selection(word, pos_tags)
            if len(morphs["PREF"]) != 0:
                if morphs["PREF"][0] in negative_prefs:
                    res.append(word)
    return res

# функция поиска простых слов по постфиксам
def search_words_by_postfix(nest, postfixes, pos_tags, pos):
    res = []
    for word in nest:
        if pos_tags[word] == pos:
            morphs = morph_selection(word, pos_tags)
            for postfix in postfixes:
                if postfix in morphs["POSTFIX"]:
                    res.append(word)
                    break
    return res

# функция поиска простых глаголов несовершенного вида
def search_imperfective_verbs(nest, morph, pos_tags):
    res = []
    for word in nest:
        if pos_tags[word] == "VERB":
            modif_word = modify_word(word)
            tags = morph.parse(modif_word)[0]
            # проверяем вид глагола
            if tags.tag.aspect == "impf":
                res.append(word)
    return res

# функция, возвращающая True, если child отличается от parent только добавлением одного любого морфа (или если разницы нет)
def diff_1_any(parent, child):
    diff = 0
    for morphs in parent:
        if morphs == "PREF":
            if len(child[morphs]) - len(parent[morphs]) > 0:
                for i in range(len(parent[morphs])):
                    if parent[morphs][i] != child[morphs][i+1]:
                        return False
            elif len(child[morphs]) == len(parent[morphs]):
                for i in range(len(parent[morphs])):
                    if parent[morphs][i] != child[morphs][i]:
                        return False
            else: 
                return False
            diff += len(child[morphs]) - len(parent[morphs])
            if diff > 1: 
                return False
        # может быть алломорфный корень
        elif morphs != "ROOT":
            for elem in parent[morphs]:
                if not (elem in child[morphs]):
                    return False
            diff += len(child[morphs]) - len(parent[morphs])
            if diff > 1: 
                return False
    if diff == 1 or diff == 0:
        return True
    else:
        return False
    
# функция, возвращающая True, если child отличается от parent только добавлением одного конкретного морфа (или если разницы нет)
def diff_1(parent, child, morph):
    diff = 0
    # для постфикса нужно сразу проверить корень (вариант не допускается)
    if morph == "POSTFIX":
        if parent["ROOT"] != child["ROOT"]:
            return False
    for morphs in parent:
        if morphs != morph and morphs != "ROOT":
            for elem in parent[morphs]:
                if not (elem in child[morphs]):
                    return False
            if len(child[morphs]) != len(parent[morphs]):
                return False
        # если указанный аффикс - приставка
        elif morphs == morph == "PREF":
            if len(child[morphs]) - len(parent[morphs]) > 0:
                # приставка может наращиваться только слева
                for i in range(len(parent[morphs])):
                    if parent[morphs][i] != child[morphs][i+1]:
                        return False
            elif len(child[morphs]) == len(parent[morphs]):
                for i in range(len(parent[morphs])):
                    if parent[morphs][i] != child[morphs][i]:
                        return False
            else: 
                return False
            diff = len(child[morphs]) - len(parent[morphs])
            if diff > 1: 
                return False
        # если указанный аффикс - суффикс или постфикс
        elif morphs == morph:
            for elem in parent[morphs]:
                if not (elem in child[morphs]):
                    return False
            diff = len(child[morphs]) - len(parent[morphs])
            if diff > 1: 
                return False
    if diff != 1 and diff != 0:
        return False
    return True

# функция поиска производного слова для простого существительного
def search_derivate_for_noun(morphs_key, nest, diminutive_nouns, magnifying_nouns, negative_pref_nouns,
                             negative_pref_adjectives, negative_pref_verbs, reflexive_verbs, pos_tags, proc_words):
    childs = []
    # 1. уменьшительно-ласкательные существительные
    for word in diminutive_nouns:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 2. увеличительные существительные
    for word in magnifying_nouns:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 3. существительные, образованные только с помощью суффиксов
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not ((word in diminutive_nouns) or (word in magnifying_nouns)
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "SUFF"):
                    childs.append(word)
                    proc_words.append(word)
    # 4. а) прилагательные, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not ((word in proc_words) or (word in negative_pref_adjectives)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 4. б) прилагательные, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_adjectives:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    # 4. в) остальные прилагательные
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 5. наречия
    for word in nest:
        if pos_tags[word] == "ADVERB":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 6. а) существительные, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not ((word in diminutive_nouns) or (word in magnifying_nouns) or (word in negative_pref_nouns) 
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 6. б) существительные, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_nouns:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    # 7. а) глаголы, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "VERB":
            if not ((word in proc_words) or (word in negative_pref_verbs) or (word in reflexive_verbs)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 7. б) глаголы, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_verbs:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    # 7. в) остальные глаголы
    for word in nest:
        if pos_tags[word] == "VERB":
            if not ((word in proc_words) or (word in reflexive_verbs)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    return childs

# функция поиска производного слова для простого прилагательного
def search_derivate_for_adj(morphs_key, nest, diminutive_adjectives, 
                            magnifying_adjectives, negative_pref_adjectives, 
                            negative_pref_nouns, pos_tags, proc_words):
    childs = []
    # 1. уменьшительно-ласкательные прилагательные
    for word in diminutive_adjectives:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 2. увеличительные прилагательные
    for word in magnifying_adjectives:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 3. прилагательные, образованные только с помощью суффиксов
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not ((word in diminutive_adjectives) or (word in magnifying_adjectives)
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "SUFF"):
                    childs.append(word)
                    proc_words.append(word)
    # 4. наречия
    for word in nest:
        if pos_tags[word] == "ADVERB":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 5. а) существительные, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not ((word in proc_words) or (word in negative_pref_nouns)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 5. б) существительные, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_nouns:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    # 5. в) остальные существительные
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 6. а) прилагательные, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not ((word in diminutive_adjectives) or (word in magnifying_adjectives) or (word in negative_pref_adjectives) 
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 6. б) прилагательные, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_adjectives:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    return childs

# функция поиска производного слова для простого глагола
def search_derivate_for_verb(morphs_key, nest, reflexive_verbs, reflexive_adv_participles,
                            reflexive_participles, imperfective_verbs,
                            single_action_verbs, repeated_action_verbs,
                            abstract_nouns, nouns_persons_by_action, 
                            negative_pref_verbs, pos_tags, proc_words):
    childs = []
    # 1. возвратные глаголы
    for word in reflexive_verbs:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "POSTFIX"):
                childs.append(word)
                proc_words.append(word)
    # 2. глаголы несовершенного вида, образованные с помощью суффиксов
    for word in imperfective_verbs:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "SUFF"):
                childs.append(word)
                proc_words.append(word)
    # 3. глаголы, обозначающие однократное действие
    for word in single_action_verbs:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 4. глаголы, обозначающие многократное действие
    for word in repeated_action_verbs:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 5. остальные глаголы, образованные с помощью суффиксов
    for word in nest:
        if pos_tags[word] == "VERB":
            if not ((word in reflexive_verbs) or (word in imperfective_verbs) or (word in single_action_verbs)
                    or (word in repeated_action_verbs) or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "SUFF"):
                    childs.append(word)
                    proc_words.append(word)
    # 6. а) глаголы, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "VERB":
            if not ((word in reflexive_verbs) or (word in imperfective_verbs) or (word in single_action_verbs)
                    or (word in repeated_action_verbs)  or (word in negative_pref_verbs) 
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 6. б) глаголы, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_verbs:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    # 7. причастия
    for word in nest:
        if pos_tags[word] == "PARTICIPLE":
            if not ((word in proc_words) or (word in reflexive_participles)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 8. деепричастия
    for word in nest:
        if pos_tags[word] == "ADV PARTICIPLE":
            if not ((word in proc_words) or (word in reflexive_adv_participles)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 9. отвлечённые существительные
    for word in abstract_nouns:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 10. существительные, обозначающие названия лиц по действию
    for word in nouns_persons_by_action:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1_any(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    # 11. остальные существительные
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not ((word in abstract_nouns) or (word in nouns_persons_by_action)
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 12. прилагательные
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 13. наречия
    for word in nest:
        if pos_tags[word] == "ADVERB":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    return childs

# функция поиска производного слова для простого наречия
def search_derivate_for_adverb(morphs_key, nest, pos_tags, proc_words, reflexive_verbs):
    childs = []
    # 1. прилагательные
    for word in nest:
        if pos_tags[word] == "ADJ":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 2. наречия
    for word in nest:
        if pos_tags[word] == "ADVERB":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 3. существительные
    for word in nest:
        if pos_tags[word] == "NOUN":
            if not (word in proc_words):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    # 4. глаголы
    for word in nest:
        if pos_tags[word] == "VERB":
            if not ((word in proc_words) or (word in reflexive_verbs)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1_any(morphs_key, morphs_word):
                    childs.append(word)
                    proc_words.append(word)
    return childs

# функция поиска производного слова для простого деепричастия
def search_derivate_for_adv_participle(morphs_key, nest,
                                        reflexive_adv_participles, negative_pref_adv_participles,
                                        pos_tags, proc_words):
    childs = []
    # 1. возвратные деепричастия
    for word in reflexive_adv_participles:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "POSTFIX"):
                childs.append(word)
                proc_words.append(word)
    # 2. а) деепричастия, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "ADV PARTICIPLE":
            if not ((word in reflexive_adv_participles) or (word in negative_pref_adv_participles) 
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 2. б) деепричастия, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_adv_participles:
        if not ((word in proc_words) or (word in reflexive_adv_participles)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    return childs

# функция поиска производного слова для простого причастия
def search_derivate_for_participle(morphs_key, nest,
                                    reflexive_participles, negative_pref_participles,
                                    pos_tags, proc_words):
    childs = []
    # 1. возвратные причастия
    for word in reflexive_participles:
        if not (word in proc_words):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "POSTFIX"):
                childs.append(word)
                proc_words.append(word)
    # 2. а) причастия, образованные только с помощью приставок (кроме НЕ и АНТИ)
    for word in nest:
        if pos_tags[word] == "PARTICIPLE":
            if not ((word in reflexive_participles) or (word in negative_pref_participles) 
                    or (word in proc_words)):
                morphs_word = morph_selection(word, pos_tags)
                if diff_1(morphs_key, morphs_word, "PREF"):
                    childs.append(word)
                    proc_words.append(word)
    # 2. б) причастия, образованные только с помощью приставок НЕ и АНТИ
    for word in negative_pref_participles:
        if not ((word in proc_words) or (word in reflexive_participles)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_1(morphs_key, morphs_word, "PREF"):
                childs.append(word)
                proc_words.append(word)
    return childs

# функция формирования словообразовательных цепочек (с разницей в одну морфему, учитываем только добавление аффиксов)
def search_derivate_1(parrent_words, proc_words, nest, diminutive_nouns, magnifying_nouns, 
                    diminutive_adjectives, magnifying_adjectives, reflexive_verbs, 
                    reflexive_adv_participles, reflexive_participles,
                    imperfective_verbs, single_action_verbs, repeated_action_verbs,
                    abstract_nouns, nouns_persons_by_action, negative_pref_nouns, 
                    negative_pref_adjectives, negative_pref_verbs, negative_pref_adv_participles, 
                    negative_pref_participles, pos_tags):
    for key in parrent_words:
        childs = []
        # если это лист дерева
        if len(parrent_words[key]) == 0:
            # производящее слово - существительное
            if pos_tags[key] == "NOUN":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_noun(morphs_key, nest, diminutive_nouns, 
                                                  magnifying_nouns, negative_pref_nouns, 
                                                  negative_pref_adjectives, negative_pref_verbs, reflexive_verbs,
                                                  pos_tags, proc_words)
            # производящее слово - прилагательное
            if pos_tags[key] == "ADJ":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_adj(morphs_key, nest, diminutive_adjectives, 
                                                            magnifying_adjectives, negative_pref_adjectives, 
                                                            negative_pref_nouns, pos_tags, proc_words)
            # производящее слово - глагол
            if pos_tags[key] == "VERB":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_verb(morphs_key, nest, reflexive_verbs, reflexive_adv_participles,
                                                          reflexive_participles, imperfective_verbs,
                                                          single_action_verbs, repeated_action_verbs,
                                                          abstract_nouns, nouns_persons_by_action, 
                                                          negative_pref_verbs, pos_tags, proc_words)
            # производящее слово - наречие
            if pos_tags[key] == "ADVERB":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_adverb(morphs_key, nest, pos_tags, proc_words, reflexive_verbs)
            # производящее слово - деепричастие
            if pos_tags[key] == "ADV PARTICIPLE":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_adv_participle(morphs_key, nest,
                                                                        reflexive_adv_participles, negative_pref_adv_participles,
                                                                        pos_tags, proc_words)
            # производящее слово - причастие
            if pos_tags[key] == "PARTICIPLE":
                morphs_key = morph_selection(key, pos_tags)
                childs = search_derivate_for_participle(morphs_key, nest,
                                                                    reflexive_participles, negative_pref_participles,
                                                                    pos_tags, proc_words)
        if len(childs) != 0:
            for child in childs:
                parrent_words[key].append(child)
    for word in proc_words:
        if not (word in parrent_words):
            parrent_words.update({word: []})
        if word in nest:
            nest.remove(word)

# функция, возвращающая True, если child отличается от parent только добавлением одной приставки и одного суффикса или
# одной приставки и одного постфикса
def diff_2(parent, child):
    diff = 0
    for morphs in parent:
        if morphs == "PREF":
            if len(child[morphs]) - len(parent[morphs]) != 1:
                return False
            for i in range(len(parent[morphs])):
                if parent[morphs][i] != child[morphs][i+1]:
                    return False
            diff = 1
        elif morphs == "SUFF" or morphs == "POSTFIX":
            if len(child[morphs]) - len(parent[morphs]) < 0:
                return False
            for elem in parent[morphs]:
                if not (elem in child[morphs]):
                    return False
            diff += len(child[morphs]) - len(parent[morphs])
    if diff != 2:
        return False
    return True

# функция поиска производного слова, образованного с помощью одной приставки и одного суффикса
def search_derivate_for_word_2(morphs_key, nest, pos_tags, proc_words, reflexive_verbs):
    childs = []
    for word in nest:
        if not ((word in proc_words) or (word in reflexive_verbs)):
            morphs_word = morph_selection(word, pos_tags)
            if diff_2(morphs_key, morphs_word):
                childs.append(word)
                proc_words.append(word)
    return childs

# функция формирования словообразовательных цепочек (с разницей в 2 морфемы: приставка + суффикс или приставка + постфикс)
def search_derivate_2(parrent_words, proc_words, reflexive_verbs, nest, pos_tags):
    for key in parrent_words:
        childs = []
        # производящее слово - существительное, прилагательное или глагол
        if pos_tags[key] in ("NOUN", "ADJ", "VERB"):
            morphs_key = morph_selection(key, pos_tags)
            if len(morphs_key["ROOT"]) == 1:
                childs = search_derivate_for_word_2(morphs_key, nest,
                                                    pos_tags, proc_words, reflexive_verbs)
        if len(childs) != 0:
            for child in childs:
                parrent_words[key].append(child)
    for word in proc_words:
        if not (word in parrent_words):
            parrent_words.update({word: []})
        if word in nest:
            nest.remove(word)

# функция обработки словообразовательного гнезда (СГ)
def nest_processing(vertices, custom_vertices, nest, undistributed_words, morph):
    # словарь, где ключ (производящее слово) - строка, а значение (производные слова) - список строк
    res = {}
    # список обработанных слов
    proc_words = []
    #проставляем словам части речи,
    #получаем словарь, где ключ - слово из nest (не приведённое к обычному виду и не разбитое на словарь морфов), 
    # а значение - его часть речи
    pos_tags = identify_pos(nest, morph)
    # удаляем из гнезда числительные (кроме порядковых - они считаются прилагательными)
    for word in pos_tags:
        if pos_tags[word] == "NUMR":
            nest.discard(word)
    vertex = ''
    # проверяем, выбрана ли уже вершина для дерева
    for line in custom_vertices:
        line = line.replace('\n','')
        if line in nest:
            vertex = line
    # если не выбрана
    if vertex == '':
        # поиск вершины СГ функцией
        vertex = search_vertex(nest, pos_tags)
    res.update({vertex : []})
    vertices.append(vertex)
    nest.remove(vertex)
    # ниже - списки строк
    # уменьшительно-ласкательные существительные
    diminutive_nouns = search_words_by_suffs(nest, diminutive_nouns_suffs, pos_tags, "NOUN")
    # увеличительные существительные
    magnifying_nouns = search_words_by_suffs(nest, magnifying_nouns_suffs, pos_tags, "NOUN")
    # уменьшительно-ласкательные прилагательные
    diminutive_adjectives = search_words_by_suffs(nest, diminutive_adjectives_suffs, pos_tags, "ADJ")
    # увеличительные прилагательные
    magnifying_adjectives = search_words_by_suffs(nest, magnifying_adjectives_suffs, pos_tags, "ADJ")
    # возвратные глаголы
    reflexive_verbs = search_words_by_postfix(nest, reflexive_postfix, pos_tags, "VERB")
    # возвратные деепричастия
    reflexive_adv_participles = search_words_by_postfix(nest, reflexive_postfix, pos_tags, "ADV PARTICIPLE")
    # возвратные причастия
    reflexive_participles = search_words_by_postfix(nest, reflexive_postfix, pos_tags, "PARTICIPLE")
    # глаголы несовершенного вида
    imperfective_verbs = search_imperfective_verbs(nest, morph, pos_tags)
    # глаголы, обозначающие однократное действие
    single_action_verbs = search_words_by_suffs(nest, single_action_verbs_suffs, pos_tags, "VERB")
    # глаголы, обозначающие многократное действие
    repeated_action_verbs = search_words_by_suffs(nest, repeated_action_verbs_suffs, pos_tags, "VERB")
    # отвлечённые существительные
    abstract_nouns = search_words_by_suffs(nest, abstract_nouns_suffs, pos_tags, "NOUN")
    # существительные, обозначающие названия лиц по действию)
    nouns_persons_by_action = search_words_by_suffs(nest, nouns_persons_by_action_suffs, pos_tags, "NOUN")
    # существительные с префиксами отрицания
    negative_pref_nouns = search_negative_words(nest, pos_tags, "NOUN")
    # прилагательные с префиксами отрицания
    negative_pref_adjectives = search_negative_words(nest, pos_tags, "ADJ")
    # глаголы с префиксами отрицания
    negative_pref_verbs = search_negative_words(nest, pos_tags, "VERB")
    # деепричастия с префиксами отрицания
    negative_pref_adv_participles = search_negative_words(nest, pos_tags, "ADV PARTICIPLE")
    # причастия с префиксами отрицания
    negative_pref_participles = search_negative_words(nest, pos_tags, "PARTICIPLE")
    # выполняем, пока все слова не будут распределены по словообразоват. цепочкам или больше ничего никуда нельзя присоединить 
    # с разницей в 1 морфему
    while len(nest) != 0:
        while len(nest) != 0:
            old_len = len(nest)
            search_derivate_1(res, proc_words, nest, diminutive_nouns, magnifying_nouns, 
                            diminutive_adjectives, magnifying_adjectives, reflexive_verbs, 
                            reflexive_adv_participles, reflexive_participles,
                            imperfective_verbs, single_action_verbs, repeated_action_verbs,
                            abstract_nouns, nouns_persons_by_action, negative_pref_nouns, negative_pref_adjectives,
                            negative_pref_verbs, negative_pref_adv_participles, negative_pref_participles, pos_tags)
            if old_len - len(nest) == 0:
                break
        old_len = len(nest)
        # учитываем разницу в 2 морфемы: приставка + суффикс или приставка + постфикс
        search_derivate_2(res, proc_words, reflexive_verbs, nest, pos_tags)
        if old_len - len(nest) == 0:
                break
    # оставшиеся нераспределенными слова
    undistributed_words.append(nest)
    return res

# основная функция обработки всех групп однокоренных слов
def main_processing(data, custom_vertices):
     # список списков, каждый список - нераспределнные в дереве слова
    undistributed_words = []
    start_time = time.time()
    morph = pymorphy2.MorphAnalyzer()
    # словообразовательные гнёзда - массив словарей, где в каждом словаре ключ - это
    # слово, а значение - массив производных от него слов
    # кроме того, есть отдельный элемент с ключом "vertex", хранящий вершину СГ
    word_formation_nests = []
    # массив вершин СГ
    vertices = []
    for nest in data:
        # слова в каждом гнезде сортируем в алфавитном порядке
        nest.sort()
        # обработка текущей группы слов
        word_formation_nests.append(nest_processing(vertices, custom_vertices, nest, undistributed_words, morph))

    filename = 'trees.json'
    with open(filename, 'w') as f:
        json.dump(word_formation_nests, f)

    print_nests_in_file(word_formation_nests, vertices, undistributed_words)
    print("--- %s seconds ---\n" % (time.time() - start_time))
    print("Общее число деревьев: ", len(data))

# функция печати одного гнезда
def print_nest(nest, key, k):
    res = ""
    #отступ для отдельного уровня
    tab = "   "
    for word in nest[key]:
        #печать отступа
        for i in range(0, k):
            res += tab
        res += word + "\n" + print_nest(nest, word, k + 1)
    return res

# функция печати всех построенных гнёзд в файл
def print_nests_in_file(word_formation_nests, vertices, undistributed_words):
    #печать СГ в файл
    string = ""
    for i, vertex in enumerate(vertices):
        string += "---------------------------------------------------" + "\n"
        #вершину СГ печатаем без отступа
        string += vertex + "\n"
        string += print_nest(word_formation_nests[i], vertex, 1)
        string += "\n" + "\n"
        string += "Оставшиеся нераспределёнными слова:" + "\n"
        for word in undistributed_words[i]:
            string += word + "\n"
    with open("trees.txt", "w") as out_file:
        out_file.write(string)
