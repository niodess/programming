pip install Pillow
python image_filter_pro_v5.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, simpledialog
from PIL import Image, ImageTk, ImageFilter, ImageEnhance, ImageOps, ImageDraw, ImageFont
import os
import glob
from datetime import datetime

def set_dark_theme(root):
    style = ttk.Style(root)
    style.theme_use('clam')
    bg = "#1e1e1e"
    fg = "#ffffff"
    accent = "#4a9eff"
    frame_bg = "#252526"

    root.configure(bg=bg)
    style.configure("TFrame", background=bg)
    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TLabelframe", background=frame_bg)
    style.configure("TLabelframe.Label", background=frame_bg, foreground=accent, font=("Segoe UI", 10, "bold"))
    style.configure("TButton", background="#3c3c3c", foreground=fg, padding=6)
    style.map("TButton", background=[("active", accent)])


class ImageFilterProV5:
    def __init__(self, root):
        self.root = root
        self.root.title("🖼️ ImageFilter Pro v5 — Ultimate РИЗ-330045д")
        self.root.geometry("1280x800")

        set_dark_theme(root)

        # === Переменные ===
        self.original_image = None
        self.current_image = None
        self.history = []
        self.photo_image = None

        # Рисование
        self.drawing_mode = False
        self.draw_layer = None
        self.draw_draw = None
        self.brush_color = "#FFFFFF"
        self.brush_size = 10
        self.last_x = self.last_y = None

        self.setup_ui()
        self.create_menu()
        self.bind_hotkeys()

    def setup_ui(self):
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === ПРЕВЬЮ ===
        left = ttk.LabelFrame(main, text="🖼️ Превью")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(left, bg="#1a1a1a", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.draw_brush)
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, 'last_x', None) or setattr(self, 'last_y', None))

        # === ПРАВАЯ ПАНЕЛЬ ===
        right = ttk.Frame(main, width=370)
        right.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))

        # Фильтры
        f1 = ttk.LabelFrame(right, text="⚡ Быстрые фильтры")
        f1.pack(fill=tk.X, pady=5)
        for name, cmd in [("Ч/Б", self.apply_grayscale), ("Сепия", self.apply_sepia),
                          ("Негатив", self.apply_negative), ("Размытие", self.apply_blur),
                          ("Резкость", self.apply_sharpen)]:
            ttk.Button(f1, text=name, command=cmd).pack(fill=tk.X, pady=2)

        # Слайдеры
        f2 = ttk.LabelFrame(right, text="🎚️ Регулировки")
        f2.pack(fill=tk.X, pady=5)
        self.brightness_var = tk.DoubleVar(value=1.0)
        self.contrast_var = tk.DoubleVar(value=1.0)
        self.saturation_var = tk.DoubleVar(value=1.0)
        self.sharpness_var = tk.DoubleVar(value=1.0)
        for lbl, var in [("Яркость", self.brightness_var), ("Контраст", self.contrast_var),
                         ("Насыщенность", self.saturation_var), ("Резкость", self.sharpness_var)]:
            self.create_slider(f2, lbl, var)
        ttk.Button(f2, text="✓ Применить регулировки", command=self.apply_adjustments).pack(fill=tk.X, pady=5)

        # Трансформации
        f3 = ttk.LabelFrame(right, text="🔄 Трансформации")
        f3.pack(fill=tk.X, pady=5)
        ttk.Button(f3, text="⟲ Повернуть влево", command=lambda: self.rotate(-90)).pack(fill=tk.X, pady=2)
        ttk.Button(f3, text="⟳ Повернуть вправо", command=lambda: self.rotate(90)).pack(fill=tk.X, pady=2)
        ttk.Button(f3, text="↔ Отразить горизонтально", command=self.flip_horizontal).pack(fill=tk.X, pady=2)
        ttk.Button(f3, text="↕ Отразить вертикально", command=self.flip_vertical).pack(fill=tk.X, pady=2)
        ttk.Button(f3, text="Изменить размер...", command=self.resize_image).pack(fill=tk.X, pady=2)

        # Инструменты (Рисование + Текст)
        f4 = ttk.LabelFrame(right, text="🛠️ Инструменты")
        f4.pack(fill=tk.X, pady=5)
        ttk.Button(f4, text="✏️ Включить/выключить рисование", command=self.toggle_drawing_mode).pack(fill=tk.X, pady=2)
        ttk.Button(f4, text="🎨 Цвет кисти", command=self.choose_brush_color).pack(fill=tk.X, pady=2)
        ttk.Button(f4, text="🔠 Добавить текст на фото", command=self.add_text_on_image).pack(fill=tk.X, pady=2)
        ttk.Button(f4, text="Добавить водяной знак", command=self.add_watermark).pack(fill=tk.X, pady=2)
        ttk.Button(f4, text="Авто-улучшение", command=self.auto_enhance).pack(fill=tk.X, pady=2)
        ttk.Button(f4, text="Сравнить до/после", command=self.compare_before_after).pack(fill=tk.X, pady=2)

        # Управление
        f5 = ttk.Frame(right)
        f5.pack(fill=tk.X, pady=8)
        ttk.Button(f5, text="↩ Отменить (Ctrl+Z)", command=self.undo).pack(fill=tk.X, pady=2)
        ttk.Button(f5, text="🔄 Сбросить к оригиналу", command=self.reset_to_original).pack(fill=tk.X, pady=2)
        ttk.Button(f5, text="📁 Пакетная обработка", command=self.batch_process).pack(fill=tk.X, pady=2)
        ttk.Button(f5, text="💾 Сохранить фото (Ctrl+S)", command=self.save_photo).pack(fill=tk.X, pady=2)

        # Статус
        self.status_var = tk.StringVar(value="Откройте изображение")
        ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

    def create_slider(self, parent, label, var):
        f = ttk.Frame(parent)
        f.pack(fill=tk.X, pady=3)
        ttk.Label(f, text=label).pack(anchor=tk.W)
        ttk.Scale(f, from_=0, to=3, variable=var, orient=tk.HORIZONTAL).pack(fill=tk.X)

    def create_menu(self):
        menubar = tk.Menu(self.root)
        fm = tk.Menu(menubar, tearoff=0)
        fm.add_command(label="Открыть изображение (Ctrl+O)", command=self.open_image)
        fm.add_command(label="Сохранить фото (Ctrl+S)", command=self.save_photo)
        fm.add_command(label="Создать коллаж", command=self.create_collage)
        fm.add_separator()
        fm.add_command(label="Выход", command=self.root.quit)
        menubar.add_cascade(label="Файл", menu=fm)

        tm = tk.Menu(menubar, tearoff=0)
        tm.add_command(label="Пакетная обработка", command=self.batch_process)
        tm.add_command(label="Сравнить до/после", command=self.compare_before_after)
        menubar.add_cascade(label="Инструменты", menu=tm)
        self.root.config(menu=menubar)

    def bind_hotkeys(self):
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_photo())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Escape>", lambda e: self.toggle_drawing_mode() if self.drawing_mode else None)

    # ==================== РЕЖИМ РИСОВАНИЯ + ТЕКСТ ====================

    def toggle_drawing_mode(self):
        if self.current_image is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение")
            return
        self.drawing_mode = not self.drawing_mode

        if self.drawing_mode:
            self.draw_layer = Image.new("RGBA", self.current_image.size, (0, 0, 0, 0))
            self.draw_draw = ImageDraw.Draw(self.draw_layer)
            self.status_var.set("✏️ РЕЖИМ РИСОВАНИЯ ВКЛЮЧЁН — рисуй мышью | Esc — выход")
        else:
            self.apply_drawing_layer()
            self.status_var.set("Режим рисования выключен")

    def choose_brush_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.brush_color = color

    def on_canvas_click(self, event):
        """Обрабатывает клик — либо начало рисования, либо размещение текста"""
        if self.drawing_mode and self.draw_draw:
            self.last_x, self.last_y = event.x, event.y

    def draw_brush(self, event):
        if not self.drawing_mode or self.draw_draw is None or self.last_x is None:
            return

        # Масштабирование координат
        if self.current_image is None: return
        scale_x = self.current_image.width / self.canvas.winfo_width()
        scale_y = self.current_image.height / self.canvas.winfo_height()

        x1 = int(self.last_x * scale_x)
        y1 = int(self.last_y * scale_y)
        x2 = int(event.x * scale_x)
        y2 = int(event.y * scale_y)

        self.draw_draw.line([(x1, y1), (x2, y2)], fill=self.brush_color, width=self.brush_size)
        self.last_x, self.last_y = event.x, event.y
        self.update_preview()

    def apply_drawing_layer(self):
        if self.draw_layer and self.current_image:
            self.add_to_history()
            base = self.current_image.convert("RGBA")
            self.current_image = Image.alpha_composite(base, self.draw_layer).convert("RGB")
            self.draw_layer = None
            self.draw_draw = None
            self.update_preview()

    def add_text_on_image(self):
        """Добавляет текст прямо на изображение (в режиме рисования или обычном)"""
        if self.current_image is None:
            messagebox.showwarning("Внимание", "Сначала откройте изображение")
            return

        text = simpledialog.askstring("Текст на фото", "Введите текст:")
        if not text:
            return

        # Если включён режим рисования — пишем на draw_layer
        if self.drawing_mode and self.draw_draw:
            self.draw_draw.text((50, 50), text, fill=self.brush_color)
            self.update_preview()
            messagebox.showinfo("Готово", "Текст добавлен на слой рисования")
        else:
            # Обычный режим — сразу на изображение
            self.add_to_history()
            img = self.current_image.convert("RGB")
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 40)
            except:
                font = ImageFont.load_default()
            draw.text((50, 50), text, font=font, fill="white")
            self.current_image = img
            self.update_preview()

    # ==================== ОСНОВНЫЕ ФУНКЦИИ ====================

    def update_preview(self):
        if self.current_image is None:
            return

        cw = max(self.canvas.winfo_width(), 500)
        ch = max(self.canvas.winfo_height(), 500)
        disp = self.current_image.copy()

        if self.draw_layer:
            if disp.mode != "RGBA":
                disp = disp.convert("RGBA")
            disp = Image.alpha_composite(disp, self.draw_layer)

        disp.thumbnail((cw-10, ch-10), Image.LANCZOS)
        self.photo_image = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(cw//2, ch//2, image=self.photo_image, anchor=tk.CENTER)

        w, h = self.current_image.size
        self.status_var.set(f"{w}×{h} px  |  {'Рисование' if self.drawing_mode else self.current_image.mode}")

    def add_to_history(self):
        if self.current_image:
            self.history.append(self.current_image.copy())
            if len(self.history) > 10:
                self.history.pop(0)

    def undo(self):
        if self.history:
            self.current_image = self.history.pop()
            self.update_preview()
        else:
            messagebox.showinfo("Undo", "Нет действий для отмены")

    def open_image(self):
        path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp")])
        if not path: return
        try:
            self.original_image = Image.open(path).convert("RGB")
            self.current_image = self.original_image.copy()
            self.history.clear()
            self.update_preview()
            self.status_var.set(f"Открыт: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_photo(self):
        """Сохраняет обработанное фото"""
        if self.current_image is None:
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG (рекомендуется)", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp"), ("PDF", "*.pdf")]
        )
        if path:
            try:
                ext = os.path.splitext(path)[1].lower()
                if ext == ".pdf":
                    self.current_image.save(path, "PDF", resolution=100)
                else:
                    self.current_image.save(path, quality=95)
                messagebox.showinfo("Фото сохранено", f"Сохранено: {path}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def reset_to_original(self):
        if self.original_image:
            self.current_image = self.original_image.copy()
            self.history.clear()
            self.update_preview()

    # ==================== ФИЛЬТРЫ ====================

    def apply_filter(self, func, name):
        if self.current_image is None: return
        self.add_to_history()
        self.current_image = func(self.current_image)
        self.update_preview()

    def apply_grayscale(self):
        self.apply_filter(lambda img: img.convert("L"), "Ч/Б")

    def apply_sepia(self):
        def sepia(img):
            if img.mode != "RGB": img = img.convert("RGB")
            pixels = img.load()
            for y in range(img.height):
                for x in range(img.width):
                    r, g, b = pixels[x, y]
                    pixels[x, y] = (min(255, int(0.393*r + 0.769*g + 0.189*b)),
                                    min(255, int(0.349*r + 0.686*g + 0.168*b)),
                                    min(255, int(0.272*r + 0.534*g + 0.131*b)))
            return img
        self.apply_filter(sepia, "Сепия")

    def apply_negative(self):
        self.apply_filter(lambda img: ImageOps.invert(img.convert("RGB")), "Негатив")

    def apply_blur(self):
        self.apply_filter(lambda img: img.filter(ImageFilter.GaussianBlur(3)), "Размытие")

    def apply_sharpen(self):
        self.apply_filter(lambda img: img.filter(ImageFilter.SHARPEN), "Резкость")

    def apply_adjustments(self):
        if self.current_image is None: return
        self.add_to_history()
        img = self.current_image.convert("RGB")
        img = ImageEnhance.Brightness(img).enhance(self.brightness_var.get())
        img = ImageEnhance.Contrast(img).enhance(self.contrast_var.get())
        img = ImageEnhance.Color(img).enhance(self.saturation_var.get())
        img = ImageEnhance.Sharpness(img).enhance(self.sharpness_var.get())
        self.current_image = img
        self.update_preview()

    def rotate(self, angle):
        if self.current_image:
            self.add_to_history()
            self.current_image = self.current_image.rotate(angle, expand=True)
            self.update_preview()

    def flip_horizontal(self):
        if self.current_image:
            self.add_to_history()
            self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
            self.update_preview()

    def flip_vertical(self):
        if self.current_image:
            self.add_to_history()
            self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
            self.update_preview()

    def resize_image(self):
        if not self.current_image: return
        w = simpledialog.askinteger("Размер", "Ширина", initialvalue=self.current_image.width)
        h = simpledialog.askinteger("Размер", "Высота", initialvalue=self.current_image.height)
        if w and h:
            self.add_to_history()
            self.current_image = self.current_image.resize((w, h), Image.LANCZOS)
            self.update_preview()

    def add_watermark(self):
        if not self.current_image: return
        text = simpledialog.askstring("Водяной знак", "Текст:")
        if not text: return
        self.add_to_history()
        img = self.current_image.convert("RGB")
        draw = ImageDraw.Draw(img)
        try: font = ImageFont.truetype("arial.ttf", 36)
        except: font = ImageFont.load_default()
        x, y = img.width - 280, img.height - 70
        draw.text((x+2, y+2), text, font=font, fill="black")
        draw.text((x, y), text, font=font, fill="white")
        self.current_image = img
        self.update_preview()

    def auto_enhance(self):
        if not self.current_image: return
        self.add_to_history()
        img = self.current_image.convert("RGB")
        img = ImageEnhance.Contrast(img).enhance(1.2)
        img = ImageEnhance.Brightness(img).enhance(1.08)
        img = ImageEnhance.Color(img).enhance(1.12)
        img = ImageEnhance.Sharpness(img).enhance(1.3)
        self.current_image = img
        self.update_preview()

    # ==================== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ====================

    def compare_before_after(self):
        if self.original_image is None or self.current_image is None: return
        win = tk.Toplevel(self.root)
        win.title("До / После")
        win.geometry("1100x620")
        f = ttk.Frame(win)
        f.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for title, img in [("ДО (Оригинал)", self.original_image), ("ПОСЛЕ", self.current_image)]:
            lf = ttk.LabelFrame(f, text=title)
            lf.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
            c = tk.Canvas(lf, bg="#1a1a1a")
            c.pack(fill=tk.BOTH, expand=True)
            c.after(80, lambda c=c, im=img: self._show_on_canvas(c, im))

    def _show_on_canvas(self, canvas, img):
        cw = canvas.winfo_width() or 500
        ch = canvas.winfo_height() or 500
        tmp = img.copy()
        tmp.thumbnail((cw-10, ch-10), Image.LANCZOS)
        photo = ImageTk.PhotoImage(tmp)
        canvas.delete("all")
        canvas.create_image(cw//2, ch//2, image=photo, anchor=tk.CENTER)
        canvas.image = photo

    def batch_process(self):
        folder = filedialog.askdirectory()
        if not folder: return
        effect = simpledialog.askstring("Эффект", "1=Ч/Б  2=Сепия  3=Размытие  4=Резкость  5=Негатив  6=Авто-улучшение")
        if not effect: return

        out_folder = os.path.join(folder, "processed_" + datetime.now().strftime("%Y%m%d_%H%M"))
        os.makedirs(out_folder, exist_ok=True)

        files = []
        for ext in ("*.jpg", "*.png", "*.jpeg", "*.webp"):
            files.extend(glob.glob(os.path.join(folder, ext)))

        count = 0
        for path in files:
            try:
                img = Image.open(path)
                if effect == "1": img = img.convert("L")
                elif effect == "2": img = self._apply_sepia(img)
                elif effect == "3": img = img.filter(ImageFilter.GaussianBlur(3))
                elif effect == "4": img = img.filter(ImageFilter.SHARPEN)
                elif effect == "5": img = ImageOps.invert(img.convert("RGB"))
                elif effect == "6":
                    img = ImageEnhance.Contrast(img.convert("RGB")).enhance(1.2)
                    img = ImageEnhance.Color(img).enhance(1.1)
                img.save(os.path.join(out_folder, os.path.basename(path)), quality=90)
                count += 1
            except:
                continue
        messagebox.showinfo("Готово", f"Обработано {count} изображений\nСохранено в: {out_folder}")

    def _apply_sepia(self, img):
        if img.mode != "RGB": img = img.convert("RGB")
        pixels = img.load()
        for y in range(img.height):
            for x in range(img.width):
                r, g, b = pixels[x, y]
                pixels[x, y] = (min(255, int(0.393*r+0.769*g+0.189*b)),
                                min(255, int(0.349*r+0.686*g+0.168*b)),
                                min(255, int(0.272*r+0.534*g+0.131*b)))
        return img

    def create_collage(self):
        files = filedialog.askopenfilenames(title="Выберите 2–6 фото")
        if len(files) < 2: return
        imgs = []
        for f in files[:6]:
            try:
                im = Image.open(f).convert("RGB")
                im.thumbnail((400, 400))
                imgs.append(im)
            except: continue
        if not imgs: return

        cols = 2 if len(imgs) <= 4 else 3
        w, h = imgs[0].size
        collage = Image.new("RGB", (cols * w, ((len(imgs) + cols - 1) // cols) * h), (30, 30, 30))
        for i, im in enumerate(imgs):
            collage.paste(im, ((i % cols) * w, (i // cols) * h))

        path = filedialog.asksaveasfilename(defaultextension=".png")
        if path:
            collage.save(path)
            messagebox.showinfo("Коллаж создан", path)


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageFilterProV5(root)
    root.mainloop()