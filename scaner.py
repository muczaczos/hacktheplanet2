import tkinter as tk
import subprocess

def run_command():
    # Uruchamia polecenie bez 'sudo', bo aplikacja działa z uprawnieniami root
    process = subprocess.Popen(['airmon-ng', 'start', 'wlan1'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    output.delete(1.0, tk.END)  # Czyści okno tekstowe przed nowym wyjściem
    for line in iter(process.stdout.readline, ''):
        output.insert(tk.END, line)  # Wyświetla dane w czasie rzeczywistym
        output.update()

# Tworzenie głównego okna aplikacji
app = tk.Tk()
app.title('Airmon-NG GUI')

# Tworzenie przycisku do uruchamiania polecenia
run_button = tk.Button(
    app,
    text='Start Airmon',
    command=run_command,
    width=20,          # Szerokość przycisku (liczba znaków)
    height=2,          # Wysokość przycisku (liczba linii tekstu)
    font=('Helvetica', 16)  # Czcionka i rozmiar tekstu
)
run_button.pack()

# Tworzenie okna tekstowego do wyświetlania wyników
output = tk.Text(app, height=20, width=80)
output.pack()

# Uruchamianie aplikacji
app.mainloop()
