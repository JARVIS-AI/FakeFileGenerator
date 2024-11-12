import tkinter as tk
from tkinter import messagebox, filedialog, PhotoImage, ttk
import os
import traceback
import datetime
import random
import string
import subprocess

def choose_directory():
    directory = filedialog.askdirectory()
    if directory:
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, directory)

def get_unique_filename(full_filename):
    base, ext = os.path.splitext(full_filename)
    
    # Check if extension has multiple parts (like img.lz4), keep the full extension
    if '.' in ext[1:]:  # We skip the first dot with [1:]
        base = base + ext  # Append the full extension back to the base
        ext = ''  # Reset ext to avoid splitting the multiple part extension

    # Handle file naming when overwriting is disabled
    if not overwrite_var.get():
        # This is where the issue was — add _1, _2, _3 at the end of base, just before the extension
        i = 1
        new_filename = f"{base}_{i}{ext}"  # Start with _1 suffix on the base filename
        while os.path.exists(new_filename):
            i += 1
            new_filename = f"{base}_{i}{ext}"
        return new_filename
    else:
        # Handle file naming when overwriting is enabled (no change to filename)
        return full_filename

def show_overwrite_confirmation(existing_files):
    confirm_window = tk.Toplevel(app)
    confirm_window.title("Overwrite Warning")
    confirm_window.resizable(False, False)

    text_box = tk.Text(confirm_window, wrap="word", height=10, width=50, padx=5, pady=2)
    text_box.pack(padx=10, pady=10)

    for file in existing_files:
        text_box.insert(tk.END, file + "\n")

    text_box.config(state="disabled")

    scrollbar = tk.Scrollbar(confirm_window, command=text_box.yview)
    # scrollbar.pack(side="right", fill="y")
    text_box.config(yscrollcommand=scrollbar.set)

    result = None

    def on_confirm():
        nonlocal result
        result = True
        confirm_window.destroy()

    def on_cancel():
        nonlocal result
        result = False
        confirm_window.destroy()

    button_frame = tk.Frame(confirm_window)
    button_frame.pack(pady=10)

    yes_button = tk.Button(button_frame, text="Yes", command=on_confirm)
    yes_button.pack(side="left", padx=10)

    no_button = tk.Button(button_frame, text="No", command=on_cancel)
    no_button.pack(side="right", padx=10)

    confirm_window.grab_set()

    confirm_window.wait_window()

    return result

log_file_path = "error_log.txt"
        
def log_error(error_message):
    # Add a timestamp to each log entry
    with open(log_file_path, "a") as log_file:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {error_message}\n")

cancel_generation = False

def cancel_file_generation():
    global cancel_generation
    cancel_generation = True
    cancel_button.config(state="disabled")

def clear_entries():
    filename_entry.delete(0, tk.END)
    extension_entry.delete(0, tk.END)
    size_entry.delete(0, tk.END)
    num_files_entry.delete(0, tk.END)
    directory_entry.delete(0, tk.END)
    size_unit.set("MB")
    overwrite_var.set(1)
    randomize_var.set(False)
    directory_option.set(0)
    status_label.config(text="Ready Again...", fg="green")
    progress_bar["value"] = 0

def open_directory():
    directory = directory_entry.get()
    if not os.path.exists(directory):
        messagebox.showerror("Error", "Directory does not exist.")
        return
    
    try:
        if os.name == 'nt':  # For Windows
            subprocess.Popen(f'explorer {directory}')
        elif os.name == 'posix':  # For macOS and Linux
            subprocess.Popen(['open', directory])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open directory: {e}")

def generate_files():
    global cancel_generation
    cancel_generation = False
    
    filename = filename_entry.get()
    extension = extension_entry.get()
    directory = directory_entry.get()

    try:
        size = int(size_entry.get())
        num_files = int(num_files_entry.get())

        if size <= 0:
            status_label.config(text="Error: File size must be greater than 0.", fg="red")
            return
        
        unit = size_unit.get()
        if unit == "KB":
            size *= 1024
        elif unit == "MB":
            size *= 1024 * 1024
        elif unit == "GB":
            size *= 1024 * 1024 * 1024

    except ValueError as e:
        status_label.config(text="Error: File size and number of files must be valid integers.", fg="red")
        log_error(f"ValueError: {e}")
        return

    if not filename or not extension or size <= 0 or not directory or num_files <= 0:
        status_label.config(text="Error: Please fill in all fields correctly.", fg="red")
        log_error("Error: Invalid input fields.")
        return
    
    if overwrite_var.get():
        existing_files = [
            os.path.join(directory, f"{filename}_{i+1}.{extension}") for i in range(num_files)
            if os.path.exists(os.path.join(directory, f"{filename}_{i+1}.{extension}"))
        ]

        if existing_files:
            confirm_overwrite = show_overwrite_confirmation(existing_files)
            if not confirm_overwrite:
                status_label.config(text="File generation cancelled.", fg="blue")
                return

    generate_button.config(state="disabled")
    cancel_button.config(state="normal")

    progress_bar["value"] = 0
    progress_bar["maximum"] = size * num_files
    status_label.config(text=f"Generating {num_files} files...", fg="blue")

    chunk_size = 1024 * 1024
    total_bytes_written = 0

    success_count = 0
    failure_count = 0

    for i in range(num_files):
        if cancel_generation:
            status_label.config(text="File generation canceled by user.", fg="orange")
            break

        if directory_option.get() == 1:
            full_filename = os.path.join(directory, f"{filename}_{i+1}.{extension}")
        else:
            full_filename = os.path.join(os.getcwd(), f"{filename}_{i+1}.{extension}")

        full_filename = get_unique_filename(full_filename)

        status_label.config(text=f"Generating file {i + 1} of {num_files}...", fg="blue")
        app.update()

        try:
            with open(full_filename, "wb") as f:
                bytes_written = 0
                while bytes_written < size:
                    if cancel_generation:
                        status_label.config(text="File generation canceled by user.", fg="orange")
                        break

                    if randomize_var.get():
                        chunk = bytes(random.getrandbits(8) for _ in range(min(chunk_size, size - bytes_written)))
                    else:
                        chunk = b"\0" * min(chunk_size, size - bytes_written)

                    f.write(chunk)
                    bytes_written += len(chunk)
                    total_bytes_written += len(chunk)

                    progress_bar["value"] = total_bytes_written
                    app.update()

            if cancel_generation:
                break

            progress_bar.step(size)
            success_count += 1

        except OSError as e:
            status_label.config(text=f"I/O Error - CHECK LOG!", fg="red")
            log_error(f"OSError: {str(e)} - Filename: {full_filename}")
            failure_count += 1
            progress_bar.stop()
            return

        except Exception as e:
            status_label.config(text=f"Error: {str(e)}", fg="red")
            log_error(f"General Exception: {str(e)}\n{traceback.format_exc()}")
            failure_count += 1
            progress_bar.stop()
            return

    if not cancel_generation:
        status_label.config(text=f"{success_count} files created successfully, {failure_count} files failed.", fg="green" if failure_count == 0 else "orange")
    else:
        status_label.config(text="File generation was canceled.", fg="orange")

    progress_bar.stop()
    generate_button.config(state="normal")
    cancel_button.config(state="disabled")

def show_about():
    messagebox.showinfo("About", "Fake File Generator by JARVIS-AI\nVersion 2.1.9")

def update_directory_ui():
    if directory_option.get() == 1:
        directory_button.grid(row=4, column=0, padx=10, pady=5)
        directory_entry.grid(row=4, column=1, padx=10, pady=5)
        directory_entry.config(state="normal")
        directory_button.config(state="normal")
    else:
        directory_button.grid_forget()
        directory_entry.grid_forget()
        directory_entry.delete(0, tk.END)
        directory_entry.insert(0, os.getcwd())

app = tk.Tk()
app.title("Fake File Generator by JARVIS-AI")
app.resizable(False, False)
app.iconbitmap("ffg.ico")
app.iconphoto(True, PhotoImage(file="ffg.png"))

style = ttk.Style()
style.configure("TProgressbar", thickness=20)

menu_bar = tk.Menu(app)
app.config(menu=menu_bar)

help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

tk.Label(app, text="Filename:").grid(row=0, column=0, padx=10, pady=5)
filename_entry = tk.Entry(app)
filename_entry.grid(row=0, column=1, padx=10, pady=5)

tk.Label(app, text="Extension:").grid(row=1, column=0, padx=10, pady=5)
extension_entry = tk.Entry(app)
extension_entry.grid(row=1, column=1, padx=10, pady=5)

tk.Label(app, text="Size in").grid(row=2, sticky='w', column=0, padx=40, pady=5)
size_unit = ttk.Combobox(app, values=["Byte", "KB", "MB", "GB"], state="readonly", width=4)
size_unit.grid(row=2, column=0, sticky='e', padx=0, pady=5)
size_unit.set("MB")
size_entry = tk.Entry(app)
size_entry.grid(row=2, column=1, padx=10, pady=5)

tk.Label(app, text="Number of Files:").grid(row=3, column=0, padx=10, pady=5)
num_files_entry = tk.Entry(app)
num_files_entry.grid(row=3, column=1, padx=10, pady=5)

directory_button = tk.Button(app, text="Browse...", command=choose_directory)
directory_button.grid(row=4, column=0, padx=10, pady=5)
directory_entry = tk.Entry(app)
directory_entry.grid(row=4, column=1, padx=10, pady=5)

directory_option = tk.IntVar()
same_dir_radio = tk.Radiobutton(app, text="App directory", variable=directory_option, value=0, command=update_directory_ui)
same_dir_radio.grid(row=5, column=0, padx=10, pady=5, sticky="w")
specify_dir_radio = tk.Radiobutton(app, text="Custom directory", variable=directory_option, value=1, command=update_directory_ui)
specify_dir_radio.grid(row=5, column=1, padx=10, pady=5, sticky="w")

overwrite_var = tk.IntVar(value=1)
overwrite_checkbox = tk.Checkbutton(app, text="Allow Overwriting", variable=overwrite_var)
overwrite_checkbox.grid(row=6, column=0, columnspan=2, padx=10, pady=5)

randomize_var = tk.BooleanVar()
randomize_checkbox = tk.Checkbutton(app, text="Randomized Content", variable=randomize_var)
randomize_checkbox.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

generate_button = tk.Button(app, text="Generate Files", command=generate_files)
generate_button.grid(row=8, column=0, sticky='w', padx=10, pady=5)

cancel_button = tk.Button(app, text="Cancel", command=cancel_file_generation, state="disabled")
cancel_button.grid(row=8, column=1, sticky='e', padx=10, pady=5)

clear_button = tk.Button(app, text="Clear Entries", command=clear_entries)
clear_button.grid(row=9, column=0, sticky='w', padx=10, pady=5)

open_dir_button = tk.Button(app, text="Open Directory", command=open_directory)
open_dir_button.grid(row=9, column=1, sticky='e', padx=10, pady=5)

status_label = tk.Label(app, text="Status Ready: Waiting for action...", fg="blue")
status_label.grid(row=10, column=0, columnspan=3, padx=10, pady=10)

progress_bar = ttk.Progressbar(app, orient="horizontal", length=300, mode="determinate", style="TProgressbar")
progress_bar.grid(row=11, column=0, columnspan=3, padx=10, pady=10)

update_directory_ui()

app.mainloop()
