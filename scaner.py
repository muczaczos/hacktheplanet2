import tkinter as tk
from tkinter import ttk
import subprocess
import threading

# --- GLOBALNE ZMIENNE ---
current_process = None

# Dla stacji: BSSID, PWR, Beacons, Data, CH, MB, [x]
# Dla klientów: BSSID, Station, PWR, Rate, Lost, [x]

# Zaznaczone stacje/klienci (można rozszerzyć o słowniki)
selected_station = None
selected_client = None

# --- FUNKCJE OGÓLNE ---

def run_command(command):
    """
    Uruchamia dowolne polecenie i wyświetla wynik w oknie tekstowym (output_text).
    """
    global current_process
    try:
        # Jeśli jest już proces, najpierw go zatrzymujemy.
        stop_command()

        # Czyścimy okno tekstowe z poprzednich wyników.
        output_text.delete("1.0", tk.END)

        current_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Odczyt w osobnym wątku, by nie blokować GUI
        def read_output():
            for line in iter(current_process.stdout.readline, ''):
                output_text.insert(tk.END, line)
                output_text.see(tk.END)  # Automatyczne przewijanie w dół
            current_process.stdout.close()

        threading.Thread(target=read_output, daemon=True).start()

    except Exception as e:
        output_text.insert(tk.END, f"Error: {e}\n")

def stop_command():
    """
    Zatrzymuje aktualnie uruchomiony proces (np. airodump-ng).
    """
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        output_text.insert(tk.END, "\n[!] Command stopped by user.\n")

# --- FUNKCJE PRZYCISKÓW (Twoje komendy) ---

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
    global selected_station
    if not selected_station:
        output_text.insert(tk.END, "No station selected.\n")
        return
    # Przykład użycia BSSID
    run_command(['reaver', '-i', 'wlan1', '-b', selected_station, '-S', '-v'])

# --- AIRODUMP: PARSOWANIE I WYPEŁNIANIE TABEL ---

def run_airodump():
    """
    Uruchamiamy airodump-ng w wątku, parsujemy i wrzucamy do Tabel (Treeview).
    """
    # Czyścimy istniejące dane w tabelach
    for row in stations_tree.get_children():
        stations_tree.delete(row)
    for row in clients_tree.get_children():
        clients_tree.delete(row)

    # Uruchamiamy airodump-ng w osobnym wątku
    def airodump_thread():
        stop_command()  # Najpierw zatrzymujemy ewentualny stary proces
        process = subprocess.Popen(
            ['airodump-ng', 'wlan1'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        # Odczyt linii i parsowanie
        for line in iter(process.stdout.readline, ''):
            parts = line.split()
            # Prosty filtr: stacje <-> klienci
            if len(parts) < 1:
                continue
            # Pomijamy nagłówki
            if parts[0] in ["BSSID", "Station", "#", ""]:
                continue

            # Przykładowe dopasowanie do stacji (7 kolumn)
            # BSSID, PWR, Beacons, #Data, CH, MB, ENC, ...
            # Indeksy do dopracowania:
            # parts[0] -> BSSID
            # parts[1] -> PWR
            # parts[2] -> Beacons
            # parts[3] -> #Data
            # parts[4] -> CH
            # parts[5] -> MB
            # ...
            if len(parts) >= 6:
                # Uznajmy, że to stacja
                bssid   = parts[0]
                pwr     = parts[1]
                beacons = parts[2]
                data_   = parts[3]
                ch      = parts[4]
                mb      = parts[5]
                insert_station(bssid, pwr, beacons, data_, ch, mb)
            # W innym wierszu airodump pojawiają się klienci
            # BSSID, Station, PWR, Rate, Lost, Frames, Probe ...
            # Indeksy do ustalenia w zależności od formatu
            if len(parts) >= 5:
                # Prosty przykład:
                # BSSID, Station, PWR, Rate, Lost
                # (Może się zdarzyć, że airodump najpierw listuje stacje, a dopiero w drugiej sekcji klientów)
                # Zależnie od formatu, lepiej sprawdzać warunki, np.:
                # if parts[1].count(':') == 5: # stacja vs. client
                pass

    threading.Thread(target=airodump_thread, daemon=True).start()

def insert_station(bssid, pwr, beacons, data_, ch, mb):
    """
    Dodaje wiersz do tabeli Stations z checkboxem.
    """
    # Wstawiamy wiersz
    row_id = stations_tree.insert(
        "",
        tk.END,
        values=(bssid, pwr, beacons, data_, ch, mb, "")
    )
    # Dodajemy checkbox w kolumnie 6 (ostatnia) – to jest trudne w standardowym Treeview
    create_checkbox_for_tree(stations_tree, row_id, 6, bssid, is_station=True)

def create_checkbox_for_tree(tree, item_id, col_index, mac, is_station=True):
    """
    Tworzymy checkbox w danej komórce (kolumna col_index).
    W standardowym Treeview to 'hack': wstawiamy Checkbutton na wierzch.
    """
    # Wyliczamy pozycję komórki
    bbox = tree.bbox(item_id, col_index)
    if not bbox:
        # Czasem bbox jest puste, np. w momencie tworzenia wiersza.
        # Można opóźnić wstawienie checka, np. .after(100, create_checkbox_for_tree, ...)
        tree.after(100, lambda: create_checkbox_for_tree(tree, item_id, col_index, mac, is_station))
        return

    x, y, width, height = bbox

    var = tk.BooleanVar()

    def on_check():
        if var.get():
            if is_station:
                print(f"Selected station: {mac}")
                global selected_station
                selected_station = mac
            else:
                print(f"Selected client: {mac}")
                global selected_client
                selected_client = mac

    cb = tk.Checkbutton(tree, variable=var, command=on_check)
    # Wstawiamy checkbutton w Treeview
    window_id = tree.create_window(x, y, anchor="nw", window=cb)

    # UWAGA: przy przewijaniu w pionie/poziomie checkbox nie będzie się przesuwał.
    # Trzeba obsłużyć zdarzenia typu <<TreeviewScroll>> i ponownie ustawiać pozycję.
    # Jest to zaawansowany temat w czystym Tkinter.

# --- BUDOWA GŁÓWNEGO OKNA ---

app = tk.Tk()
app.title("Airmon-NG GUI")

# 1. Górna część: Tabele (Stations / Clients)

top_frame = tk.Frame(app)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

# --- Stations ---
stations_label = tk.Label(top_frame, text="Stations", font=('Helvetica', 14, 'bold'))
stations_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

stations_cols = ("BSSID", "PWR", "Beacons", "Data", "CH", "MB", "Select")
stations_tree = ttk.Treeview(top_frame, columns=stations_cols, show="headings", height=10)
for col in stations_cols:
    stations_tree.heading(col, text=col)
    stations_tree.column(col, width=80)
stations_tree.grid(row=1, column=0, padx=5, pady=5)

stations_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=stations_tree.yview)
stations_tree.configure(yscrollcommand=stations_scroll.set)
stations_scroll.grid(row=1, column=1, sticky="ns")

# --- Clients ---
clients_label = tk.Label(top_frame, text="Clients", font=('Helvetica', 14, 'bold'))
clients_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")

clients_cols = ("BSSID", "Station", "PWR", "Rate", "Lost", "Select")
clients_tree = ttk.Treeview(top_frame, columns=clients_cols, show="headings", height=10)
for col in clients_cols:
    clients_tree.heading(col, text=col)
    clients_tree.column(col, width=80)
clients_tree.grid(row=1, column=2, padx=5, pady=5)

clients_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=clients_tree.yview)
clients_tree.configure(yscrollcommand=clients_scroll.set)
clients_scroll.grid(row=1, column=3, sticky="ns")

# 2. Środkowa część: Okno tekstowe na wyniki poleceń
output_text = tk.Text(app, height=10, width=80, font=('Courier', 12))
output_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

# 3. Dolna część: przyciski
button_frame = tk.Frame(app)
button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")

def create_button(parent, text, command, row, column):
    button = tk.Button(
        parent,
        text=text,
        command=command,
        width=20,
        height=2,
        font=('Helvetica', 12)
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
