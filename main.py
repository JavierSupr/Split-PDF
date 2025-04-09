import tkinter as tk
from tkinter import filedialog, messagebox
from PyPDF2 import PdfReader, PdfWriter
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import os

zoom_scale = 2.0  # default zoom scale
pdf_path = ""     # global path untuk PDF terakhir

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
    global pdf_path
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        pdf_path = file_path
        entry_file.delete(0, tk.END)
        entry_file.insert(0, file_path)
        show_preview_all_pages()

def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        entry_folder.delete(0, tk.END)
        entry_folder.insert(0, folder_path)

def show_preview_all_pages():
    global zoom_scale, pdf_path

    if not pdf_path:
        return

    try:
        for widget in preview_frame.winfo_children():
            widget.destroy()

        base_width = int(300 * zoom_scale)
        images = convert_from_path(pdf_path, size=(base_width, None))

        for i, img in enumerate(images):
            img_tk = ImageTk.PhotoImage(img)

            # Frame horizontal untuk satu halaman dan info
            page_row = tk.Frame(preview_frame, bg="white")
            page_row.pack(fill='x', pady=5)

            # Gambar halaman di kiri
            label = tk.Label(page_row, image=img_tk, bg="white")
            label.image = img_tk
            label.pack(side='left')

            # Nomor halaman di kanan
            page_number_label = tk.Label(page_row, text=f"Halaman {i+1}", bg="white", fg="gray", font=("Arial", 12))
            page_number_label.pack(side='right', padx=10)

    except Exception as e:
        messagebox.showerror("Gagal Tampilkan Pratinjau", str(e))

def zoom_in():
    global zoom_scale
    zoom_scale += 0.1
    show_preview_all_pages()

def zoom_out():
    global zoom_scale
    if zoom_scale > 0.2:
        zoom_scale -= 0.1
        show_preview_all_pages()

def start_split():
    input_path = entry_file.get()
    output_folder = entry_folder.get()

    if not input_path or not output_folder:
        messagebox.showwarning("Peringatan", "Mohon pilih file PDF dan folder output.")
        return

    split_pdf(input_path, output_folder)

def _on_mousewheel(event):
    # Windows dan macOS
    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

def _on_linux_scroll(event):
    # Linux scroll up/down
    if event.num == 4:
        canvas.yview_scroll(-1, "units")
    elif event.num == 5:
        canvas.yview_scroll(1, "units")


# === GUI SETUP ===
root = tk.Tk()
root.title("PDF Splitter + Preview (Zoomable)")
root.geometry("1100x700")

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True)

# Left Panel
left_frame = tk.Frame(main_frame, width=300, padx=10, pady=10)
left_frame.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(left_frame, text="Pilih file PDF:").pack(anchor='w')
entry_file = tk.Entry(left_frame, width=40)
entry_file.pack(pady=(0,5))
tk.Button(left_frame, text="Browse", command=select_file).pack(pady=(0,10))

tk.Label(left_frame, text="Pilih folder output:").pack(anchor='w')
entry_folder = tk.Entry(left_frame, width=40)
entry_folder.pack(pady=(0,5))
tk.Button(left_frame, text="Browse", command=select_folder).pack(pady=(0,20))

tk.Button(left_frame, text="Split PDF", command=start_split, bg="green", fg="white", height=2, width=20).pack(pady=10)


# Right Panel (PDF Preview)
right_frame = tk.Frame(main_frame)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

right_controls_frame = tk.Frame(right_frame, padx=5, pady=5)
right_controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

tk.Label(right_controls_frame, text="Zoom:").pack(pady=(20, 5))
tk.Button(right_controls_frame, text="Zoom In (+)", command=zoom_in, width=10).pack(pady=3)
tk.Button(right_controls_frame, text="Zoom Out (-)", command=zoom_out, width=10).pack(pady=3)


canvas = tk.Canvas(right_frame, bg="white")
scroll_y = tk.Scrollbar(right_frame, orient="vertical", command=canvas.yview)
canvas.configure(yscrollcommand=scroll_y.set)

scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

preview_frame = tk.Frame(canvas, bg="white")
canvas_window = canvas.create_window((0, 0), window=preview_frame, anchor='n')

canvas.bind_all("<MouseWheel>", _on_mousewheel)

# Linux scroll support
canvas.bind_all("<Button-4>", _on_linux_scroll)
canvas.bind_all("<Button-5>", _on_linux_scroll)


def on_frame_configure(event):
    canvas.configure(scrollregion=canvas.bbox('all'))

def on_canvas_configure(event):
    # Dapatkan lebar canvas
    canvas_width = event.width
    # Update posisi preview_frame ke tengah horizontal
    canvas.itemconfig(canvas_window, width=canvas_width)


preview_frame.bind("<Configure>", on_frame_configure)
canvas.bind("<Configure>", on_canvas_configure)

root.mainloop()
