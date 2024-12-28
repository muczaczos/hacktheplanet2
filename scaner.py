import tkinter as tk
import subprocess

def run_airmon():
    # Uruchamia polecenie 'sudo airmon-ng start wlan1'
    process = subprocess.Popen(['airmon-ng', 'start', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

def run_iwconfig():
    # Uruchamia polecenie 'iwconfig'
    process = subprocess.Popen(['iwconfig'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

def run_network_manager():
    # Uruchamia polecenie 'systemctl start NetworkManager'
    process = subprocess.Popen(['systemctl', 'start', 'NetworkManager'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

def run_airmon_check_kill():
    # Uruchamia polecenie 'airmon-ng check kill'
    process = subprocess.Popen(['airmon-ng', 'check', 'kill'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

def run_airodump():
    # Uruchamia polecenie 'airodump-ng wlan1'
    process = subprocess.Popen(['airodump-ng', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

# Przycisk do uruchamiania 'sudo airmon-ng start wlan1'
sudo_airmon_button = tk.Button(
    app,
    text='Start Airmon',
    command=run_airmon,
    width=25,
    height=2,
    font=('Helvetica', 16)
)
sudo_airmon_button.pack(pady=10)

# Przycisk do uruchamiania 'iwconfig'
iwconfig_button = tk.Button(
    app,
    text='Show IWConfig',
    command=run_iwconfig,
    width=25,
    height=2,
    font=('Helvetica', 16)
)
iwconfig_button.pack(pady=10)

# Przycisk do uruchamiania 'systemctl start NetworkManager'
network_manager_button = tk.Button(
    app,
    text='Start Network Manager',
    command=run_network_manager,
    width=25,
    height=2,
    font=('Helvetica', 16)
)
network_manager_button.pack(pady=10)

# Przycisk do uruchamiania 'airmon-ng check kill'
airmon_check_kill_button = tk.Button(
    app,
    text='Check Kill Airmon',
    command=run_airmon_check_kill,
    width=25,
    height=2,
    font=('Helvetica', 16)
)
airmon_check_kill_button.pack(pady=10)

# Przycisk do uruchamiania 'airodump-ng wlan1'
airodump_button = tk.Button(
    app,
    text='Start Airodump',
    command=run_airodump,
    width=25,
    height=2,
    font=('Helvetica', 16)
)
airodump_button.pack(pady=10)

# Tworzenie okna tekstowego do wyświetlania wyników
output = tk.Text(app, height=20, width=80, font=('Courier', 14))
output.pack()

# Uruchamianie aplikacji
app.mainloop()
