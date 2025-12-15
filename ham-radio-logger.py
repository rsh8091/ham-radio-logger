"""
Ham Radio Logger

This file defines the main menu loop and stub functions
for the different actions. The actual logic (file I/O,
QSO prompts, stats, etc.) need to be implemented in the TODOs.
"""

import json  # will be useful later
import os  # will be useful later

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
    print("Enter QSO band:")
    band = input().strip()
    qso["band"] = band
    print("Enter any other comments you want to about this QSO:")
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
    Stub for searching QSOs.

    TODO:
    - Show a small submenu:
        1) Search by callsign
        2) Search by band
        3) Search by mode
    - Based on choice, ask for search term
    - Filter QSOs loaded from LOG_FILE
    - Display matches
    """
    print()
    print("[Search QSOs] (not implemented yet)")
    # TODO: implement search logic here


def handle_show_stats() -> None:
    """
    Stub for showing statistics.

    TODO:
    - Load all QSOs from LOG_FILE
    - Use collections.Counter to summarize:
        - QSOs by band
        - QSOs by mode
        - Top N callsigns
    - Print the results in a simple text format
    """
    print()
    print("[Show stats] (not implemented yet)")
    # TODO: implement stats logic here


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
