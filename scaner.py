import tkinter as tk
from tkinter import ttk
import subprocess
import threading
import re

current_process = None

def run_airodump():
    global current_process
    if current_process:
        return  # Unikamy uruchamiania kilku instancji naraz

    def update_airodump():
        """Czyta dane z airodump-ng i dynamicznie aktualizuje tabelę."""
        global current_process
        seen_bssids = {}  # Przechowuje BSSID -> wpis w tabeli
        
        for line in iter(current_process.stdout.readline, ''):
            match = re.match(r'([0-9A-F:]{17})\s+(-?\d+)\s+\d+\s+\d+\s+(\d+)\s+(\d+)\s+(.*?)\s+(WPA2?|WEP|OPN)?', line)
            if match:
                bssid, power, beacons, data, essid, enc = match.groups()
                power = int(power)  # Siła sygnału jako liczba

                if bssid not in seen_bssids:
                    table.insert("", tk.END, values=(bssid, essid, power, enc))
                    seen_bssids[bssid] = table.get_children()[-1]
                else:
                    table.item(seen_bssids[bssid], values=(bssid, essid, power, enc))

            # Usuwanie z listy nieaktywnych stacji
            for bssid in list(seen_bssids.keys()):
                if bssid not in line:
                    table.delete(seen_bssids[bssid])
                    del seen_bssids[bssid]

        current_process = None  # Proces zakończony

    try:
        current_process = subprocess.Popen(
            ['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True
        )
        threading.Thread(target=update_airodump, daemon=True).start()
    except Exception as e:
        status_label.config(text=f"Error: {e}")

def stop_airodump():
    """Zatrzymuje proces airodump-ng."""
    global current_process
    if current_process:
        current_process.terminate()
        current_process = None
        status_label.config(text="Airodump Stopped.")

# Tworzenie GUI
app = tk.Tk()
app.title("Airodump-NG GUI")

# Tabela wyników
columns = ("BSSID", "ESSID", "Power", "Encryption")
table = ttk.Treeview(app, columns=columns, show="headings", height=15)
for col in columns:
    table.heading(col, text=col)
    table.column(col, width=150)
table.pack(padx=10, pady=10, fill="both", expand=True)

# Przyciski
btn_start = tk.Button(app, text="Start Airodump", command=run_airodump)
btn_stop = tk.Button(app, text="Stop Airodump", command=stop_airodump)
btn_start.pack(side=tk.LEFT, padx=10, pady=5)
btn_stop.pack(side=tk.RIGHT, padx=10, pady=5)

# Status
status_label = tk.Label(app, text="Ready", fg="blue")
status_label.pack()

app.mainloop()
