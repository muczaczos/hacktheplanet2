import tkinter as tk
import subprocess

def run_airmon():
    # Uruchamia polecenie 'airmon-ng start wlan1'
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

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

# Przycisk do uruchamiania 'airmon-ng start wlan1'
airmon_button = tk.Button(
    app,
    text='Start Airmon',
    command=run_airmon,
    width=20,
    height=2,
    font=('Helvetica', 16)
)
airmon_button.pack(pady=10)

# Przycisk do uruchamiania 'iwconfig'
iwconfig_button = tk.Button(
    app,
    text='Show IWConfig',
    command=run_iwconfig,
    width=20,
    height=2,
    font=('Helvetica', 16)
)
iwconfig_button.pack(pady=10)

# Tworzenie okna tekstowego do wyświetlania wyników
output = tk.Text(app, height=20, width=80, font=('Courier', 14))
output.pack()

# Uruchamianie aplikacji
app.mainloop()
