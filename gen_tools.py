import random
from itertools import permutations
from combinatorics import genera_combinazioni, gen_constrained_choices, genera_varianti_scelte

COMPLETE_STATEMENTS ="complete_statements" # this is a key useful only inside the program

def convert_to_dictionary(risp, lab):
    statements = risp[lab["statements"]]
    has_non_dict = any(
        not isinstance(elemento, dict)
        for group in statements.values()
        for elemento in group
    )
    if has_non_dict:
        newstatements = {}
        for group_label, group in zip(statements.keys(),statements.values()):
            newstatements[group_label] = []
            for element in group:
                if not isinstance(element, dict):
                    newelement = {}
                    newelement[lab["statement"]] = element
                    if lab["group_fractions"] in risp.keys() and group_label in risp[lab["group_fractions"]].keys():
                        newelement[lab["correct"]] = risp[lab["group_fractions"]][group_label]
                    elif lab["group_fractions"] in risp.keys() and not group_label in risp[lab["group_fractions"]].keys():
                        newelement[lab["correct"]] = 0
                    else:
                        newelement[lab["correct"]] = group_label
                else:
                    newelement = element
                newstatements[group_label].append(newelement)
        return newstatements
    return statements

def genera_template(risp, nomifile,lab):

    with open(nomifile["template_"+risp[lab["question_type"]]], 'r') as template_file:
        template = template_file.read()

    template = template.replace("__PHNOMEDOMANDA", risp[lab["question_name"]])
    template = template.replace("_PHCONSEGNA", risp[lab["task"]])

    affermazioni = "__PHAFFERMAZIONE"
    itemized = (lab["options"] in risp.keys() and lab["itemized"] in risp[lab["options"]])
    range_phaffermazione_start =0
    if risp[lab["question_type"]] == "mcq":
        itemized=False
        range_phaffermazione_start = 1
    if itemized:
        affermazioni = affermazioni.replace("__PHAFFERMAZIONE","<ul> \n__PHAFF_LISTA \n\t</ul>" )
    for i in range(range_phaffermazione_start, int(risp[lab["number_of_statements"]])):
        affermazioni = affermazioni.replace("__PHAFF_LISTA", "\n\t<li> AFFERMAZIONE"+str(i)+"</li>__PHAFF_LISTA")
        affermazioni = affermazioni.replace("__PHAFFERMAZIONE", "\n\tAFFERMAZIONE"+str(i)+"__PHAFFERMAZIONE")
    affermazioni = affermazioni.replace("__PHAFFERMAZIONE", "")
    affermazioni = affermazioni.replace("__PHAFF_LISTA", "")
    template = template.replace("__PHELENCOAFFERMAZIONI",affermazioni)

    if lab["options"] in risp.keys() and lab["moodle_shuffle"] in risp[lab["options"]]:
        template = template.replace("__PHSHUFFLE", "1")
    else:
        template = template.replace("__PHSHUFFLE", "0")

    if risp[lab["question_type"]] == "dd":
        with open(nomifile["template_dragbox"], 'r') as template_dragbox_file:
            template_db = template_dragbox_file.read()
        for key, filler in risp[lab["answers"]].items():
            infinite = ""
            if (lab["if_infinite"] in risp.keys()) and key in risp[lab["if_infinite"]].keys() and risp[lab["if_infinite"]][key].startswith("infi"):
                infinite = "<infinite/>"
            template_db_inst = template_db.replace("__PHDRAGBOX", filler).replace("__PHIFINFINITE",infinite)
            template = template.replace("__PHDRAGBOXES", template_db_inst + "\n__PHDRAGBOXES")
        template = template.replace("__PHDRAGBOXES", "")

    # print(template)

    return template

def complete_answers(risp,nomifile,lab):
    template_affermazioni = ""
    if risp[lab["question_type"]] == "mcq":
        with open(nomifile["template_MCQ_answers"], 'r') as template_mcq_an_file:
            template_affermazioni = template_mcq_an_file.read()
    for group in risp[lab["statements"]].keys():
        risp[COMPLETE_STATEMENTS][group] = []
        for rich_statement in risp[lab["statements"]][group]:
            if risp[lab["question_type"]] == "dd" and not risp[lab["answers_placeholder"]] in rich_statement[lab["statement"]]:
                # here we must add the '[[number]]' at the end; it is in the 'corretta' field
                risp[COMPLETE_STATEMENTS][group].append(rich_statement[lab["statement"]]  + ": [[" + rich_statement[lab["correct"]] + "]]")
            elif risp[lab["question_type"]] == "dd":
                risp[COMPLETE_STATEMENTS][group].append(
                    rich_statement[lab["statement"]].replace(risp[lab["answers_placeholder"]],"[[" + rich_statement[lab["correct"]] + "]]"))
            elif risp[lab["question_type"]] == "mcq":
                if group != "1": # poiché il gruppo 1 per mcq è la domanda, deve rimanere cosí com'è e non prendere la struttura di una risposta (vedi dopo)
                    tmp = template_affermazioni
                    risp[COMPLETE_STATEMENTS][group].append(
                        tmp.replace("__PHAFFERMAZIONE", rich_statement[lab["statement"]]).replace("__PHFRACTION",
                                                                                           rich_statement[lab["correct"]]))
            elif risp[lab["question_type"]] == "cloze" and risp[lab["cloze_type"]] == "SHORTANSWER":
                # # if it is a SHORTANSWER kind of cloze, the answer is already composed in the filler, 'correct' says which is the placeholder and the correct filler
                # risp[COMPLETE_STATEMENTS][group].append(rich_statement[lab["statement"]].replace(rich_statement[lab["correct"]],risp[lab["answers"]][rich_statement[lab["correct"]]]))
                risp[COMPLETE_STATEMENTS][group].append(rich_statement[lab["statement"]].replace(risp[lab["answers_placeholder"]],
                                                                                              risp[lab["answers"]][
                                                                                                  group]))
            elif risp[lab["question_type"]] == "cloze":
                # this is the case of single answer: here we build the correct cloze answer string using the 'correct' field to indicate which among the answers is the correct answer (it gets an '=')
                answer = "{:" + risp[lab["cloze_type"]] + ":__PHOPZIONE}"
                for chiave, opzione in risp[lab["answers"]].items():
                    if rich_statement[lab["correct"]] == chiave:
                        answer = answer.replace("__PHOPZIONE", "=" + opzione + "~__PHOPZIONE")
                    else:
                        answer = answer.replace("__PHOPZIONE", opzione + "~__PHOPZIONE")
                answer = answer.replace("~__PHOPZIONE", "")
                risp[COMPLETE_STATEMENTS][group].append(rich_statement[lab["statement"]] + " "+ answer)
        if risp[lab["question_type"]] == "mcq":# poiché il gruppo 1 per mcq è la domanda, deve rimanere cosí com'è e non prendere la struttura di una risposta
                    # però in verify anche il gruppo 1 è stato trasformato in dictionary, e lo voglio di nuovo una lista
                    # (ha senso questo avanti e dietro? lo avevo fatto per uniformità)
            risp[COMPLETE_STATEMENTS]["1"] = [rich_answer[lab["statement"]] for rich_answer in risp[lab["statements"]]["1"]]

# def is_mcq_single(choice, risp):
#     if sum(int(choice[i]) for i in range(2,len(choice)) if float(risp[lab["group_fraction"]]) > 0) > 1:
#         return False
#     return True

def prepare_questions(risp, template,lab):
    tutte_le_domande = ""

    groups_dimensions = [len(risp[lab["statements"]][group]) for group in risp[lab["statements"]].keys()]

    # if choices are specified in the JSON file, let's ude them
    # if not, generation might be constrained
    #  if not, all possible choices are generated
    if lab["choices"] in risp.keys() and len(risp[lab["choices"]]) != 0:
        varianti_scelte = risp[lab["choices"]]
    elif lab["computed_choices"] in risp.keys() and len(risp[lab["computed_choices"]]) != 0:
        varianti_scelte = gen_constrained_choices(risp[lab["computed_choices"]])
    else:
        varianti_scelte  = genera_varianti_scelte(groups_dimensions, int(risp[lab["number_of_statements"]]))

    number_of_statements = int(risp[lab["number_of_statements"]])

    perm = []
    if lab["options"] in risp.keys() and lab["all_orders"] in risp[lab["options"]]:
        # all permutations of the number of statements required, so each combination generates len(all_permutations) versions with the same question with items presented in different order
        perm = list(permutations(list(range(number_of_statements))))

    elif risp[lab["question_type"]] == "mcq":
        #  here I need no permutation because an MCQ answer has always the first statement true (statements will be shuffled by moodle)
        perm = [list(range(number_of_statements))]

    numero_totale_domande = 0

    print("numero di alternative utilizzate per le scelte:", len(varianti_scelte))
    numero_perm = max(len(perm),1)
    print("\t\t numero di permutazioni per domanda:", numero_perm)

    conto = 0
    numero_q = 1
    for scelte in varianti_scelte:
        conto=conto+1
        # print("scelte:", scelte)
        combinations, where_from = genera_combinazioni(groups_dimensions, scelte, [])
        # print("COMBINAZIONI:",len(combinations))

        print(f"\t {conto} - numero di domande per {scelte}: {len(combinations)}, totale: {len(combinations) * numero_perm}")
        for comb in combinations:
            # statements' placeholders are substituted with actual sentences, permuting the sentences (or not) depending on "permutations"

            # here permutations is a single permutation, to avoid having questions from different groups always in the same order (if the groups are large all permutations are too many)
            #  this cannot be where permutations are generated above because a different permutation for each question is required
            if (not lab["options"] in risp.keys() or lab["all_orders"] not in risp[lab["options"]]) and risp[
                lab["question_type"]] != "mcq":
                shuffle = random.sample(list(range(number_of_statements)), number_of_statements)
                perm = [shuffle]

            for shuffle in perm:
                # copying template in a tmp var so it can be reused for the following sentences
                temp = template

                if (risp[lab["question_type"]] == "mcq" and
                        (lab["options"] in risp and lab["multiple"] in risp[lab["options"]] or sum(
                            1 for x in where_from[1:]
                            if str(x) in risp[lab["group_fractions"]]
                            and float(risp[lab["group_fractions"]][str(x)]) > 0) > 1)):
                    temp = temp.replace("__PHISSINGLE", "false")
                else:
                    temp = temp.replace("__PHISSINGLE", "true")

                temp = temp.replace("__PHNUMEROQ", str(numero_q))

                numero_q += 1
                for i in range(number_of_statements):
                    # picks one statement from the complete ones (a list of statements for each group); it uses "where_from" to determine the group, the combination to determine which one
                    statement = risp[COMPLETE_STATEMENTS][str(where_from[i])][comb[i]]
                    # the statement is copied in one of the placeholders, depending on the permutation (shuffle)
                    temp = temp.replace("AFFERMAZIONE" + str(shuffle[i]), statement)
                    # print(f"inquesta domanda sostituisco adesso l' AFFERMAZIONE{shuffle[i]} con la risposta da {where_from[i]}: {risp[COMPLETE_STATEMENTS][str(where_from[i])][comb[i]]}")
                tutte_le_domande = tutte_le_domande + "\n" + temp

        # print(numero_q-1, "domande generate")
        numero_totale_domande = numero_q - 1
    return tutte_le_domande, numero_totale_domande