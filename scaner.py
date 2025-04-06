import tkinter as tk
from tkinter import ttk
import subprocess
import threading

# ======= GLOBALNE ZMIENNE ======= #
current_process = None
selected_station = None
selected_client = None
station_clients = {}  # BSSID -> lista MAC klientów
all_clients = []      # przechowujemy pełną listę klientów

# ======= FUNKCJE OGÓLNE ======= #
def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        output_text.insert(tk.END, "\n[!] Command stopped by user.\n")

def run_command(command):
    global current_process
    try:
        stop_command()
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

# ======= PRZYCISKI ======= #
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
    run_command(['reaver', '-i', 'wlan1', '-b', selected_station, '-S', '-v'])

# ======= AIRODUMP ======= #
def run_airodump():
    threading.Thread(target=parse_airodump_output, daemon=True).start()

def parse_airodump_output():
    global station_clients, all_clients
    station_clients = {}
    all_clients = []

    for row in stations_tree.get_children():
        stations_tree.delete(row)
    for row in clients_tree.get_children():
        clients_tree.delete(row)

    stop_command()
    process = subprocess.Popen(
        ['airodump-ng', 'wlan1'],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    parse_mode = None
    for line in iter(process.stdout.readline, ''):
        line_str = line.strip()
        print("DBG:", line_str)  # dodaj to
        if not line_str:
            parse_mode = None
            continue
        if line_str.startswith("BSSID "):
            parse_mode = "AP"
            continue
        if line_str.startswith("STATION "):
            parse_mode = "STA"
            continue
        if parse_mode is None:
            continue
        if parse_mode == "AP":
            parse_ap_line(line_str)
        elif parse_mode == "STA":
            parse_sta_line(line_str)

def parse_ap_line(line_str):
    parts = line_str.split(None, 10)
    if len(parts) < 10:
        return
    bssid    = parts[0]
    pwr      = parts[1]
    beacons  = parts[2]
    data_    = parts[3]
    per_s    = parts[4]
    ch       = parts[5]
    mb       = parts[6]
    enc      = parts[7]
    cipher   = parts[8]
    auth_    = parts[9]
    essid    = parts[10] if len(parts) > 10 else ""

    station_clients[bssid] = []  # Zainicjuj listę klientów
    insert_station(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid)

def parse_sta_line(line_str):
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

    # Próbujemy przypisać klienta do BSSID (z pola 'Probes')
    bssid = None
    for possible_bssid in station_clients:
        if possible_bssid.lower() in probes.lower():
            bssid = possible_bssid
            station_clients[bssid].append((station_mac, pwr, rate, lost, frames, notes, probes))
            break

    all_clients.append((station_mac, pwr, rate, lost, frames, notes, probes))
    insert_client(station_mac, pwr, rate, lost, frames, notes, probes)

# ======= TABELA ======= #
def insert_station(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid):
    row_id = stations_tree.insert(
        "", tk.END,
        values=(bssid, pwr, beacons, data_, per_s, ch, mb, enc, cipher, auth_, essid, "")
    )
    create_checkbox_for_tree(stations_tree, row_id, 11, bssid, is_station=True)

def insert_client(station_mac, pwr, rate, lost, frames, notes, probes):
    row_id = clients_tree.insert(
        "", tk.END,
        values=(station_mac, pwr, rate, lost, frames, notes, probes, "")
    )
    create_checkbox_for_tree(clients_tree, row_id, 7, station_mac, is_station=False)

def create_checkbox_for_tree(tree, item_id, col_index, mac, is_station=True):
    bbox = tree.bbox(item_id, col_index)
    if not bbox:
        tree.after(100, lambda: create_checkbox_for_tree(tree, item_id, col_index, mac, is_station))
        return

    x, y, width, height = bbox
    var = tk.BooleanVar()

    def on_check():
        if var.get():
            if is_station:
                global selected_station
                selected_station = mac
                print(f"[Selected Station] {mac}")
                filter_clients_by_station(mac)
            else:
                global selected_client
                selected_client = mac
                print(f"[Selected Client] {mac}")
        else:
            if is_station:
                clear_client_filter()

    cb = tk.Checkbutton(tree, variable=var, command=on_check)
    tree.create_window(x, y, anchor="nw", window=cb)

def filter_clients_by_station(bssid):
    clients_tree.delete(*clients_tree.get_children())
    clients = station_clients.get(bssid, [])
    for client in clients:
        insert_client(*client)

def clear_client_filter():
    clients_tree.delete(*clients_tree.get_children())
    for client in all_clients:
        insert_client(*client)

# ======= INTERFEJS GRAFICZNY ======= #
app = tk.Tk()
app.title("Airmon-NG GUI")

app.grid_columnconfigure(0, weight=1, uniform="column")
app.grid_columnconfigure(1, weight=1, uniform="column")

top_frame = tk.Frame(app)
top_frame.grid(row=0, column=0, columnspan=2, sticky="nsew")

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

output_text = tk.Text(app, height=10, width=80, font=('Courier', 12))
output_text.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")

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
