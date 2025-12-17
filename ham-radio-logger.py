"""
Ham Radio Logger

This file defines the main menu loop and stub functions
for the different actions. The actual logic (file I/O,
QSO prompts, stats, etc.) need to be implemented in the TODOs.
"""

import json  # will be useful later
import os  # will be useful later
from collections import Counter

# For now, keep the log file simple and in the same folder
LOG_FILE = "qsolog.jsonl"
MY_CALL = "AG5XY"


def ensure_log_file_exists() -> None:
    """
    Make sure the log file exists so reading it later
    doesn't crash with FileNotFoundError.
    """
    if not os.path.exists(LOG_FILE):
        # Create an empty file
        open(LOG_FILE, "a", encoding="utf-8").close()


def load_all_qsos(filename: str) -> list[dict]:

    qso_list = []

    # First see if file exists, and if not return an empty list

    if not os.path.exists(filename):
        return qso_list

    # Now, get the lines, strip them, and add them to list if not blank.

    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line == "":
                continue
            qso_list.append(json.loads(line))
    return qso_list


def show_main_menu() -> None:
    """
    Print the main menu and return the user's choice as a string.
    """
    print()
    print("Ham Radio Logger - Main Menu")
    print("1) Log a new QSO")
    print("2) List recent QSOs")
    print("3) Search QSOs")
    print("4) Show stats")
    print("5) Exit")
    choice = input("Enter your choice: ").strip()
    return choice


def print_qso(qso: dict) -> None:
    """
    - Loop through dict and print. First implementation is a naive one on each line.
    """

    for key, value in qso.items():
        label = key
        label = label.replace("_", " ").title()
        print(f"{label}: {value}")


def handle_log_new_qso() -> None:
    """
    - Prompt the user for QSO fields (their_call, band, etc.)
    - Build a dict with the QSO data
    - Append it as a JSON line to LOG_FILE if the user wants, if not, if they want to change it, let them.
    If they dont' want to write at all, return to main menu
    """

    qso = {}
    print("Enter their call sign:")
    their_call = input().strip().upper()
    qso["call_sign"] = their_call
    print("Enter signal report they gave you:")
    their_report = input().strip()
    qso["their_signal_report"] = their_report
    print("Enter signal report you gave them")
    my_report = input().strip()
    qso["my_signal_report"] = my_report
    print("Enter QSO band: (put mode information in mode field)")
    band = input().strip()
    qso["band"] = band
    print("Enter any other comments you want to about this QSO (Enter for none):")
    comments = input().strip()
    qso["comments"] = comments
    print()
    print("Thank you. Here is what you entered. ")
    print_qso(qso)
    print("Save to log file Y/N?")
    write_to_log = input().strip()
    if write_to_log.upper() == "Y":
        with open(LOG_FILE, "a", encoding="utf-8") as file:
            file.write(json.dumps(qso) + "\n")
        print("QSO saved. Returning to main menu")
    else:
        print("QSO not saved. Returning to main menu")


def handle_list_recent_qsos() -> None:
    """
    Fundtion to  print last n QSOs
    """
    print()
    print("How many QSOs do you want to see (default is 10)")
    qso_input = input().strip()
    if qso_input == "":
        num_qsos = 10
    else:
        try:
            num_qsos = int(qso_input)
            if num_qsos <= 0:
                print("Can't use numbers < 1. Using default instead")
                num_qsos = 10
        except ValueError:
            print("Invalid input. Using default.")
            num_qsos = 10

    # Now that we know the requested number of QSOs, get the set of them and print them.

    print("Attemptint to print the last " + str(num_qsos) + " QSOs")
    print()

    qso_list = load_all_qsos(LOG_FILE)
    if qso_list:

        # OK, we have some to print, do a slice on the list and print them:

        if num_qsos > len(qso_list):
            print("Sorry, there are not " + str(num_qsos) + " in the file")
            num_qsos = len(qso_list)
            print("Printing last " + str(num_qsos) + " instead:")

        recent_qsos = qso_list[-num_qsos:]
        for qso in recent_qsos:
            print_qso(qso)
    else:
        print("Sorry, no QSOs to print")
    return None


def handle_search_qsos() -> None:
    """
    Functionfor searching QSOs.

    - Search call sign for now
    - Let user know if not found.
    - If found, print number found, and then all instances..
    """
    print()
    search_list = load_all_qsos(LOG_FILE)
    if not search_list:
        print("No QSOs to search. Returning to main menu.")
        return None

    print("Enter call sign to search:")
    search_call = input().strip().upper()

    # Loop through list and count the QSOs by accessing each dictionary

    qso_counter = 0
    for qso in search_list:
        if qso.get("call_sign") == search_call:
            print_qso(qso)
            qso_counter += 1
    if qso_counter > 0:
        print("Found " + str(qso_counter) + " instances.")
    else:
        print("Call sign " + search_call + " not found.")
    return None


def handle_search_qsos() -> None:
    """
    Functionfor searching QSOs.

    - Search call sign for now
    - Let user know if not found.
    - If found, print number found, and then all instances..
    """
    print()
    search_list = load_all_qsos(LOG_FILE)
    if not search_list:
        print("No QSOs to search. Returning to main menu.")
        return None

    print("Enter call sign to search:")
    search_call = input().strip().upper()

    # Loop through list and count the QSOs by accessing each dictionary

    qso_counter = 0
    for qso in search_list:
        if qso.get("call_sign") == search_call:
            print_qso(qso)
            qso_counter += 1
    if qso_counter > 0:
        print("Found " + str(qso_counter) + " instances.")
    else:
        print("Call sign " + search_call + " not found.")
    return None


def count_qso_field(qso_list: list[dict], field_name: str) -> Counter:
    """
    Count occurrences of a given field across all QSOs.

    - Iterates through the QSO list
    - Extracts the specified field from each QSO
    - Normalizes values (strip + uppercase)
    - Returns a Counter of field values
    """

    counter = Counter()
    for qso in qso_list:
        clean_key = qso.get(field_name)
        if clean_key == None:
            continue
        clean_key = clean_key.strip().upper()
        counter[clean_key] += 1
    return counter


def handle_show_stats() -> None:
    """
    - Load all QSOs from LOG_FILE
    - Use collections.Counter to summarize:
        - Total QSOs
        - At least top 10 QSOs by call sign
        - At least top 5 QSOS by band
    - Print the results in a simple text format
    """

    print()
    print("Here is a summary of your log's statistics:")
    qso_list = load_all_qsos(LOG_FILE)
    if qso_list == []:
        print("no QSOs to run statistics on, returning to main menu.")
        return None

    total_qsos = len(qso_list)
    print("Total number of QSOs is " + str(total_qsos))
    print()
    print("Here are the most common call signs in your log:")
    call_counter = count_qso_field(qso_list, "call_sign")
    call_list = call_counter.most_common(10)
    for call, value in call_list:
        print(str(call) + " : " + str(value))
    print("Here are the most common bands in your log:")
    band_counter = count_qso_field(qso_list, "band")
    band_list = band_counter.most_common(5)
    for band, value in band_list:
        print(str(band) + " : " + str(value))
    return None


def main():
    """
    Main entry point for the ham radio logger.
    Sets things up and runs the menu loop.
    """
    print("Welcome to the Ham Radio Logger by " + MY_CALL + "!")
    ensure_log_file_exists()

    # Main loop
    while True:
        choice = show_main_menu()

        if choice == "1":
            handle_log_new_qso()
        elif choice == "2":
            handle_list_recent_qsos()
        elif choice == "3":
            handle_search_qsos()
        elif choice == "4":
            handle_show_stats()
        elif choice == "5":
            print("Goodbye and 73!")
            break
        else:
            print()
            print("Invalid choice, please try again.")


if __name__ == "__main__":
    main()
