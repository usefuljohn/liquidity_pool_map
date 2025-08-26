import itertools
import json
import queue
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter.scrolledtext import ScrolledText

from min_to_receive import wrapper
from poolmap import main as pathfind
from rpc import wss_handshake


class StdoutRedirector:
    """File-like object to replace sys.stdout; puts text into a queue."""

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        # tkinter expects str; ignore empty writes
        if text:
            self.queue.put(text)

    def flush(self):
        pass  # required for some code that calls flush()


def run_poolmap(result_holder, from_entry, to_entry, amt_entry, output_text, window):
    from_token = from_entry.get()
    to_token = to_entry.get()

    output_text.delete(1.0, tk.END)
    output_text.insert(tk.END, f"Running analysis for {from_token} to {to_token}...\n")

    child = threading.Thread(
        target=pathfind,
        kwargs={
            "from_token": from_token,
            "to_token": to_token,
            "input_amount": float(amt_entry.get()),
            "result_holder": result_holder,
        },
    )
    child.start()

    def stream_output():
        while child.is_alive():
            window.update_idletasks()
            window.update()
            time.sleep(0.1)

        output_text.insert(tk.END, "\nAnalysis complete.")

    window.after(100, stream_output)


def build_transaction(output_text, amt_entry, result):
    output_text.insert(tk.END, "\nBuilding transaction...\n")
    _, asset_ids, pool_ids, balances, fees = result["result"]

    input_amt = float(amt_entry.get())
    original_input_amt = float(amt_entry.get())

    rpc = result["rpc"]

    edicts = []
    for pool, pool_id, fee, ids in zip(balances, pool_ids, fees, itertools.pairwise(asset_ids)):
        output_amt = wrapper(
            rpc,
            input_amt,
            fee,
            pool[0],
            pool[1],
            f"1.3.{pool[2]}",
            f"1.3.{pool[3]}",
            f"1.3.{ids[0]}",
        )

        edicts.append(
            {
                "amount_to_sell": input_amt,
                "min_to_receive": output_amt,
                "pool": pool_id,
            }
        )

        input_amt = output_amt

    print(json.dumps(edicts, indent=2))
    print("final price:", original_input_amt / output_amt)
    # TODO: Implement JSON generation and saving
    output_text.insert(tk.END, "Transaction saved.\n")


def main():
    # Create the main window
    window = tk.Tk()
    window.title("Poolmap GUI")

    result_holder = {}

    # Create and pack the widgets
    tk.Label(window, text="From Token:").grid(column=0, row=0)
    from_entry = tk.Entry(window, width=30)
    from_entry.grid(column=1, row=0)
    from_entry.insert(0, "BTWTY.EOS")

    tk.Label(window, text="To Token:").grid(column=0, row=1)
    to_entry = tk.Entry(window, width=30)
    to_entry.grid(column=1, row=1)
    to_entry.insert(0, "IOB.XRP")

    tk.Label(window, text="Amount:").grid(column=0, row=2)
    amt_entry = tk.Entry(window, width=30)
    amt_entry.grid(column=1, row=2)
    amt_entry.insert(0, "1.0")

    save_button = tk.Button(
        window,
        text="Save Transaction",
        command=lambda: build_transaction(output_text, amt_entry, result_holder),
    )
    save_button.grid(column=1, row=3, pady=20)

    output_text = scrolledtext.ScrolledText(window, width=100, height=30)
    output_text.grid(column=0, row=4, columnspan=2)

    run_button = tk.Button(
        window,
        text="Run Analysis",
        command=lambda: run_poolmap(
            result_holder, from_entry, to_entry, amt_entry, output_text, window
        ),
    )
    run_button.grid(column=0, row=3, pady=20)

    def gui_updater(window, text_widget, queue):
        """Transfer queued text into the ScrolledText widget periodically."""
        try:
            while True:
                s = queue.get_nowait()
                text_widget.configure(state="normal")
                text_widget.insert(tk.END, s)
                text_widget.see(tk.END)
                text_widget.configure(state="disabled")
        except:
            pass
        window.after(100, gui_updater, window, text_widget, queue)

    q = queue.Queue()
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = StdoutRedirector(q)  # redirect stdout
    sys.stderr = StdoutRedirector(q)  # redirect stderr
    # Start GUI updater loop
    window.after(100, gui_updater, window, output_text, q)

    # Restore stdout on close
    def on_close():
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)
    # Start the GUI event loop
    window.mainloop()


if __name__ == "__main__":
    main()
