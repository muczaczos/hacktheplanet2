import tkinter as tk
import subprocess
import threading

def run_command(command):
    # Ogólna funkcja do uruchamiania poleceń
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)
        output.update()

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

def run_airodump():
    # Uruchamia 'airodump-ng wlan1' w osobnym wątku, aby nie blokować GUI
    def airodump_process():
        run_command(['airodump-ng', 'wlan1'])
    threading.Thread(target=airodump_process, daemon=True).start()

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
        font=('Helvetica', 14)
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

# Tworzenie okna tekstowego do wyświetlania wyników z paskiem przewijania
scrollbar = tk.Scrollbar(app)
scrollbar.grid(row=4, column=2, sticky=tk.NS)

output = tk.Text(app, height=20, width=80, font=('Courier', 14), yscrollcommand=scrollbar.set)
output.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

scrollbar.config(command=output.yview)

# Uruchamianie aplikacji
app.mainloop()
