
import tkinter as tk
from tkinter import scrolledtext
import subprocess

def run_poolmap():
    from_token = from_entry.get()
    to_token = to_entry.get()
    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, f"Running analysis for {from_token} to {to_token}...\n")
    
    command = [
        "venv/bin/python", 
        "poolmap.py",
        "--from",
        from_token,
        "--to",
        to_token
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    def stream_output():
        if process.stdout:
            for line in iter(process.stdout.readline, ''):
                output_text.insert(tk.END, line)
                output_text.see(tk.END)
                window.update_idletasks()
        if process.stderr:
            for line in iter(process.stderr.readline, ''):
                output_text.insert(tk.END, line)
                output_text.see(tk.END)
                window.update_idletasks()
        process.stdout.close()
        process.stderr.close()
        process.wait()
        output_text.insert(tk.END, "\nAnalysis complete.")

    window.after(100, stream_output)

def save_transaction():
    output_text.insert(tk.END, "\nSaving transaction...\n")
    # TODO: Implement JSON generation and saving
    output_text.insert(tk.END, "Transaction saved (placeholder).\n")

# Create the main window
window = tk.Tk()
window.title("Poolmap GUI")

# Create and pack the widgets
tk.Label(window, text="From Token:").pack(pady=5)
from_entry = tk.Entry(window, width=30)
from_entry.pack(pady=5)
from_entry.insert(0, "BTWTY.EOS")

tk.Label(window, text="To Token:").pack(pady=5)
to_entry = tk.Entry(window, width=30)
to_entry.pack(pady=5)
to_entry.insert(0, "IOB.XRP")

run_button = tk.Button(window, text="Run Analysis", command=run_poolmap)
run_button.pack(pady=10)

save_button = tk.Button(window, text="Save Transaction", command=save_transaction)
save_button.pack(pady=10)

output_text = scrolledtext.ScrolledText(window, width=80, height=20)
output_text.pack(pady=10)

# Start the GUI event loop
window.mainloop()
