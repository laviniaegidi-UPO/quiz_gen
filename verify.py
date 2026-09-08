#
# Copyright 2026 Lavinia Egidi
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import sys

def error_message (msg):
    print("❌",msg)
    sys.exit(1)

def warning_message(msg):
    print("⚠️",msg)

def verify_field_existence (campi, keys):
    for campo in campi:
        if not (campo in keys):
            error_message(f"nel file manca il campo {campo}")

def verify_mcq_choices(risp, lab):
    for i in range(len(risp[lab["statements"]])):
        if str(i+1) not in risp[lab["group_fractions"]].keys():
            risp[lab["group_fractions"]][str(i+1)] = "0"
    for choice in risp[lab["choices"]]:
        if (choice[0] != 1):
            error_message(f"Nella scelta {choice} il primo elemento deve sempre essere '1' ed è invece {choice[0]}")
        somma = sum(int(choice[i])*float(risp[lab["group_fractions"]][str(i+1)]) for i in range(1,len(choice)) if float(risp[lab["group_fractions"]][str(i+1)]) > 0)
        if somma != 100:
            error_message(f"La somma delle frazioni delle risposte corrette deve essere 100. Per la scelta {choice} la somma è {somma}")

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
                    else:
                        newelement[lab["correct"]] = group_label
                else:
                    newelement = element
                newstatements[group_label].append(newelement)
        return newstatements
    return statements

def verifica(risp, istruzioni,lab):
    num_gruppi_frasi = 0
    # first verify the existence of required fields
    verify_field_existence(istruzioni["necessary_input_fields"]["all"].values(), risp.keys())
    if risp[lab["question_type"]] == "dd":
        verify_field_existence(istruzioni["necessary_input_fields"]["dd"].values(), risp.keys())
    elif risp[lab["question_type"]] == "cloze":
        verify_field_existence(istruzioni["necessary_input_fields"]["cloze"].values(), risp.keys())
    elif risp[lab["question_type"]] == "mcq":
        verify_field_existence(istruzioni["necessary_input_fields"]["mcq"].values(), risp.keys())
    num_aff = int(risp[lab["number_of_statements"]])
    # verify that risp[lab["statements"]] is a dictionary and that it has all keys in the range 1-num_max
    if not isinstance(risp[lab["statements"]],dict):
        error_message(f"il campo 'sentences' deve essere un dizionario")
    num_gruppi_frasi = len(risp[lab["statements"]].keys())
    chiavi_continue = {str(i) for i in range(1, len(risp[lab["statements"]].keys())+1)}
    if risp[lab["statements"]].keys() != chiavi_continue:
            print(risp[lab["statements"]].keys(),chiavi_continue)
            error_message(
                f"I gruppi di risposte devono essere numerati da 1 a {len(risp[lab["statements"]].keys())}, mancano {chiavi_continue-risp[lab["statements"]].keys()}")
    # each statement can be a dictionary or it can be simple: it will be converted here to dictionary
    risp[lab["statements"]] = convert_to_dictionary(risp, lab)
    # print (f"risp['statements'] {risp[lab["statements"]]}")
    # verify that the rich_statements have both requires fields
    for chiave, elenco in risp[lab["statements"]].items():
        for domanda in elenco:
            if not (lab["statement"] in domanda.keys()) or not (lab["correct"] in domanda.keys()):
                error_message(f"In una delle domande del gruppo {chiave} manca un campo")

    # verify that each 'correct' field point to a specified 'answer'
    for chiave, elenco in risp[lab["statements"]].items():
        for domanda in elenco:
            if risp[lab["question_type"]] != "mcq" and domanda[lab["correct"]] not in risp[lab["answers"]].keys():
                error_message(f"La risposta corretta indicata per la domanda \n\t {domanda[lab["statement"]]} \n({domanda[lab["correct"]]}) \nnon è tra le scelte possibili elencate in 'answers'")
            if risp[lab["question_type"]] == "dd" and not risp[lab["answers_placeholder"]] in domanda[lab["statement"]]:
                error_message(
                    f"Nella domanda \n\t {domanda[lab["statement"]]} \nnon è previsto alcun 'buco' da riempire "+
                    f"o non è usata la stringa {risp[lab["answers_placeholder"]]} dichiarata come place holder")

    # verify that choices (if existing) make sense
    if (lab["choices"] in risp.keys() and (len(risp[lab["choices"]]))>0):
        # num_gruppi_frasi = len(risp[lab["statements"]].keys())
        for lista in risp[lab["choices"]]:
            if (len(lista) > num_gruppi_frasi):
                error_message(f"La lista {lista} in 'varianti_scelte' non ha la lunghezza giusta: deve avere al massimo {num_gruppi_frasi} elementi, quanto il numero di gruppi di frasi")
            elif (len(lista) < num_gruppi_frasi):
                warning_message(f"La lista {lista} in 'varianti_scelte' è piú corta del numero dei gruppi di frasi {num_gruppi_frasi}. Per i rimanenti gruppi verrà considerato 0. ")
            somma = sum(lista)
            if somma != num_aff:
                error_message(f"Le varianti nella lista {lista} non hanno somma pari al 'numero_affermazioni' {num_aff} ma hanno somma {somma}" )
            for choice in risp[lab["choices"]]:
                for i in range(len(choice)):
                    if choice[i] > len(risp[lab["statements"]][str(i+1)]):
                        error_message(f"Non ci sono abbastanza frasi per l'{i+1}-esima scelta {choice[i]} in {choice}")
        # verifies that that the first statement (which serves as question) is always chosen exactly once (choice = 1) and that the answer fractions sum to 100
        if(risp[lab["question_type"]] == "mcq"):
            verify_mcq_choices(risp,lab)
    # the following checks an advanced feature (to be completed)
    elif (lab["computed_choices"] in risp.keys() and len(risp[lab["computed_choices"]])>0):
        sum_of_computed_choices = 0
        for constraint in risp[lab["computed_choices"]]:
            if (lab["range"] not in constraint.keys()) or (lab["choices"] not in constraint.keys()):
                error_message(f"Il campo {constraint} in 'computed_choices' non ha almeno uno dei campi 'range' e 'choices' richiesti")
            elif (len(constraint[lab["range"]]) == 0):
                num_gruppi = len(risp[lab["statements"]])
                warning_message(f"Avviso: verrà usato il range 1-{num_gruppi} per il vincolo {constraint} in 'computed_choices'")
            if (lab["choices"] in constraint.keys()):
                try:
                    int(constraint[lab["choices"]])
                except:
                    error_message(f"Il campo 'choices' in {constraint} di  'computed_choices' deve essere un intero")
            sum_of_computed_choices = sum_of_computed_choices + int(constraint[lab["choices"]])
        if (sum_of_computed_choices != num_aff):
            error_message(f"le scelte in 'computed_choices' sono in totale {sum_of_computed_choices} ma il numero richiesto in 'number_of_statements è {num_aff}")
    # check that the cloze type is among those managed
    if risp[lab["question_type"]] == "cloze" and not risp[lab["cloze_type"]] in istruzioni["cloze_types"]["one"]:
                error_message('non so gestire il tipo_cloze specificato')
    # for dd questions check that for each possible answer it is specificed whether it must be infinite
    if risp[lab["question_type"]] == "dd":
        if not lab["if_infinite"] in risp.keys() or (lab["if_infinite"] in risp.keys()) and (risp[lab["if_infinite"]].keys() != risp[lab["answers"]].keys()):
            warning_message(f"Questo messaggio compare perché per alcune o tutte le scelte drag&drop non è specificato se sono infinite e/o è specificato anche per scelte non esistenti."+
                        f"\nVerranno trattate come finite le scelte per cui  non è specificato nulla; verrà ignorata la specifica per scelte non esistenti.")
    # verifify options
    if lab["options"] in risp.keys():
        for option in risp[lab["options"]]:
            if not option in istruzioni["meaningful_options"][risp[lab["question_type"]]].values():
                warning_message(f"L'opzione {option} non ha senso per questo tipo di domanda, verrà ignorata.")

def controlla_json_friendly(percorso_file):
    try:
        with open(percorso_file, 'r', encoding='utf-8') as f:
            contenuto = f.read()

        dati = json.loads(contenuto)
        print(f"✅ Il file {percorso_file} è sintatticamente corretto")
        return dati

    except FileNotFoundError:
        print(f"❌ Errore: Il file '{percorso_file}' non esiste.")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print("❌ Errore di sintassi nel JSON rilevato!\n")
        print(f"📌 Dettagli dell'errore:")

        # Se l'errore è "Expecting ',' delimiter" ma siamo a fine riga/fine file,
        # significa quasi sempre che manca un '}' o un ']' di chiusura.
        messaggio_chiaro = e.msg
        if "Expecting ',' delimiter" in e.msg:
            messaggio_chiaro += " ⚠️ (Nota: Spesso questo errore indica che manca una '}' o ']' di chiusura alla fine dell'oggetto o dell'ultimo elemento!)"

        print(f"   - Messaggio: {messaggio_chiaro}")
        print(f"   - Riga:      {e.lineno}")
        print(f"   - Colonna:   {e.colno}")
        print("-" * 50)

        righe = contenuto.splitlines()
        riga_errore_idx = e.lineno - 1

        print("🔍 Anteprima del codice:")

        if riga_errore_idx > 0:
            print(f"  {e.lineno - 1:4d} | {righe[riga_errore_idx - 1]}")

        if riga_errore_idx < len(righe):
            riga_corrente = righe[riga_errore_idx]
            print(f"👉 {e.lineno:4d} | {riga_corrente}")
            spazi = " " * max(0, e.colno - 1)
            print(f"         {spazi}^--- Errore qui o elemento non chiuso precedentemente")

        if riga_errore_idx < len(righe) - 1:
            print(f"  {e.lineno + 1:4d} | {righe[riga_errore_idx + 1]}")

        print("-" * 50)
        sys.exit(1)


def formatta_json(nome_file):
    try:
        # 1. Legge e decodifica il file JSON
        with open(nome_file, "r", encoding="utf-8") as f:
            dati = json.load(f)

        # 2. Riscrive il file formattato pulito
        with open(nome_file, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=4, ensure_ascii=False)

        print(f"✅ File '{nome_file}' formattato con successo!")

    except FileNotFoundError:
        print(f"❌ Errore: Il file '{nome_file}' non esiste.")
    except json.JSONDecodeError as e:
        print(f"❌ Errore: Il file '{nome_file}' non è un JSON valido.")
        print(f"   Dettaglio errore (riga {e.lineno}, colonna {e.colno}): {e.msg}")
    except Exception as e:
        print(f"❌ Si è verificato un errore imprevisto: {e}")

def main (nomefile):
    formatta_json(nomefile)
    print("sono qui, il file è", nomefile)
    controlla_json_friendly(nomefile)
    return(0)

if __name__ == "__main__":
    # sys.argv contiene gli argomenti passati da riga di comando.
    # sys.exit() per restituire un codice di stato al sistema operativo.
    # Leggi gli argomenti fuori dal main e gestisci eventuali valori mancanti
    if len(sys.argv) > 1:
        nome_input = sys.argv[1]
        main(nome_input)
    else:
        print("Nessun file da controllare")
        print("Uso: python verify.py <nome>")
#         sys.exit(main(sys.argv[1:]))