import tkinter as tk
from tkinter import ttk
import subprocess
import threading

# ======= GLOBALNE ZMIENNE ======= #
current_process = None
selected_station = None
selected_client = None

# ======= FUNKCJE OGÓLNE ======= #
def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        output_text.insert(tk.END, "\n[!] Command stopped by user.\n")

def run_command(command):
    """
    Uruchamia dowolne polecenie (np. 'iwconfig') i wyświetla wynik w output_text.
    """
    global current_process
    try:
        stop_command()  # Najpierw zatrzymujemy ewentualny stary proces
        output_text.delete("1.0", tk.END)
        current_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        def read_output():
            for line in iter(current_process.stdout.readline, ''):
                output_text.insert(tk.END, line)
                output_text.see(tk.END)
            current_process.stdout.close()

        threading.Thread(target=read_output, daemon=True).start()
    except Exception as e:
        output_text.insert(tk.END, f"Error: {e}\n")

# ======= PRZYCISKI (Twoje komendy) ======= #
def run_airmon():
    run_command(['airmon-ng', 'start', 'wlan1'])

def run_iwconfig():
    run_command(['iwconfig'])

def run_systemctl_start_networkmanager():
    run_command(['systemctl', 'start', 'NetworkManager'])

def run_systemctl_stop_networkmanager():
    run_command(['systemctl', 'stop', 'NetworkManager'])

def run_systemctl_restart_networkmanager():
    run_command(['systemctl', 'restart', 'NetworkManager'])

def run_airmon_check_kill():
    run_command(['airmon-ng', 'check', 'kill'])

def run_reaver():
    """
    Przykład użycia wybranego BSSID stacji (selected_station).
    """
    global selected_station
    if not selected_station:
        output_text.insert(tk.END, "No station selected.\n")
        return
    run_command(['reaver', '-i', 'wlan1', '-b', selected_station, '-S', '-v'])

# ======= AIRODUMP PARSOWANIE (Stanowe) ======= #
def run_airodump():
    """
    Uruchamiamy airodump-ng w wątku i parsujemy wynik w dwóch sekcjach:
    - Access Points (AP)
    - Stations (klienci)
    """
    threading.Thread(target=parse_airodump_output, daemon=True).start()

def parse_airodump_output():
    # Czyścimy tabele
    for row in stations_tree.get_children():
        stations_tree.delete(row)
    for row in clients_tree.get_children():
        clients_tree.delete(row)

    stop_command()  # Zatrzymujemy poprzedni proces
    process = subprocess.Popen(
        ['airodump-ng', 'wlan1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    parse_mode = None  # 'AP' lub 'STA'
    # W pętli czytamy linie z airodump-ng
    for line in iter(process.stdout.readline, ''):
        line_str = line.strip()

        # Sprawdzamy, czy to pusta linia => koniec sekcji
        if not line_str:
            parse_mode = None
            continue

        # Czy to nagłówek AP?
        # Nagłówek airodump: "BSSID              PWR  Beacons    #Data, #/s  CH   MB   ENC  CIPHER  AUTH ESSID"
        if line_str.startswith("BSSID "):
            parse_mode = "AP"
            continue

        # Czy to nagłówek STATION?
        # Nagłówek airodump: "STATION            PWR   Rate    Lost    Frames  Notes  Probes"
        if line_str.startswith("STATION "):
            parse_mode = "STA"
            continue

        # Jeśli nie jesteśmy w trybie AP lub STA, pomijamy linie
        if parse_mode is None:
            continue

        if parse_mode == "AP":
            parse_ap_line(line_str)
        elif parse_mode == "STA":
            parse_sta_line(line_str)

def parse_ap_line(line_str):
    """
    Przykładowe parsowanie linii AP.
    Format: BSSID  PWR  Beacons  #Data  #/s  CH  MB  ENC  CIPHER  AUTH  ESSID
    Możemy mieć 10-11+ kolumn (ESSID może mieć spacje).
    """
    # Rozdzielamy maksymalnie do 10 kolumn, reszta to ESSID
    parts = line_str.split(None, 10)
    # Sprawdzamy, czy mamy co najmniej 10 kolumn
    if len(parts) < 10:
        return

    bssid    = parts[0]
    pwr      = parts[1]
    beacons  = parts[2]
    data_    = parts[3]
    per_s    = parts[4]  # #/s
    ch       = parts[5]
    mb       = parts[6]
    enc      = parts[7]
    cipher   = parts[8]
    auth_    = parts[9]
    essid    = parts[10] if len(parts) > 10 else ""

    insert_station(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid)

def parse_sta_line(line_str):
    """
    Przykładowe parsowanie linii STATION.
    Format: STATION  PWR  Rate  Lost  Frames  Notes  Probes
    Może być więcej kolumn, bo Probes może mieć spacje.
    """
    parts = line_str.split(None, 6)
    if len(parts) < 6:
        return

    station_mac = parts[0]
    pwr         = parts[1]
    rate        = parts[2]
    lost        = parts[3]
    frames      = parts[4]
    notes       = parts[5]
    probes      = parts[6] if len(parts) > 6 else ""

    insert_client(station_mac, pwr, rate, lost, frames, notes, probes)

# ======= Wstawianie do Tabel (Treeview) ======= #
def insert_station(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid):
    """
    Dodajemy wiersz do tabeli Stations.
    Ostatnia kolumna to 'Select' – wstawiamy tam checkbox.
    """
    row_id = stations_tree.insert(
        "",
        tk.END,
        values=(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid, "")
    )
    create_checkbox_for_tree(stations_tree, row_id, 11, bssid, is_station=True)

def insert_client(station_mac, pwr, rate, lost, frames, notes, probes):
    """
    Dodajemy wiersz do tabeli Clients.
    Ostatnia kolumna to 'Select'.
    """
    row_id = clients_tree.insert(
        "",
        tk.END,
        values=(station_mac, pwr, rate, lost, frames, notes, probes, "")
    )
    create_checkbox_for_tree(clients_tree, row_id, 7, station_mac, is_station=False)

def create_checkbox_for_tree(tree, item_id, col_index, mac, is_station=True):
    """
    Tworzy Checkbutton w danej komórce. 
    To jest sztuczka – standardowy Treeview nie ma wbudowanych checkboxów.
    """
    bbox = tree.bbox(item_id, col_index)
    if not bbox:
        # Może być puste przy tworzeniu wiersza, więc opóźniamy
        tree.after(100, lambda: create_checkbox_for_tree(tree, item_id, col_index, mac, is_station))
        return

    x, y, width, height = bbox
    var = tk.BooleanVar()

    def on_check():
        if var.get():
            if is_station:
                print(f"[Selected Station] {mac}")
                global selected_station
                selected_station = mac
            else:
                print(f"[Selected Client] {mac}")
                global selected_client
                selected_client = mac

    cb = tk.Checkbutton(tree, variable=var, command=on_check)
    tree.create_window(x, y, anchor="nw", window=cb)

# ======= BUDOWA INTERFEJSU ======= #
app = tk.Tk()
app.title("Airmon-NG GUI")

# Konfiguracja kolumn
app.grid_columnconfigure(0, weight=1, uniform="column")
app.grid_columnconfigure(1, weight=1, uniform="column")

# GÓRNA CZĘŚĆ: Dwie Tabele
top_frame = tk.Frame(app)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

# Stations
stations_label = tk.Label(top_frame, text="Stations", font=('Helvetica', 14, 'bold'))
stations_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

stations_cols = ("BSSID", "PWR", "Beacons", "#Data", "#/s", "CH", "MB", "ENC", "CIPHER", "AUTH", "ESSID", "Select")
stations_tree = ttk.Treeview(top_frame, columns=stations_cols, show="headings", height=10)
for col in stations_cols:
    stations_tree.heading(col, text=col)
    stations_tree.column(col, width=80)
stations_tree.grid(row=1, column=0, padx=5, pady=5)

stations_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=stations_tree.yview)
stations_tree.configure(yscrollcommand=stations_scroll.set)
stations_scroll.grid(row=1, column=1, sticky="ns")

# Clients
clients_label = tk.Label(top_frame, text="Clients", font=('Helvetica', 14, 'bold'))
clients_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

clients_cols = ("STATION", "PWR", "Rate", "Lost", "Frames", "Notes", "Probes", "Select")
clients_tree = ttk.Treeview(top_frame, columns=clients_cols, show="headings", height=10)
for col in clients_cols:
    clients_tree.heading(col, text=col)
    clients_tree.column(col, width=80)
clients_tree.grid(row=1, column=2, padx=5, pady=5)

clients_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=clients_tree.yview)
clients_tree.configure(yscrollcommand=clients_scroll.set)
clients_scroll.grid(row=1, column=3, sticky="ns")

# ŚRODKOWA CZĘŚĆ: Okno tekstowe
output_text = tk.Text(app, height=10, width=80, font=('Courier', 12))
output_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# DOLNA CZĘŚĆ: Przyciski
button_frame = tk.Frame(app)
button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

def create_button(parent, text, command, row, column):
    button = tk.Button(
        parent, text=text, command=command, 
        width=20, height=2, font=('Helvetica', 20)
    )
    button.grid(row=row, column=column, padx=5, pady=5)

create_button(button_frame, 'Start Airmon', run_airmon, 0, 0)
create_button(button_frame, 'Show IWConfig', run_iwconfig, 0, 1)
create_button(button_frame, 'Start NetworkManager', run_systemctl_start_networkmanager, 1, 0)
create_button(button_frame, 'Stop NetworkManager', run_systemctl_stop_networkmanager, 1, 1)
create_button(button_frame, 'Restart NetworkManager', run_systemctl_restart_networkmanager, 2, 0)
create_button(button_frame, 'Airmon Check Kill', run_airmon_check_kill, 2, 1)
create_button(button_frame, 'Start Airodump', run_airodump, 3, 0)
create_button(button_frame, 'Wash', lambda: output_text.insert(tk.END, "Wash not implemented.\n"), 3, 1)
create_button(button_frame, 'Reaver', run_reaver, 4, 0)
create_button(button_frame, 'Stop Command', stop_command, 4, 1)

app.mainloop()
