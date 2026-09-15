#
# Copyright 2026 Lavinia Egidi
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import json
import argparse
from pathlib import Path
from verify import controlla_json_friendly, verifica, error_message, warning_message
from gen_tools import *
import sys
import os

FILE_CONFIG = "config.json"
# defines inputs and options
def parse_args():
    parser = argparse.ArgumentParser(
        prog='genera_quiz',
        description='genera quiz moodle in formato XML da file JSON in input')

    parser.add_argument("-i", "--input", help="file in input", type=str)
    parser.add_argument("-d", "--directory", help="elaborare tutti i file nella directory in input (se non viene specificata la directory, viene usata quella di default)",
                        type=str, nargs='?', const = '-')
    parser.add_argument("-c", "--concat", help="concatena i file specificati nel file config", action='store_true')
    return parser.parse_args(), parser

def forallfiles(input_directory,complete_quiz):
    allfiles = []
    for filename in os.listdir(input_directory):
        if filename.endswith(".json") and not filename.startswith(complete_quiz):
            allfiles.append(os.path.join(input_directory,filename))
    return allfiles

def verify_template_existence(names):
    for temp_name in names.values():
        if not os.path.exists(temp_name):
            error_message(f"Errore! Non esiste il template {temp_name}. Devono esistere i template necessari.")

def concatena(cfg,da_concatenare,nomifile):
    print(f"➡️ Concatenazione dei quiz:")

    with open( nomifile["template_quiz"], 'r') as shellfile:
        shell_lines = shellfile.readlines()

    quiz_completo = shell_lines[:2]

    for nome in da_concatenare:
        barename = Path(nome).stem
        input_path = Path(nome).parent
        nomefilequiz = barename + ".xml"
        # if nomifile["outfile_prefix"] and nomifile["outfile_prefix"] in barename:
        #     barename = barename.split(nomifile["outfile_prefix"])[1] # questo non serve piú, credo
        # elif nomifile["outfile_prefix"] and len(Path(nome).parts) == 1 and not nomifile[
        #                                                                               "outfile_prefix"] in barename:
        #     nomefilequiz = nomifile["outfile_prefix"] + nomefilequiz
        if nomifile["outfile_prefix"] and len(Path(nome).parts) == 1 and not nomifile[
                                                                                      "outfile_prefix"] in barename:
            nomefilequiz = nomifile["outfile_prefix"] + nomefilequiz

        if len(Path(nome).parts) == 1:
            input_path = nomifile["out_dir"]

        nomefilequiz = os.path.join(input_path, nomefilequiz)
        if not os.path.exists(nomefilequiz):
            warning_message(f"Attenzione! Non esiste il file {nomefilequiz}; procedo con gli altri")
        else:
            print(f"\t{nomefilequiz}")

            # Apri il file originale in lettura e quello nuovo in scrittura
            with open(nomefilequiz, "r", encoding="utf-8") as quiz:
                righe = quiz.readlines()

            # Seleziona dalla terza riga (indice 2) fino alla penultima (indice -1 escluso)
            contenuto_quiz = righe[2:-1]

            quiz_completo = quiz_completo + ["\n"] + contenuto_quiz

    quiz_completo = quiz_completo + shell_lines[-1:]
    concat_file = os.path.join(nomifile["out_dir"], nomifile["concat_quiz"]+".xml")
    with open(concat_file, "w", encoding="utf-8") as file_quiz_completo:
        file_quiz_completo.writelines(quiz_completo)

    print(f"\n➡️ Output salvato in {concat_file}")
    sys.exit(0)

def main():
    file_config = FILE_CONFIG
    if not os.path.exists(file_config):
        error_message(f"Errore! Non esiste il file {file_config}")

    cfg = controlla_json_friendly(file_config)
    with open(file_config, 'r') as file_db:
        cfg = json.load(file_db)

    nomifile = cfg["filenames"]
    template_files = {}
    for key, file_name in cfg["templates"].items():
        if key != "template_dir":
            template_files[key] = os.path.join(cfg["templates"]["template_dir"],cfg["templates"][key]+".xml")
    nomifile.update(template_files)

    if len(sys.argv) > 1 and parse_args()[0].concat:
        warning_message("È stata richiesta la concatenazione di file\n")
        if cfg["exec"] and not "ALL" in cfg["exec"]:
            concatena(cfg,cfg["exec"], nomifile)
        elif cfg["exec"] and "ALL" in cfg["exec"]:
            concatena(cfg,cfg["database"], nomifile)
        else:
            error_message(f"Nel file di configurazione {file_config} non sono specificati file da concatenare")

    verify_template_existence(template_files)

    lab = {}
    for key in cfg["necessary_input_fields"]:
        lab.update(cfg["necessary_input_fields"][key])
    for key in cfg["meaningful_options"]:
        lab.update(cfg["meaningful_options"][key])

    daeseguire = []
    input_directory = ""
    all = False

    if len(sys.argv) > 1:
        print("Sono state specificate opzioni")
        args, parser = parse_args()
        if not args.input is None:
            daeseguire = [args.input]
        elif not args.directory is None:
            all = True
            if not args.directory == '-':
                input_directory = args.directory
        else:
            print("Sulla linea di comando nessuna indicazione sui file da elaborare")
    elif not cfg["exec"]:
        print("Nel file di configurazione nessuna indicazione sui file da elaborare")
        daeseguire.append(input("Inserisci il nome del file: "))
    elif "ALL" in cfg["exec"]:
        daeseguire = cfg['database']
    else:
        daeseguire = cfg['exec']

    if all:
        if not input_directory:
            input_directory = nomifile["source_dir"]
        daeseguire = forallfiles(input_directory,nomifile["concat_quiz"])

    for nome in daeseguire:
        print("nome:",nome)
        barename = Path(nome).stem
        input_path = Path(nome).parent
        nomefilerisposte = barename + ".json"
        if nomifile["sourcefile_prefix"] and nomifile["sourcefile_prefix"] in barename:
            barename = barename.split(nomifile["sourcefile_prefix"])[1]
        elif nomifile["sourcefile_prefix"] and len(Path(nome).parts) == 1 and not nomifile["sourcefile_prefix"] in barename:
            nomefilerisposte = nomifile["sourcefile_prefix"] + nomefilerisposte
        if len(Path(nome).parts) == 1:
            input_path = nomifile["source_dir"]

        nomefilerisposte = os.path.join(input_path,nomefilerisposte)
        print(f"\n\n➡️ Elaborazione di {nomefilerisposte}")
        if not os.path.exists(nomefilerisposte):
            error_message(f"Errore! Non esiste il file {nomefilerisposte}")

        risposte = controlla_json_friendly(nomefilerisposte)

        verifica(risposte, cfg, lab)
        print("✅ Il file", nomefilerisposte, "contiene i campi previsti e, per quanto verificato, è logicamente corretto")

        # each statement can be a dictionary or it can be simple: it will be converted here to dictionary
        risposte[lab["statements"]] = convert_to_dictionary(risposte, lab)

        template = genera_template(risposte, nomifile, lab)

        # in risposte[COMPLETE_STATEMENTS] the statements are in the correct moodle format, so the generation of combinations is no longer mixed with the preparation of the moodle syntax
        risposte[COMPLETE_STATEMENTS] = {}
        complete_answers(risposte, nomifile,lab)
        # for group in risposte[COMPLETE_STATEMENTS]:
        #     print(f"il gruppo {group} contiene {len(risposte[COMPLETE_STATEMENTS][group])} frasi")

        questions, numero_totale = prepare_questions(risposte, template,lab)
        print("numero totale domande generate", numero_totale)
        with open(nomifile["template_quiz"], 'r') as shellfile:
            shell = shellfile.read()
        template = shell.replace("__PHSINGOLEDOMANDE", questions).replace("__PHCATEGORY", risposte[lab["category"]])

        if not os.path.exists(nomifile["out_dir"]):
            print(f"Creo la cartella {nomifile['out_dir']}")
            os.makedirs(nomifile["out_dir"])

        nomefilequiz = os.path.join(nomifile["out_dir"],nomifile["outfile_prefix"] + barename + ".xml")
        print(f"Il quiz è nel file {nomefilequiz}")
        with open(nomefilequiz, 'w', encoding='utf-8') as file:
            file.write(template)

    return 0

if __name__ == "__main__":
    # sys.argv contiene gli argomenti passati da riga di comando.
    # sys.exit() per restituire un codice di stato al sistema operativo.
    sys.exit(main())
#         sys.exit(main(sys.argv[1:]))


