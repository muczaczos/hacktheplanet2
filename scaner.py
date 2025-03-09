import tkinter as tk
from tkinter import ttk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_station = None  # Wybrana stacja (BSSID)
selected_client = None   # Wybrany klient (MAC klienta)
 
# --- Funkcje ogólne ---
def run_command(command):
    global current_process
    try:
        stop_command()  # Zatrzymaj poprzedni proces, jeśli istnieje
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
 
def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        output_text.insert(tk.END, "\n[!] Command stopped by user.\n")
 
# --- Funkcje przycisków (Twoje komendy) ---
def run_airmon():
    threading.Thread(target=run_command, args=(['airmon-ng', 'start', 'wlan1'],), daemon=True).start()
 
def run_iwconfig():
    threading.Thread(target=run_command, args=(['iwconfig'],), daemon=True).start()
 
def run_systemctl_start_networkmanager():
    threading.Thread(target=run_command, args=(['systemctl', 'start', 'NetworkManager'],), daemon=True).start()
 
def run_systemctl_stop_networkmanager():
    threading.Thread(target=run_command, args=(['systemctl', 'stop', 'NetworkManager'],), daemon=True).start()
 
def run_systemctl_restart_networkmanager():
    threading.Thread(target=run_command, args=(['systemctl', 'restart', 'NetworkManager'],), daemon=True).start()
 
def run_airmon_check_kill():
    threading.Thread(target=run_command, args=(['airmon-ng', 'check', 'kill'],), daemon=True).start()
 
def run_reaver():
    global selected_station
    if not selected_station:
        output_text.insert(tk.END, "No station selected.\n")
        return
    threading.Thread(target=run_command, args=(['reaver', '-i', 'wlan1', '-b', selected_station, '-S', '-v'],), daemon=True).start()
 
# --- Funkcje parsujące airodump-ng ---
def run_airodump():
    threading.Thread(target=display_airodump_results, daemon=True).start()
 
def display_airodump_results():
    # Czyścimy istniejące dane w tabelach
    for row in stations_tree.get_children():
        stations_tree.delete(row)
    for row in clients_tree.get_children():
        clients_tree.delete(row)
 
    process = subprocess.Popen(['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
 
    # Odczytujemy linie wyjścia
    for line in iter(process.stdout.readline, ''):
        parts = line.split()
        if not parts or parts[0] in ["BSSID", "Station", "#"]:
            continue
 
        # Używamy heurystyki: jeśli druga kolumna zawiera ':' (MAC), to jest to linia klienta,
        # w przeciwnym razie traktujemy jako stację.
        if ':' in parts[1]:
            # Linia klienta: oczekujemy: BSSID, Station, PWR, Rate, Lost
            if len(parts) < 5:
                continue
            client_mac = parts[0]
            station_mac = parts[1]
            pwr = parts[2]
            rate = parts[3]
            lost = parts[4]
            insert_client(client_mac, station_mac, pwr, rate, lost)
        else:
            # Linia stacji: oczekujemy: BSSID, PWR, Beacons, #Data, #/s, CH, MB, [opcjonalnie ESSID]
            if len(parts) < 7:
                continue
            bssid = parts[0]
            pwr = parts[1]
            beacons = parts[2]
            data_ = parts[3]
            rate_per_sec = parts[4]
            ch = parts[5]
            mb = parts[6]
            insert_station(bssid, pwr, beacons, data_, rate_per_sec, ch, mb)
 
def insert_station(bssid, pwr, beacons, data_, rate_per_sec, ch, mb):
    row_id = stations_tree.insert("", tk.END, values=(bssid, pwr, beacons, data_, rate_per_sec, ch, mb, ""))
    create_checkbox_for_tree(stations_tree, row_id, 7, bssid, is_station=True)
 
def insert_client(client_mac, station_mac, pwr, rate, lost):
    row_id = clients_tree.insert("", tk.END, values=(client_mac, station_mac, pwr, rate, lost, ""))
    create_checkbox_for_tree(clients_tree, row_id, 5, client_mac, is_station=False)
 
def create_checkbox_for_tree(tree, item_id, col_index, mac, is_station=True):
    # Pobieramy pozycję komórki
    bbox = tree.bbox(item_id, col_index)
    if not bbox:
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
    tree.create_window(x, y, anchor="nw", window=cb)
 
# --- Budowa głównego okna ---
app = tk.Tk()
app.title("Airmon-NG GUI")
 
# Konfiguracja kolumn – nie zmieniamy układu ogólnego
app.grid_columnconfigure(0, weight=1, uniform="column")
app.grid_columnconfigure(1, weight=1, uniform="column")
 
# --- GÓRA: Tabele dla Stations i Clients ---
top_frame = tk.Frame(app)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")
 
# Stations (kolumny: BSSID, PWR, Beacons, #Data, #/s, CH, MB, Select)
stations_label = tk.Label(top_frame, text="Stations", font=('Helvetica', 16, 'bold'))
stations_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
stations_cols = ("BSSID", "PWR", "Beacons", "#Data", "#/s", "CH", "MB", "Select")
stations_tree = ttk.Treeview(top_frame, columns=stations_cols, show="headings", height=10)
for col in stations_cols:
    stations_tree.heading(col, text=col)
    stations_tree.column(col, width=80)
stations_tree.grid(row=1, column=0, padx=5, pady=5)
stations_scroll = ttk.Scrollbar(top_frame, orient="vertical", command=stations_tree.yview)
stations_tree.configure(yscrollcommand=stations_scroll.set)
stations_scroll.grid(row=1, column=1, sticky="ns")
 
# Clients (kolumny: BSSID, Station, PWR, Rate, Lost, Select)
clients_label = tk.Label(top_frame, text="Clients", font=('Helvetica', 16, 'bold'))
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
 
# --- ŚRODEK: Okno tekstowe dla wyników innych komend ---
output_text = tk.Text(app, height=10, width=80, font=('Courier', 12))
output_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
 
# --- DÓŁ: Przycisków ---
button_frame = tk.Frame(app)
button_frame.grid(row=2, column=0, columnspan=2, sticky="nsew")
 
def create_button(parent, text, command, row, column):
    button = tk.Button(parent, text=text, command=command, width=20, height=2, font=('Helvetica', 20))
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
