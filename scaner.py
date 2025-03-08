import tkinter as tk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_bssid = None  # Zmienna do przechowywania wybranego BSSID
displayed_stations = []  # Przechowuje listę odnalezionych stacji
displayed_clients = []  # Przechowuje listę klientów

def run_command(command):
    global current_process
    try:
        current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except Exception as e:
        print(f"Error: {e}\n")
    finally:
        current_process = None

def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None

def run_airodump():
    threading.Thread(target=display_airodump_results, daemon=True).start()

def display_airodump_results():
    global displayed_stations, displayed_clients
    process = subprocess.Popen(['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    for line in process.stdout:
        parts = line.split()
        if len(parts) < 6 or parts[0] == "BSSID":
            continue  # Pomijamy nagłówki i niekompletne linie
        
        if len(parts) >= 6:  # Stacje
            bssid = parts[0]
            power = parts[2]
            channel = parts[3]
            station_info = f"{bssid} | CH: {channel} | Signal: {power}"
            displayed_stations.append(station_info)
        
        if len(parts) >= 8:  # Klienci
            client_mac = parts[0]
            station_mac = parts[5]
            channel = parts[3]
            power = parts[2]
            client_info = f"{client_mac} | {station_mac} | CH: {channel} | Signal: {power}"
            displayed_clients.append(client_info)
        
    update_labels()

def update_labels():
    for widget in stations_frame.winfo_children():
        widget.destroy()
    for widget in clients_frame.winfo_children():
        widget.destroy()
    
    for station in displayed_stations:
        tk.Label(stations_frame, text=station, font=('Courier', 12)).pack(anchor='w')
    for client in displayed_clients:
        tk.Label(clients_frame, text=client, font=('Courier', 12)).pack(anchor='w')

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

app.grid_columnconfigure(0, weight=1, uniform="column")
app.grid_columnconfigure(1, weight=1, uniform="column")

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

create_button(app, 'Start Airmon', run_command, 0, 0)
create_button(app, 'Start Airodump', run_airodump, 1, 0)
create_button(app, 'Stop Command', stop_command, 1, 1)

# Nagłówki dla sekcji
stations_label = tk.Label(app, text="Stations", font=('Helvetica', 14, 'bold'))
stations_label.grid(row=2, column=0, pady=5)

clients_label = tk.Label(app, text="Clients", font=('Helvetica', 14, 'bold'))
clients_label.grid(row=2, column=1, pady=5)

# Ramki dla wyników
stations_frame = tk.Frame(app)
stations_frame.grid(row=3, column=0, padx=10, pady=10, sticky="n")

clients_frame = tk.Frame(app)
clients_frame.grid(row=3, column=1, padx=10, pady=10, sticky="n")

app.mainloop()
