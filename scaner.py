import tkinter as tk
import subprocess
import threading

current_process = None  # Globalna zmienna przechowująca aktualny proces
selected_bssid = tk.StringVar(value="")  # Zmienna do przechowywania wybranego BSSID

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

def parse_wash_output():
    global current_process
    process = subprocess.Popen(['wash', '-i', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    bssid_list = []
    for line in process.stdout:
        if "Lck" in line or "BSSID" in line:
            # Pomija nagłówki i wiersze niezawierające danych klientów
            continue
        parts = line.split()
        if len(parts) >= 6 and parts[4] == "No":  # Sprawdź, czy 'Lck' jest 'No'
            bssid = parts[0]
            bssid_list.append(bssid)
    return bssid_list

def run_wash_and_show_clients():
    bssid_list = parse_wash_output()
    if not bssid_list:
        output.insert(tk.END, "No clients found with 'Lck: No'.\n")
        return
    
    # Tworzenie radiobuttonów dla każdego BSSID
    client_frame = tk.Frame(app)
    client_frame.grid(row=5, column=0, columnspan=2, padx=10, pady=10)
    
    tk.Label(client_frame, text="Select a client BSSID:", font=('Helvetica', 14)).pack()
    
    for bssid in bssid_list:
        tk.Radiobutton(
            client_frame,
            text=bssid,
            variable=selected_bssid,
            value=bssid,
            font=('Helvetica', 12)
        ).pack(anchor=tk.W)

def run_reaver():
    if not selected_bssid.get():
        output.insert(tk.END, "No BSSID selected.\n")
        return
    bssid = selected_bssid.get()
    threading.Thread(target=run_command, args=(['reaver', '-i', 'wlan1', '-b', bssid, '-S', '-v'],), daemon=True).start()

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
create_button(app, 'Wash', run_wash_and_show_clients, 0, 0)
create_button(app, 'Run Reaver', run_reaver, 0, 1)
create_button(app, 'Stop Command', stop_command, 1, 0)

# Tworzenie okna tekstowego do wyświetlania wyników z paskiem przewijania
scrollbar = tk.Scrollbar(app)
scrollbar.grid(row=4, column=2, sticky=tk.NS)

output = tk.Text(app, height=20, width=80, font=('Courier', 14), yscrollcommand=scrollbar.set)
output.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

scrollbar.config(command=output.yview)

# Uruchamianie aplikacji
app.mainloop()
