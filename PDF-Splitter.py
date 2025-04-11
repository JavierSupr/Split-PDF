import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
import zipfile
import os

from PyPDF2 import PdfReader, PdfWriter
from PIL import Image, ImageTk
import fitz  # PyMuPDF untuk preview PDF


class PDFSplitterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Splitter - Multi Page Example")
        self.geometry("1200x800")
        self.resizable(False, False)
        ctk.set_appearance_mode("dark")

        # Container frame untuk menampung "halaman"
        self.container = ctk.CTkFrame(self, fg_color="#1e1e1e")
        self.container.pack(fill="both", expand=True)

        # Dictionary untuk menyimpan halaman
        self.pages = {}

        # Buat 3 halaman (WelcomePage, GeneralSplitPage, FormattedSplitPage)
        for PageClass in (WelcomePage, GeneralSplitPage, FormattedSplitPage):
            page_name = PageClass.__name__
            frame = PageClass(parent=self.container, controller=self)
            self.pages[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Tampilkan halaman WelcomePage dulu
        self.show_page("WelcomePage")

    def show_page(self, page_name):
        """Menampilkan halaman tertentu by name."""
        page = self.pages[page_name]
        page.tkraise()


# =======================================
# 1) WELCOME PAGE
# =======================================
class WelcomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2c2c2c")
        self.controller = controller
        self.configure(width=1200, height=800)

        # Label judul
        ctk.CTkLabel(self, text="Selamat Datang di PDF Splitter", font=("Arial", 32, "bold")).pack(pady=30)

        # Frame scrollable untuk tutorial
        tutorial_frame = ctk.CTkScrollableFrame(self, width=800, height=400, fg_color="#333333")
        tutorial_frame.pack(pady=20)

        # Contoh isi tutorial (label panjang)
        tutorial_text = (
            "Tutorial Penggunaan:\n\n"
            "1. Untuk split per halaman atau range, gunakan menu 'General Split'.\n"
            "2. Jika Anda ingin split berdasarkan format tertentu (mis. Kuitansi, Invoice, dll.), "
            "   gunakan 'Formatted Split'.\n"
            "3. Pada tiap halaman, Anda bisa:\n"
            "   - Memilih file PDF.\n"
            "   - Memilih folder output.\n"
            "   - Mengatur range halaman atau label.\n"
            "   - Melihat preview PDF, melakukan zoom in/out, dan dragging/panning.\n"
            "   - Menyimpan hasil split.\n"
            "4. Jika ingin hasil akhir di-zip, centang opsi 'Save as ZIP'.\n\n"
            "Semoga membantu!"
        )
        ctk.CTkLabel(tutorial_frame, text=tutorial_text, font=("Arial", 16), wraplength=750, justify="left").pack(padx=20, pady=20)

        # Tombol navigasi
        nav_frame = ctk.CTkFrame(self, fg_color="#2c2c2c")
        nav_frame.pack(pady=20)

        btn_general = ctk.CTkButton(
            nav_frame, text="General Split", width=200, height=50,
            font=("Arial", 16, "bold"), fg_color="#007BFF",
            command=lambda: controller.show_page("GeneralSplitPage")
        )
        btn_general.grid(row=0, column=0, padx=20)

        btn_formatted = ctk.CTkButton(
            nav_frame, text="Formatted Split", width=200, height=50,
            font=("Arial", 16, "bold"), fg_color="#FF5733",
            command=lambda: controller.show_page("FormattedSplitPage")
        )
        btn_formatted.grid(row=0, column=1, padx=20)


# =======================================
# 2) GENERAL SPLIT PAGE
# =======================================
class GeneralSplitPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2c2c2c")
        self.controller = controller

        self.pdf_doc = None
        self.current_page = 0
        self.page_count = 0
        self.zoom_factor = 1.0  # Awal 1x
        self.min_zoom = 0.4
        self.max_zoom = 3.0

        # Var
        self.pdf_path = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.split_option = ctk.StringVar(value="Per Halaman")
        self.range_var = ctk.StringVar()
        self.split_data = []
        self.rename_entries = []
        self.save_as_zip = ctk.BooleanVar(value=False)  # Checkbox

        # Tombol BACK di kiri atas
        back_button = ctk.CTkButton(self, text="← Back", width=70, command=lambda: controller.show_page("WelcomePage"))
        back_button.pack(anchor="nw", padx=10, pady=10)

        # Judul
        ctk.CTkLabel(self, text="General Split", font=("Arial", 20, "bold")).pack(pady=5)

        # Frame utama
        main_frame = ctk.CTkFrame(self, fg_color="#333333")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left Frame (Option)
        left_option = ctk.CTkFrame(main_frame, fg_color="#2c2c2c")
        left_option.pack(side="left", fill="y", padx=10, pady=10)

        # Browse PDF
        ctk.CTkLabel(left_option, text="Pilih PDF:", font=("Arial", 14)).pack(pady=(10,0), anchor="w")
        ctk.CTkEntry(left_option, textvariable=self.pdf_path, width=300, state="readonly").pack(pady=5, anchor="w")
        ctk.CTkButton(left_option, text="Browse PDF", command=self.browse_pdf).pack(pady=(0,10), anchor="w")

        # Folder output
        ctk.CTkLabel(left_option, text="Folder Output:", font=("Arial", 14)).pack(pady=(0,0), anchor="w")
        ctk.CTkEntry(left_option, textvariable=self.output_folder, width=300, state="readonly").pack(pady=5, anchor="w")
        ctk.CTkButton(left_option, text="Browse Folder", command=self.browse_folder).pack(pady=(0,10), anchor="w")

        # Metode split
        ctk.CTkLabel(left_option, text="Metode Split:", font=("Arial", 14)).pack(anchor="w")
        split_combo = ctk.CTkComboBox(
            left_option, values=["Per Halaman", "Range Halaman"],
            variable=self.split_option, command=self.toggle_range
        )
        split_combo.pack(pady=5, anchor="w")

        # Range entry
        self.range_label = ctk.CTkLabel(left_option, text="Range Halaman:", font=("Arial", 14))
        self.range_entry = ctk.CTkEntry(left_option, textvariable=self.range_var, placeholder_text="Contoh: 1-3,4-5,7")

        if self.split_option.get() == "Per Halaman":
            self.range_label.pack_forget()
            self.range_entry.pack_forget()
        else:
            self.range_label.pack(pady=(5,0), anchor="w")
            self.range_entry.pack(pady=(0,10), anchor="w")

        # Tombol Generate
        ctk.CTkButton(left_option, text="Generate Splits", command=self.generate_splits).pack(pady=10, anchor="w")

        # Frame rename
        self.rename_frame = ctk.CTkScrollableFrame(left_option, fg_color="#3c3c3c", width=300, height=150)
        self.rename_frame.pack(padx=5, pady=5, fill="x")

        # Checkbox Save as ZIP
        ctk.CTkCheckBox(left_option, text="Save as ZIP?", variable=self.save_as_zip).pack(pady=10, anchor="w")

        # Tombol Split
        ctk.CTkButton(left_option, text="Split PDF", fg_color="#28A745", command=self.split_pdf).pack(pady=10)

        # Right Frame (Preview)
        right_preview = ctk.CTkFrame(main_frame, fg_color="#2c2c2c")
        right_preview.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Canvas + Scroll
        self.canvas = tk.Canvas(right_preview, bg="black", width=600, height=600)
        self.canvas.pack(fill="both", expand=True)

        # Binding event untuk drag/pan
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)

        self.start_x = 0
        self.start_y = 0
        self.pan_x = 0
        self.pan_y = 0

        # Frame navigasi (zoom + next/prev)
        nav_frame = ctk.CTkFrame(right_preview, fg_color="#2c2c2c")
        nav_frame.pack(pady=5, fill="x")

        self.prev_btn = ctk.CTkButton(nav_frame, text="◀ Prev Page", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(nav_frame, text="0/0", font=("Arial", 14))
        self.page_label.pack(side="left", padx=5)

        self.next_btn = ctk.CTkButton(nav_frame, text="Next Page ▶", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)

        ctk.CTkButton(nav_frame, text="Zoom -", command=self.zoom_out).pack(side="right", padx=5)
        ctk.CTkButton(nav_frame, text="Zoom +", command=self.zoom_in).pack(side="right", padx=5)

    # ========== ZOOM & PAN FUNGSI ==========
    def zoom_in(self):
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += 0.2
            self.update_preview()

    def zoom_out(self):
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= 0.2
            self.update_preview()

    def start_pan(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def do_pan(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.start_x = event.x
        self.start_y = event.y
        self.canvas.move(self.canvas_img, dx, dy)
        self.pan_x += dx
        self.pan_y += dy

    def browse_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            self.pdf_path.set(os.path.basename(file_path))
            self.full_pdf_path = file_path
            self.load_pdf(file_path)

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.output_folder.set(folder_path)

    def toggle_range(self, evt=None):
        if self.split_option.get() == "Per Halaman":
            self.range_label.pack_forget()
            self.range_entry.pack_forget()
        else:
            self.range_label.pack(pady=(5,0), anchor="w")
            self.range_entry.pack(pady=(0,10), anchor="w")

    def load_pdf(self, pdf_path):
        self.pdf_doc = fitz.open(pdf_path)
        self.page_count = len(self.pdf_doc)
        self.current_page = 0
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_preview()

    def update_preview(self):
        if not self.pdf_doc:
            return
        page = self.pdf_doc[self.current_page]
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas_img = self.canvas.create_image(self.pan_x, self.pan_y, image=self.tk_img, anchor="nw")
        self.canvas.config(scrollregion=(0,0, pix.width, pix.height))

        self.page_label.configure(text=f"{self.current_page+1}/{self.page_count}")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.pan_x = 0
            self.pan_y = 0
            self.update_preview()

    def next_page(self):
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.pan_x = 0
            self.pan_y = 0
            self.update_preview()

    def generate_splits(self):
        if not self.full_pdf_path:
            messagebox.showerror("Error", "Pilih file PDF terlebih dahulu!")
            return

        for w in self.rename_frame.winfo_children():
            w.destroy()
        self.split_data.clear()
        self.rename_entries.clear()

        reader = PdfReader(self.full_pdf_path)
        total_pages = len(reader.pages)

        if self.split_option.get() == "Per Halaman":
            for i in range(total_pages):
                self.split_data.append([i])
        else:
            pages_list = self.parse_ranges(self.range_var.get(), total_pages)
            if pages_list is None:
                return
            self.split_data = pages_list

        base_name = os.path.splitext(os.path.basename(self.full_pdf_path))[0]

        for idx, chunk in enumerate(self.split_data):
            default_name = f"{base_name}_{idx+1}.pdf"
            label_text = f"File #{idx+1}: Halaman {self.chunk_to_str(chunk)}"
            ctk.CTkLabel(self.rename_frame, text=label_text, fg_color="#3c3c3c").pack(pady=(10,2), anchor="w")

            var = ctk.StringVar(value=default_name)
            ent = ctk.CTkEntry(self.rename_frame, textvariable=var, width=250)
            ent.pack(pady=(0,5), anchor="w")

            self.rename_entries.append(var)

        messagebox.showinfo("Info", "Silakan rename jika perlu, lalu klik 'Split PDF'.")

    def parse_ranges(self, range_str, total_pages):
        chunks = []
        parts = range_str.split(',')
        for part in parts:
            try:
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    if start < 1 or end > total_pages or start > end:
                        raise ValueError
                    idxs = list(range(start-1, end))
                else:
                    val = int(part)
                    if val < 1 or val > total_pages:
                        raise ValueError
                    idxs = [val-1]
                chunks.append(idxs)
            except:
                messagebox.showerror("Error", f"Range tidak valid: {part}")
                return None
        return chunks

    def chunk_to_str(self, chunk):
        if len(chunk) == 1:
            return str(chunk[0]+1)
        else:
            return f"{chunk[0]+1}-{chunk[-1]+1}"

    def split_pdf(self):
        """Split logic dengan ZIP opsional.
           Jika zip dicentang → file PDF di-zip lalu dihapus.
           Jika tidak → file PDF saja, tanpa zip."""
        if not self.full_pdf_path:
            messagebox.showerror("Error", "Pilih file PDF terlebih dahulu!")
            return
        if not self.output_folder.get():
            messagebox.showerror("Error", "Pilih folder output terlebih dahulu!")
            return
        if not self.split_data or not self.rename_entries:
            messagebox.showerror("Error", "Klik 'Generate Splits' dulu.")
            return

        reader = PdfReader(self.full_pdf_path)
        output_files = []

        # 1. Loop buat file PDF split
        for idx, chunk in enumerate(self.split_data):
            out_name = self.rename_entries[idx].get().strip()
            if not out_name.lower().endswith(".pdf"):
                out_name += ".pdf"

            writer = PdfWriter()
            for p in chunk:
                writer.add_page(reader.pages[p])

            save_path = os.path.join(self.output_folder.get(), out_name)
            with open(save_path, "wb") as f:
                writer.write(f)
            output_files.append(save_path)

        # 2. Jika save_as_zip → buat zip, hapus file PDF splitted
        if self.save_as_zip.get():
            base_name = os.path.splitext(os.path.basename(self.full_pdf_path))[0]
            zip_name = f"{base_name}.zip"
            zip_path = os.path.join(self.output_folder.get(), zip_name)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for fpath in output_files:
                    zipf.write(fpath, arcname=os.path.basename(fpath))

            # Hapus file PDF splitted
            for fpath in output_files:
                if os.path.exists(fpath):
                    os.remove(fpath)

        messagebox.showinfo("Sukses", "PDF berhasil di-split!")


# =======================================
# 3) FORMATTED SPLIT PAGE
# =======================================
class FormattedSplitPage(ctk.CTkFrame):
    """
    Terdapat 7 label:
    Kuitansi, Invoice, SPB, Faktur Pajak, BA REKON, NPK, BASO
    Masing-masing user isi range, default nama file = <label>_<nama_pdf>.pdf
    """
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="#2c2c2c")
        self.controller = controller

        self.pdf_doc = None
        self.current_page = 0
        self.page_count = 0
        self.zoom_factor = 1.0
        self.min_zoom = 0.4
        self.max_zoom = 3.0

        self.pdf_path = ctk.StringVar()
        self.output_folder = ctk.StringVar()
        self.save_as_zip = ctk.BooleanVar(value=False)

        # Dokumen2
        self.docs = ["Kuitansi", "Invoice", "SPB", "Faktur Pajak", "BA REKON", "NPK", "BASO"]
        self.range_vars = {}      # { "Kuitansi": ctk.StringVar, ... }
        self.rename_vars = {}     # { "Kuitansi": ctk.StringVar, ... }

        # Tombol BACK di kiri atas
        back_button = ctk.CTkButton(self, text="← Back", width=70, command=lambda: controller.show_page("WelcomePage"))
        back_button.pack(anchor="nw", padx=10, pady=10)

        ctk.CTkLabel(self, text="Formatted Split", font=("Arial", 20, "bold")).pack(pady=5)

        main_frame = ctk.CTkFrame(self, fg_color="#333333")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Left
        left_option = ctk.CTkFrame(main_frame, fg_color="#2c2c2c")
        left_option.pack(side="left", fill="y", padx=10, pady=10)

        ctk.CTkLabel(left_option, text="Pilih PDF:", font=("Arial", 14)).pack(pady=(10,0), anchor="w")
        ctk.CTkEntry(left_option, textvariable=self.pdf_path, width=300, state="readonly").pack(pady=5, anchor="w")
        ctk.CTkButton(left_option, text="Browse PDF", command=self.browse_pdf).pack(pady=(0,10), anchor="w")

        ctk.CTkLabel(left_option, text="Folder Output:", font=("Arial", 14)).pack(pady=(0,0), anchor="w")
        ctk.CTkEntry(left_option, textvariable=self.output_folder, width=300, state="readonly").pack(pady=5, anchor="w")
        ctk.CTkButton(left_option, text="Browse Folder", command=self.browse_folder).pack(pady=(0,10), anchor="w")

        # Frame dokumen
        doc_frame = ctk.CTkScrollableFrame(left_option, fg_color="#3c3c3c", width=300, height=300)
        doc_frame.pack(pady=10, fill="x")

        for doc in self.docs:
            ctk.CTkLabel(doc_frame, text=doc, fg_color="#3c3c3c").pack(pady=(10,2), anchor="w")
            range_var = ctk.StringVar()
            rename_var = ctk.StringVar()

            range_ent = ctk.CTkEntry(doc_frame, textvariable=range_var, placeholder_text="Range Halaman?", width=250)
            range_ent.pack(pady=(0,2), anchor="w")

            rename_ent = ctk.CTkEntry(doc_frame, textvariable=rename_var, width=250)
            rename_ent.pack(pady=(0,5), anchor="w")

            self.range_vars[doc] = range_var
            self.rename_vars[doc] = rename_var

        ctk.CTkCheckBox(left_option, text="Save as ZIP?", variable=self.save_as_zip).pack(pady=10, anchor="w")

        ctk.CTkButton(left_option, text="Split PDF", fg_color="#28A745", command=self.split_pdf).pack(pady=10)

        # Right (Preview)
        right_preview = ctk.CTkFrame(main_frame, fg_color="#2c2c2c")
        right_preview.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(right_preview, bg="black", width=600, height=600)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.start_x = 0
        self.start_y = 0
        self.pan_x = 0
        self.pan_y = 0

        nav_frame = ctk.CTkFrame(right_preview, fg_color="#2c2c2c")
        nav_frame.pack(pady=5, fill="x")

        ctk.CTkButton(nav_frame, text="◀ Prev Page", command=self.prev_page).pack(side="left", padx=5)

        self.page_label = ctk.CTkLabel(nav_frame, text="0/0", font=("Arial", 14))
        self.page_label.pack(side="left", padx=5)

        ctk.CTkButton(nav_frame, text="Next Page ▶", command=self.next_page).pack(side="left", padx=5)
        ctk.CTkButton(nav_frame, text="Zoom -", command=self.zoom_out).pack(side="right", padx=5)
        ctk.CTkButton(nav_frame, text="Zoom +", command=self.zoom_in).pack(side="right", padx=5)

    # ========== BROWSE & PREVIEW ==========
    def browse_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF Files","*.pdf")])
        if path:
            self.pdf_path.set(os.path.basename(path))
            self.load_pdf(path)

            base_name = os.path.splitext(os.path.basename(path))[0]
            for doc in self.docs:
                self.rename_vars[doc].set(f"{doc}_{base_name}.pdf")

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder.set(folder)

    def load_pdf(self, pdf_path):
        self.pdf_doc = fitz.open(pdf_path)
        self.page_count = len(self.pdf_doc)
        self.current_page = 0
        self.zoom_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.update_preview()

    # ========== ZOOM & PAN ==========
    def zoom_in(self):
        if self.zoom_factor < self.max_zoom:
            self.zoom_factor += 0.2
            self.update_preview()

    def zoom_out(self):
        if self.zoom_factor > self.min_zoom:
            self.zoom_factor -= 0.2
            self.update_preview()

    def start_pan(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def do_pan(self, event):
        dx = event.x - self.start_x
        dy = event.y - self.start_y
        self.start_x = event.x
        self.start_y = event.y
        self.canvas.move(self.canvas_img, dx, dy)
        self.pan_x += dx
        self.pan_y += dy

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.pan_x = 0
            self.pan_y = 0
            self.update_preview()

    def next_page(self):
        if self.current_page < self.page_count - 1:
            self.current_page += 1
            self.pan_x = 0
            self.pan_y = 0
            self.update_preview()

    def update_preview(self):
        if not self.pdf_doc:
            return
        page = self.pdf_doc[self.current_page]
        mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        self.tk_img = ImageTk.PhotoImage(img)
        self.canvas.delete("all")
        self.canvas_img = self.canvas.create_image(self.pan_x, self.pan_y, image=self.tk_img, anchor="nw")

        self.page_label.configure(text=f"{self.current_page+1}/{self.page_count}")

    # ========== SPLIT LOGIC ==========
    def split_pdf(self):
        """Split logic dengan ZIP opsional.
           Jika zip dicentang → file PDF di-zip lalu dihapus.
           Jika tidak → file PDF saja, tanpa zip."""
        if not self.pdf_doc:
            messagebox.showerror("Error","Pilih file PDF terlebih dahulu!")
            return
        if not self.output_folder.get():
            messagebox.showerror("Error","Pilih folder output terlebih dahulu!")
            return

        reader = PdfReader(self.pdf_doc.name)
        output_files = []

        # 1. Loop buat file PDF split
        for doc in self.docs:
            rangetext = self.range_vars[doc].get().strip()
            out_name = self.rename_vars[doc].get().strip()
            if not out_name.lower().endswith(".pdf"):
                out_name += ".pdf"

            if not rangetext:
                # Jika user kosongkan range => skip
                continue

            pages = self.parse_ranges(rangetext, len(reader.pages))
            if pages is None:
                return

            writer = PdfWriter()
            for p in pages:
                writer.add_page(reader.pages[p])

            save_path = os.path.join(self.output_folder.get(), out_name)
            with open(save_path, "wb") as f:
                writer.write(f)
            output_files.append(save_path)

        # Tambahkan file PDF asli ke dalam output_files
        original_pdf = self.pdf_path.get()
        output_files.append(original_pdf)

        # 2. Jika save_as_zip → buat zip, hapus file PDF splitted
        if self.save_as_zip.get() and output_files:
            base_name = os.path.splitext(self.pdf_path.get())[0]  # "kalender" dsb
            zip_name = f"{base_name}.zip"
            zip_path = os.path.join(self.output_folder.get(), zip_name)

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                for fpath in output_files:
                    zipf.write(fpath, arcname=os.path.basename(fpath))

            # Hapus file PDF splitted
            for fpath in output_files:
                if fpath != original_pdf and os.path.exists(fpath):
                    try:
                        os.remove(fpath)
                    except PermissionError:
                        messagebox.showwarning("Peringatan", f"Gagal menghapus {os.path.basename(fpath)} karena sedang digunakan.")

        messagebox.showinfo("Sukses", "Formatted Split Berhasil!")

    def parse_ranges(self, range_str, total):
        chunks = []
        parts = range_str.split(',')
        for part in parts:
            try:
                if '-' in part:
                    s,e = map(int, part.split('-'))
                    if s<1 or e>total or s>e:
                        raise ValueError
                    idxs = list(range(s-1,e))
                else:
                    val = int(part)
                    if val<1 or val>total:
                        raise ValueError
                    idxs = [val-1]
                chunks.extend(idxs)
            except:
                messagebox.showerror("Error", f"Range tidak valid: {part}")
                return None
        return sorted(chunks)


if __name__ == "__main__":
    app = PDFSplitterApp()
    app.mainloop()
