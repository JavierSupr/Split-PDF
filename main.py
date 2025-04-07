import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
import os

def split_pdf(input_path, output_folder):
    try:
        reader = PdfReader(input_path)
        for i in range(len(reader.pages)):
            writer = PdfWriter()
            writer.add_page(reader.pages[i])

            output_filename = os.path.join(output_folder, f"page_{i + 1}.pdf")
            with open(output_filename, "wb") as output_file:
                writer.write(output_file)
        messagebox.showinfo("Berhasil", f"PDF berhasil di-split ke folder:\n{output_folder}")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def select_file():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder_path)

def start_split():
    input_path = entry_file.get()
    output_folder = entry_folder.get()

    if not input_path or not output_folder:
        messagebox.showwarning("Peringatan", "Mohon pilih file PDF dan folder output.")
        return

    split_pdf(input_path, output_folder)

# GUI Setup
root = tk.Tk()
root.title("PDF Splitter")
root.geometry("400x200")

# Input file
tk.Label(root, text="Pilih file PDF:").pack(pady=(10, 0))
entry_file = tk.Entry(root, width=50)
entry_file.pack()
tk.Button(root, text="Browse", command=select_file).pack(pady=5)

# Output folder
tk.Label(root, text="Pilih folder output:").pack(pady=(10, 0))
entry_folder = tk.Entry(root, width=50)
entry_folder.pack()
tk.Button(root, text="Browse", command=select_folder).pack(pady=5)

# Split button
tk.Button(root, text="Split PDF", command=start_split, bg="green", fg="white").pack(pady=15)

root.mainloop()
