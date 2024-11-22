# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

from PIL.Image import Resampling

from imageproccesing import load_and_preprocess_image, calculate_similarity, visualize_differences
from report_generation import create_similarity_chart, create_excel_report, generate_text_report
from utils import CLARINASE_PATH, CLARITINE_PATH, REFERENCE_CLARINASE, REFERENCE_CLARITINE, OUTPUT_DIR, \
    SIMILARITY_THRESHOLD
import os
from PIL import Image, ImageTk # Обновленный импорт
import threading


class ImageComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Сравнение изображений упаковок")
        self.root.geometry("1200x800")

        
        self.selected_folder = tk.StringVar(value="Clarinase 14 repetabs")
        self.image_path = None
        self.image_name = tk.StringVar()
        self.save_path = None

       
        self.create_widgets()

    def create_widgets(self):
        
        load_frame = ttk.LabelFrame(self.root, text="Загрузка изображения")
        load_frame.pack(fill="x", padx=10, pady=10)

        
        load_button = ttk.Button(load_frame, text="Загрузить изображение", command=self.load_image)
        load_button.pack(side="left", padx=5, pady=5)

        
        name_label = ttk.Label(load_frame, text="Название:")
        name_label.pack(side="left", padx=5)
        name_entry = ttk.Entry(load_frame, textvariable=self.image_name)
        name_entry.pack(side="left", padx=5)

        
        folder_label = ttk.Label(load_frame, text="Папка:")
        folder_label.pack(side="left", padx=5)
        folder_option = ttk.OptionMenu(load_frame, self.selected_folder, "Clarinase 14 repetabs",
                                       "Clarinase 14 repetabs", "Claritine 20 tablets")
        folder_option.pack(side="left", padx=5)
        
        save_button = ttk.Button(load_frame, text="Сохранить", command=self.save_image)
        save_button.pack(side="left", padx=5, pady=5)

        separator = ttk.Separator(self.root, orient='horizontal')
        separator.pack(fill='x', padx=10, pady=10)

        compare_button = ttk.Button(self.root, text="Начать процесс сравнения изображений",
                                    command=self.start_comparison_thread)
        compare_button.pack(pady=10)

        self.progress = ttk.Progressbar(self.root, orient='horizontal', length=400, mode='determinate')
        self.progress.pack(pady=10)

        self.create_scrollable_result_frame()

        footer = ttk.Label(self.root, text="Выполнено как тестовое задание для компании Biocad, Автор: Корнилов Денис Андреевич", font=("Arial", 10))
        footer.pack(side="bottom", pady=10)

    def create_scrollable_result_frame(self):
        """Создание прокручиваемой области для отображения результатов."""
        # Фрейм, содержащий Canvas и Scrollbar
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.canvas = tk.Canvas(container, borderwidth=0, background="#f0f0f0")
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.result_frame = tk.Frame(self.canvas, background="#f0f0f0")

        self.canvas.create_window((0, 0), window=self.result_frame, anchor="nw")
    
        self.result_frame.bind("<Configure>", self.on_frame_configure)

        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)

    def on_frame_configure(self, event):
        """Обновление области прокрутки Canvas."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_mousewheel(self, event):
        """Прокрутка Canvas с помощью колесика мыши."""
        # Для Windows и MacOS
        if os.name == 'nt':
            delta = int(-1 * (event.delta / 120))
        else:
            delta = int(-1 * (event.delta))
        self.canvas.yview_scroll(delta, "units")

    def load_image(self):
        filetypes = [("Image files", "*.png *.jpg *.jpeg")]
        filepath = filedialog.askopenfilename(title="Выберите изображение", filetypes=filetypes)
        if filepath:
            self.image_path = Path(filepath)
            self.image_name.set(self.image_path.stem)
            messagebox.showinfo("Успех", f"Изображение {self.image_path.name} загружено.")

    def save_image(self):
        if not self.image_path:
            messagebox.showerror("Ошибка", "Сначала загрузите изображение.")
            return
        name = self.image_name.get()
        if not name:
            messagebox.showerror("Ошибка", "Введите название изображения.")
            return
        selected_folder = self.selected_folder.get()
        destination_folder = CLARINASE_PATH if selected_folder == "Clarinase 14 repetabs" else CLARITINE_PATH
        destination_path = destination_folder / f"{name}{self.image_path.suffix}"
        try:
            os.makedirs(destination_folder, exist_ok=True)
            with open(self.image_path, 'rb') as src, open(destination_path, 'wb') as dst:
                dst.write(src.read())
            messagebox.showinfo("Успех", f"Изображение сохранено в {destination_folder}.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить изображение: {e}")

    def start_comparison_thread(self):
        # Запуск процесса сравнения в отдельном потоке
        thread = threading.Thread(target=self.compare_images)
        thread.start()

    def compare_images(self):
        self.root.after(0, self.disable_widgets)

        # Очистка предыдущих результатов
        self.root.after(0, self.clear_results)

        # Загрузка референсных изображений
        reference_clarinase_path = CLARINASE_PATH / REFERENCE_CLARINASE
        reference_claritine_path = CLARITINE_PATH / REFERENCE_CLARITINE

        reference_clarinase = load_and_preprocess_image(reference_clarinase_path)
        reference_claritine = load_and_preprocess_image(reference_claritine_path)

        if reference_clarinase is None or reference_claritine is None:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", "Не удалось загрузить референсные изображения."))
            self.root.after(0, self.enable_widgets)
            return

        # Сбор всех изображений
        all_images = {}
        total_images = 0
        for folder, folder_path, reference_image in [
            ("Clarinase 14 repetabs", CLARINASE_PATH, reference_clarinase),
            ("Claritine 20 tablets", CLARITINE_PATH, reference_claritine)
        ]:
            images = []
            for filename in os.listdir(folder_path):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = folder_path / filename
                    img = load_and_preprocess_image(img_path)
                    if img is not None:
                        images.append((filename, img))
            all_images[folder] = images
            total_images += len(images) - 1  # Исключаем референсные изображения

        # Инициализация прогресс-бара
        self.root.after(0, self.set_progress_max, total_images)
        self.root.after(0, self.set_progress_value, 0)

        # Определение степени схожести и выделение различий
        results = {}
        charts_paths = {}
        low_similarity_images = {}  # Для хранения путей к изображениям с низкой схожестью
        for folder, images in all_images.items():
            results[folder] = []
            low_similarity_images[folder] = []
            for filename, img in images:
                # Пропуск референсных изображений
                if (folder == "Clarinase 14 repetabs" and filename == REFERENCE_CLARINASE) or \
                        (folder == "Claritine 20 tablets" and filename == REFERENCE_CLARITINE):
                    continue
                reference_image = reference_clarinase if folder == "Clarinase 14 repetabs" else reference_claritine
                similarity_score, diff = calculate_similarity(reference_image, img)
                results[folder].append((filename, similarity_score))

                # Визуализация различий (только для изображений с низкой схожестью)
                if similarity_score < SIMILARITY_THRESHOLD:
                    output_diff_path = OUTPUT_DIR / f"diff_{folder}_{filename.replace(' ', '_').split('.')[0]}.png"
                    visualize_differences(reference_image, img, diff, output_diff_path)
                    low_similarity_images[folder].append(output_diff_path)

                # Обновление прогресс-бара
                self.root.after(0, self.update_progress, 1)

            
            charts_paths[folder] = create_similarity_chart(folder, results[folder], OUTPUT_DIR)

        
        excel_report_path = create_excel_report(results, OUTPUT_DIR)

        
        generate_text_report(results, OUTPUT_DIR, excel_report_path, charts_paths)

        
        self.root.after(0, self.display_results, results, charts_paths, low_similarity_images)

        
        self.root.after(0, self.add_report_buttons)

        
        self.root.after(0, self.enable_widgets)

        # Сообщение об окончании процесса
        self.root.after(0, lambda: messagebox.showinfo("Готово",
                                                       "Процесс сравнения завершен. Результаты сохранены в папке 'results'."))

    def set_progress_max(self, maximum):
        self.progress['maximum'] = maximum

    def set_progress_value(self, value):
        self.progress['value'] = value

    def update_progress(self, increment=1):
        """Обновление прогресс-бара."""
        self.progress['value'] += increment
        self.root.update_idletasks()

    def disable_widgets(self):
        """Отключение виджетов во время обработки."""
        self.disable_widget_recursive(self.root)

    def disable_widget_recursive(self, widget):
        """Рекурсивное отключение виджетов, поддерживающих 'state'."""
        try:
            widget.configure(state='disabled')
        except tk.TclError:
            pass  # Игнорируем виджеты без опции 'state'
        for child in widget.winfo_children():
            self.disable_widget_recursive(child)

    def enable_widgets(self):
        """Включение виджетов после обработки."""
        self.enable_widget_recursive(self.root)

    def enable_widget_recursive(self, widget):
        """Рекурсивное включение виджетов, поддерживающих 'state'."""
        try:
            widget.configure(state='normal')
        except tk.TclError:
            pass  # Игнорируем виджеты без опции 'state'
        for child in widget.winfo_children():
            self.enable_widget_recursive(child)

    def clear_results(self):
        """Очистка области результатов."""
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def display_results(self, results, charts_paths, low_similarity_images):
        """Отображение результатов сравнения в GUI."""
        for folder, folder_results in results.items():
            folder_label = ttk.Label(self.result_frame, text=f"Результаты для папки: {folder}",
                                     font=("Arial", 12, "bold"))
            folder_label.pack(anchor="w", pady=(10, 0))

            # Таблица результатов
            tree = ttk.Treeview(self.result_frame, columns=("Filename", "Similarity"), show='headings', height=5)
            tree.heading("Filename", text="Имя файла")
            tree.heading("Similarity", text="Схожесть (%)")
            tree.column("Filename", width=300)
            tree.column("Similarity", width=100, anchor='center')
            for filename, score in folder_results:
                tree.insert("", "end", values=(filename, f"{score:.2f}%"))
            tree.pack(fill="x", pady=5)

            # Отображение графика
            chart_path = charts_paths.get(folder)
            if chart_path and chart_path.exists():
                img = Image.open(chart_path)
                img = img.resize((600, 300), Resampling.LANCZOS)  # Используем Resampling.LANCZOS
                photo = ImageTk.PhotoImage(img)
                chart_label = ttk.Label(self.result_frame, image=photo)
                chart_label.image = photo
                chart_label.pack(pady=5)

            # Отображение изображений с низкой схожестью
            if low_similarity_images.get(folder):
                for diff_image_path in low_similarity_images[folder]:
                    if diff_image_path.exists():
                        filename = diff_image_path.stem.split('_')[-1]
                        ttk.Label(self.result_frame,
                                  text=f"Различия для {filename} (Схожесть: менее {SIMILARITY_THRESHOLD}%)").pack()
                        img_diff = Image.open(diff_image_path)
                        img_diff = img_diff.resize((600, 300), Resampling.LANCZOS)  # Используем Resampling.LANCZOS
                        photo_diff = ImageTk.PhotoImage(img_diff)
                        diff_label = ttk.Label(self.result_frame, image=photo_diff)
                        diff_label.image = photo_diff
                        diff_label.pack(pady=5)

    def add_report_buttons(self):
        """Добавление кнопок для открытия отчетов."""
        button_frame = ttk.Frame(self.result_frame)
        button_frame.pack(pady=10)

        # Кнопка открытия Excel отчета
        excel_button = ttk.Button(button_frame, text="Открыть Excel отчет", command=self.open_excel_report)
        excel_button.pack(side="left", padx=10)

        # Кнопка открытия текстового отчета
        text_button = ttk.Button(button_frame, text="Открыть текстовый отчет", command=self.open_text_report)
        text_button.pack(side="left", padx=10)

    def open_excel_report(self):
        """Открытие Excel отчета."""
        excel_path = OUTPUT_DIR / "similarity_report.xlsx"
        if excel_path.exists():
            os.startfile(str(excel_path))
        else:
            messagebox.showerror("Ошибка", "Excel отчет не найден.")

    def open_text_report(self):
        """Открытие текстового отчета."""
        text_path = OUTPUT_DIR / "report.txt"
        if text_path.exists():
            os.startfile(str(text_path))
        else:
            messagebox.showerror("Ошибка", "Текстовый отчет не найден.")
