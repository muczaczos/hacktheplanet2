import tkinter as tk
from tkinter import ttk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_station = None  # Tutaj możemy przechowywać wybrane stacje
selected_client = None   # Tutaj możemy przechowywać wybranych klientów

# ====== Funkcje ogólne ====== #
def run_command(command):
    """
    Uruchamia dowolne polecenie w subprocess.
    Nie wyświetla już wyniku w Text, ale można to rozszerzyć.
    """
    global current_process
    try:
        current_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    except Exception as e:
        print(f"Error: {e}")
    finally:
        current_process = None

def stop_command():
    """
    Zatrzymuje aktualnie uruchomiony proces (np. airodump-ng).
    """
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None

# ====== Funkcje do przycisków z Twojego kodu ====== #
def run_airmon():
    threading.Thread(
        target=run_command,
        args=(['airmon-ng', 'start', 'wlan1'],),
        daemon=True
    ).start()

def run_iwconfig():
    threading.Thread(
        target=run_command,
        args=(['iwconfig'],),
        daemon=True
    ).start()

def run_systemctl_start_networkmanager():
    threading.Thread(
        target=run_command,
        args=(['systemctl', 'start', 'NetworkManager'],),
        daemon=True
    ).start()

def run_systemctl_stop_networkmanager():
    threading.Thread(
        target=run_command,
        args=(['systemctl', 'stop', 'NetworkManager'],),
        daemon=True
    ).start()

def run_systemctl_restart_networkmanager():
    threading.Thread(
        target=run_command,
        args=(['systemctl', 'restart', 'NetworkManager'],),
        daemon=True
    ).start()

def run_airmon_check_kill():
    threading.Thread(
        target=run_command,
        args=(['airmon-ng', 'check', 'kill'],),
        daemon=True
    ).start()

def run_reaver():
    """
    Przykładowa funkcja, która mogłaby korzystać z selected_station/selected_client.
    """
    global selected_station
    if not selected_station:
        print("No station selected!")
        return
    threading.Thread(
        target=run_command,
        args=(['reaver', '-i', 'wlan1', '-b', selected_station, '-S', '-v'],),
        daemon=True
    ).start()

# ====== Funkcje do airodump-ng ====== #
def run_airodump():
    """
    Uruchamiamy wątek, który odpala airodump-ng i parsuje dane.
    """
    threading.Thread(target=display_airodump_results, daemon=True).start()

def display_airodump_results():
    """
    Odpala airodump-ng, parsuje wyniki i wyświetla je w dwóch tabelach:
    - Stations
    - Clients
    """
    # Czyścimy istniejące dane w tabelach
    for row in stations_tree.get_children():
        stations_tree.delete(row)
    for row in clients_tree.get_children():
        clients_tree.delete(row)

    process = subprocess.Popen(
        ['airodump-ng', 'wlan1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Parsujemy linie airodump-ng
    for line in process.stdout:
        parts = line.split()
        if not parts or parts[0] in ["BSSID", "Station", ""]:
            continue

        # Przykład: rozróżniamy stację i klienta po liczbie kolumn
        # (to jest uproszczone - dopasuj do realnego formatu airodump-ng)
        if len(parts) >= 8:
            # Prawdopodobnie klient
            # BSSID, Station, PWR, Rate, Lost, Frames, Probe
            # Indeksy do dopracowania w zależności od faktycznego formatu
            bssid      = parts[0]
            station    = parts[1]
            pwr        = parts[2]
            rate       = parts[3]
            lost       = parts[4]
            # Możesz dodać więcej kolumn, np. frames, probe
            insert_client(bssid, station, pwr, rate, lost)
        else:
            # Prawdopodobnie stacja
            # BSSID, PWR, Beacons, #Data, CH, MB, ENC, ...
            bssid    = parts[0]
            pwr      = parts[1]
            beacons  = parts[2] if len(parts) > 2 else ""
            data     = parts[3] if len(parts) > 3 else ""
            ch       = parts[4] if len(parts) > 4 else ""
            mb       = parts[5] if len(parts) > 5 else ""
            insert_station(bssid, pwr, beacons, data, ch, mb)

def insert_station(bssid, pwr, beacons, data, ch, mb):
    """
    Dodaje wiersz do tabeli Stations z checkboxem.
    """
    # Tworzymy unikalny identyfikator wiersza
    row_id = stations_tree.insert("", tk.END, values=(bssid, pwr, beacons, data, ch, mb, ""))
    # Dodajemy checkbox w kolumnie 7
    # Niestety standardowy Treeview nie ma wbudowanych checkboxów,
    # więc często robi się to np. przez ikonki lub osobną kolumnę z Buttonem.
    # Poniżej - przykładowy hack z "opcja #7" jako placeholder:
    create_checkbox_for_tree(stations_tree, row_id, 6, bssid, station=True)

def insert_client(bssid, station, pwr, rate, lost):
    """
    Dodaje wiersz do tabeli Clients z checkboxem.
    """
    row_id = clients_tree.insert("", tk.END, values=(bssid, station, pwr, rate, lost, ""))
    create_checkbox_for_tree(clients_tree, row_id, 5, bssid, station=False)

def create_checkbox_for_tree(tree, item_id, col_index, mac, station=True):
    """
    Tworzymy checkbox 'na wierzchu' Treeview – w praktyce to 'trick'.
    Najprościej jest zbudować Canvas i tam wstawić Checkbutton.
    """
    # Pozycja komórki w Treeview
    bbox = tree.bbox(item_id, col_index)
    if not bbox:
        return
    x, y, width, height = bbox
    # Tworzymy wirtualny widget w obszarze Treeview
    var = tk.BooleanVar()
    def on_check():
        if var.get():
            # Zaznaczony
            if station:
                print(f"[Station selected] BSSID: {mac}")
                # Tutaj zapisz do global selected_station
                global selected_station
                selected_station = mac
            else:
                print(f"[Client selected] MAC: {mac}")
                global selected_client
                selected_client = mac

    cb = tk.Checkbutton(tree, variable=var, command=on_check)
    cb_window = tree.create_window(x, y, anchor="nw", window=cb)
    # To demo – w praktyce trzeba nasłuchiwać '<<TreeviewScroll>>',
    # żeby przesuwać checkbox razem z wierszem.

# ====== Budowa głównego okna ====== #
app = tk.Tk()
app.title('Airmon-NG GUI')

# 1) Góra ekranu: Dwie tabele (Stations, Clients)
top_frame = tk.Frame(app)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

# Stations
stations_label = tk.Label(top_frame, text="Stations", font=('Helvetica', 16, 'bold'))
stations_label.grid(row=0, column=0, padx=5, pady=5)
stations_cols = ("BSSID", "PWR", "Beacons", "Data", "CH", "MB", "Check")
stations_tree = ttk.Treeview(top_frame, columns=stations_cols, show="headings", height=10)
for col in stations_cols:
    stations_tree.heading(col, text=col)
    stations_tree.column(col, width=80)  # szerokość do dostosowania
stations_tree.grid(row=1, column=0, padx=5, pady=5)

# Dodaj pionowy scrollbar
stations_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=stations_tree.yview)
stations_tree.configure(yscrollcommand=stations_scroll.set)
stations_scroll.grid(row=1, column=1, sticky="ns")

# Clients
clients_label = tk.Label(top_frame, text="Clients", font=('Helvetica', 16, 'bold'))
clients_label.grid(row=0, column=2, padx=5, pady=5)
clients_cols = ("BSSID", "Station", "PWR", "Rate", "Lost", "Check")
clients_tree = ttk.Treeview(top_frame, columns=clients_cols, show="headings", height=10)
for col in clients_cols:
    clients_tree.heading(col, text=col)
    clients_tree.column(col, width=80)
clients_tree.grid(row=1, column=2, padx=5, pady=5)

clients_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=clients_tree.yview)
clients_tree.configure(yscrollcommand=clients_scroll.set)
clients_scroll.grid(row=1, column=3, sticky="ns")

# 2) Dół ekranu: przyciski
#   Zgodnie z Twoim kodem – ten sam układ, tylko w wierszu 2
button_frame = tk.Frame(app)
button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

def create_button(parent, text, command, row, column):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        width=20,
        height=2,
        font=('Helvetica', 20)
    )
    button.grid(row=row, column=column, padx=1, pady=1)

create_button(button_frame, 'Start Airmon', run_airmon, 0, 0)
create_button(button_frame, 'Show IWConfig', run_iwconfig, 0, 1)
create_button(button_frame, 'Start NetworkManager', run_systemctl_start_networkmanager, 1, 0)
create_button(button_frame, 'Stop NetworkManager', run_systemctl_stop_networkmanager, 1, 1)
create_button(button_frame, 'Restart NetworkManager', run_systemctl_restart_networkmanager, 2, 0)
create_button(button_frame, 'Airmon Check Kill', run_airmon_check_kill, 2, 1)
create_button(button_frame, 'Start Airodump', run_airodump, 3, 0)
create_button(button_frame, 'Wash', lambda: print("Wash not implemented."), 3, 1)  # Możesz dodać run_wash
create_button(button_frame, 'Reaver', run_reaver, 4, 0)
create_button(button_frame, 'Stop Command', stop_command, 4, 1)

app.mainloop()
