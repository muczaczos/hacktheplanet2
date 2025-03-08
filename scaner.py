import tkinter as tk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_bssid = None  # Zmienna do przechowywania wybranego BSSID
displayed_stations = []  # Przechowuje stacje
displayed_clients = []  # Przechowuje klientów

def run_command(command):
    global current_process
    try:
        current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        current_process = None  # Proces zakończony

def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None

def run_airmon():
    threading.Thread(target=run_command, args=(['airmon-ng', 'start', 'wlan1'],), daemon=True).start()

def run_airodump():
    threading.Thread(target=display_airodump_results, daemon=True).start()

def display_airodump_results():
    global displayed_stations, displayed_clients
    process = subprocess.Popen(['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        parts = line.split()
        if len(parts) < 6 or parts[0] == "BSSID":
            continue  # Pomijamy nagłówki i niekompletne linie
        
        if len(parts) >= 6 and len(parts) < 8:
            bssid = parts[0]
            power = parts[2]  # RSSI/Sygnał
            channel = parts[3]
            station_data = f"{bssid} | CH: {channel} | Signal: {power}"
            displayed_stations.append(station_data)
        
        if len(parts) >= 8:
            client_mac = parts[0]
            station_mac = parts[5]
            power = parts[3]
            channel = parts[4]
            client_data = f"{client_mac} | {station_mac} | CH: {channel} | Signal: {power}"
            displayed_clients.append(client_data)
        
    update_display()

def update_display():
    station_list.delete(0, tk.END)
    client_list.delete(0, tk.END)
    for station in displayed_stations:
        station_list.insert(tk.END, station)
    for client in displayed_clients:
        client_list.insert(tk.END, client)

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

# Nagłówki kolumn
header_frame = tk.Frame(app)
header_frame.grid(row=0, column=0, columnspan=2, pady=5)

tk.Label(header_frame, text="Stations", font=("Helvetica", 14, "bold")).grid(row=0, column=0, padx=50)
tk.Label(header_frame, text="Clients", font=("Helvetica", 14, "bold")).grid(row=0, column=1, padx=50)

# Listboxy do wyświetlania wyników
station_list = tk.Listbox(app, height=20, width=50, font=('Courier', 12))
station_list.grid(row=1, column=0, padx=10, pady=10)

client_list = tk.Listbox(app, height=20, width=50, font=('Courier', 12))
client_list.grid(row=1, column=1, padx=10, pady=10)

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

create_button(app, 'Start Airmon', run_airmon, 2, 0)
create_button(app, 'Start Airodump', run_airodump, 2, 1)
create_button(app, 'Stop Command', stop_command, 3, 0)

app.mainloop()
