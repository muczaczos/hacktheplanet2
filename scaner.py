import tkinter as tk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_bssid = None  # Zmienna do przechowywania wybranego BSSID
displayed_bssids = {}  # Przechowuje aktualnie wyświetlane BSSID

def run_command(command):
    global current_process
    try:
        current_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in iter(current_process.stdout.readline, ''):
            update_output(line)
    except Exception as e:
        update_output(f"Error: {e}\n")
    finally:
        current_process = None  # Proces zakończony

def stop_command():
    global current_process
    if current_process:
        current_process.terminate()
        update_output("\nCommand stopped by user.\n")
        current_process = None

def update_output(text):
    output_label.config(text=text)

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
    threading.Thread(target=display_airodump_results, daemon=True).start()

def display_airodump_results():
    global displayed_bssids
    process = subprocess.Popen(['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    for line in process.stdout:
        parts = line.split()
        if len(parts) < 6 or parts[0] == "BSSID":
            continue  
        bssid = parts[0]
        power = parts[2]  
        channel = parts[3]
        essid = " ".join(parts[5:]) if len(parts) > 5 else "Unknown"
        displayed_bssids[bssid] = f"{bssid} | CH: {channel} | Signal: {power} | {essid}"
        update_output("\n".join(displayed_bssids.values()))

def run_wash():
    threading.Thread(target=run_command, args=(['wash', '-i', 'wlan1'],), daemon=True).start()

def run_reaver():
    if not selected_bssid:
        update_output("No BSSID selected.")
        return
    threading.Thread(target=run_command, args=(['reaver', '-i', 'wlan1', '-b', selected_bssid, '-S', '-v'],), daemon=True).start()

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

create_button(app, 'Start Airmon', run_airmon, 0, 0)
create_button(app, 'Show IWConfig', run_iwconfig, 0, 1)
create_button(app, 'Start NetworkManager', run_systemctl_start_networkmanager, 1, 0)
create_button(app, 'Stop NetworkManager', run_systemctl_stop_networkmanager, 1, 1)
create_button(app, 'Restart NetworkManager', run_systemctl_restart_networkmanager, 2, 0)
create_button(app, 'Airmon Check Kill', run_airmon_check_kill, 2, 1)
create_button(app, 'Start Airodump', run_airodump, 3, 0)
create_button(app, 'Wash', run_wash, 3, 1)
create_button(app, 'Reaver', run_reaver, 4, 0)
create_button(app, 'Stop Command', stop_command, 4, 1)

output_label = tk.Label(app, text="Output will be displayed here", font=('Courier', 14), justify="left", anchor="w")
output_label.grid(row=5, column=0, columnspan=2, padx=10, pady=10, sticky="w")

app.mainloop()
