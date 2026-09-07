from itertools import combinations, product
import sys

def genera_combinazioni(group_lens, choice, group_start):
    all_group_combs = []

    # generate combinations for each group, numbering elements from 0 to group_len -1
    # itertools.combinations gives all combinations of required elts from available ones
    # makes of them a list and then a list of lists for all groups

    # if the group_start is not specified, it defaults to 0 for all groups
    if len(group_start) == 0:
        group_start = [0 for i in group_lens]

    # available is the number of sentences in each group
    # required is how many we want from each group
    # group_start defines the index of the first item in the group
    for available, required, start in zip(group_lens, choice, group_start):
        # available names lists all names (indexes) available for the group
        available_names = range(start,available + start)
        # single_group_combs gives all sets of 'required' elts from each group, no repetitions
        single_group_combs = list(combinations(available_names, int(required)))
        # all_group_combs packs the single_group_combs in a list
        all_group_combs.append(single_group_combs)

    # the following code gives the cartesian product of the above combinations, as lists
    # itertools.product gives the cartesian product of a sequence of lists
    # the * unpacks the list of lists, providing to the method a sequence of lists
    # this produces a list ((0,), (1, 2), (0, 3)) (0 from first group, 1 and 2 from the second, 0 and 3 from the third)
    #  the result of the cartesian product must be "flattened" because we need a single list -> [0, 1, 2, 0, 3]
    #  the line 'flattened_list' means: make a list of 'index', and this inside two nested 'for' (for group and for index)
    final_combinations = []
    for combo_tuple in product(*all_group_combs):
        flattened_list = [index for group in combo_tuple for index in group]
        final_combinations.append(flattened_list)

    # It is necessary to remember where these items come from (the choice in input)
    # Looking again at the choice list, the list where_from says from which group the flattened_list indexes come from
    where_from = []
    group = 1
    for required in choice:
        for i in range(0,int(required)):
            where_from.append(group)
        group += 1

    return final_combinations, where_from

# this generates variants with 0 or 1 statements per group
def gen_constrained_choices (constraints):
    groups_numbers = [requirement["range"][1] - requirement["range"][0] + 1 for requirement in constraints]
    choice = [requirement["choices"] for requirement in constraints]
    group_start = [requirement["range"][0] for requirement in constraints]
    comb, _ = genera_combinazioni(groups_numbers, choice, group_start)
    # this returns a list of lists of length the sum of the required choices listing the groups from which the questions are to be taken

    max_group = max([requirement["range"][1] for requirement in constraints])
    all_choices = []

    for list in comb:
        tmp_choice = [0 for _ in range(max_group)]
        for group in list:
            tmp_choice[group-1]=1
        all_choices.append(tmp_choice)


    return all_choices

# copiato di sana pianta da gemini, da verificare
def genera_varianti_scelte(groups_dimensions, number_of_required_statements):
    """
    Trova tutte le combinazioni di numeri che rispettano i limiti di ogni gruppo
    e la cui somma è esattamente pari a somma_totale.

    :param groups_dimensions: Lista o tupla con la dimensione massima consentita per ogni gruppo.
    :param number_of_required_statements: La somma esatta che gli elementi della lista devono raggiungere.
    :return: Una lista di liste contenente tutte le combinazioni valide.
    """
    risultati = []

    def backtrack(indice_gruppo, somma_corrente, percorso_corrente):
        # Caso base: abbiamo assegnato un valore a tutti i gruppi
        if indice_gruppo == len(groups_dimensions):
            if somma_corrente == number_of_required_statements:
                risultati.append(list(percorso_corrente))
            return

        # Ottimizzazione (Pruning): se la somma rimasta da raggiungere supera la
        # capacità massima di tutti i gruppi rimanenti messi insieme, ci fermiamo.
        spazio_rimanente_massimo = sum(groups_dimensions[indice_gruppo:])
        if number_of_required_statements - somma_corrente > spazio_rimanente_massimo:
            return

        # Ottimizzazione 2: se la somma corrente ha già superato il totale desiderato, ci fermiamo.
        if somma_corrente > number_of_required_statements:
            return

        # Esploriamo tutte le scelte possibili per il gruppo corrente (da 0 al massimo del gruppo)
        limite_massimo = groups_dimensions[indice_gruppo]
        for valore in range(limite_massimo + 1):
            percorso_corrente.append(valore)
            backtrack(indice_gruppo + 1, somma_corrente + valore, percorso_corrente)
            percorso_corrente.pop()  # Backtrack (rimuove l'ultima scelta per provarne un'altra)

    # Avviamo la ricorsione partendo dal primo gruppo (indice 0) con somma 0
    backtrack(0, 0, [])
    return risultati