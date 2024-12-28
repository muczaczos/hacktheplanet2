import tkinter as tk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_bssid = None  # Zmienna do przechowywania wybranego BSSID

def run_command(command):
    global current_process
    try:
        current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output.delete(1.0, tk.END)
        for line in iter(current_process.stdout.readline, ''):
            output.insert(tk.END, line)
            output.update()
    except Exception as e:
        output.insert(tk.END, f"Error: {e}\n")
    finally:
        current_process = None  # Proces zakończony

def stop_command():
    global current_process
    if current_process:
        current_process.terminate()  # Wysyła sygnał zakończenia do procesu
        output.insert(tk.END, "\nCommand stopped by user.\n")
        current_process = None

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

def run_airodump():
    threading.Thread(target=run_command, args=(['airodump-ng', 'wlan1'],), daemon=True).start()

def run_wash():
    # Funkcja, która uruchamia komendę 'wash' i analizuje jej wynik
    threading.Thread(target=display_wash_results, daemon=True).start()

def display_wash_results():
    process = subprocess.Popen(['wash', '-i', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output.delete(1.0, tk.END)  # Czyści wyjście przed nowymi danymi
    line_number = 0
    checkbuttons = []  # Lista przechowująca Checkbuttons
    output.insert(tk.END, "Running wash command...\n")  # Debug: informacja, że komenda 'wash' jest uruchamiana

    for line in process.stdout:
        output.insert(tk.END, f"Processing line: {line}")  # Debug: każdy wiersz z wash
        if "BSSID" in line:  # Ignoruj nagłówki
            continue
        parts = line.split()
        if len(parts) >= 6:
            bssid = parts[0]
            wps_version = parts[1]
            signal = parts[3]
            # Tworzenie GUI dla każdego klienta (BSSID)
            row = line_number // 2
            col = line_number % 2

            client_frame = tk.Frame(app)
            client_frame.grid(row=row, column=col, padx=5, pady=5)

            tk.Label(client_frame, text=f"BSSID: {bssid}, WPS: {wps_version}, Signal: {signal}", font=('Helvetica', 12)).pack(side=tk.LEFT)

            var = tk.BooleanVar(value=False)
            checkbutton = tk.Checkbutton(client_frame, text="Select", variable=var)
            checkbutton.pack(side=tk.RIGHT)

            # Przypisz do Checkbuttona funkcję zapisującą BSSID w zmiennej
            checkbutton.config(command=lambda bssid=bssid, var=var: select_bssid(bssid, var))

            checkbuttons.append((bssid, var))  # Przechowuj BSSID i zmienną stanu checkboxa
            line_number += 1

    app.update()

def select_bssid(bssid, var):
    global selected_bssid
    if var.get():
        selected_bssid = bssid
        output.insert(tk.END, f"Selected BSSID: {bssid}\n")

def run_reaver():
    if not selected_bssid:
        output.insert(tk.END, "No BSSID selected.\n")
        return
    threading.Thread(target=run_command, args=(['reaver', '-i', 'wlan1', '-b', selected_bssid, '-S', '-v'],), daemon=True).start()

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

# Konfiguracja kolumn
app.grid_columnconfigure(0, weight=1, uniform="column")
app.grid_columnconfigure(1, weight=1, uniform="column")

# Funkcja do tworzenia przycisku
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

# Przyciski w dwóch kolumnach
create_button(app, 'Start Airmon', run_airmon, 0, 0)
create_button(app, 'Show IWConfig', run_iwconfig, 0, 1)
create_button(app, 'Start NetworkManager', run_systemctl_start_networkmanager, 1, 0)
create_button(app, 'Stop NetworkManager', run_systemctl_stop_networkmanager, 1, 1)
create_button(app, 'Restart NetworkManager', run_systemctl_restart_networkmanager, 2, 0)
create_button(app, 'Airmon Check Kill', run_airmon_check_kill, 2, 1)
create_button(app, 'Start Airodump', run_airodump, 3, 0)
create_button(app, 'Wash', run_wash, 3, 1)
create_button(app, 'Reaver', run_reaver, 4, 0)
create_button(app, 'Stop Command', stop_command, 4, 1)  # Dodany przycisk do zatrzymywania procesu

# Tworzenie okna tekstowego do wyświetlania wyników z paskiem przewijania
scrollbar = tk.Scrollbar(app)
scrollbar.grid(row=5, column=2, sticky=tk.NS)

output = tk.Text(app, height=20, width=80, font=('Courier', 14), yscrollcommand=scrollbar.set)
output.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

scrollbar.config(command=output.yview)

# Uruchamianie aplikacji
app.mainloop()
