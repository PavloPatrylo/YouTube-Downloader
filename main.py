import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import urllib.request
import threading
from pathlib import Path

class YoutubeDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # Визначаємо базовий шлях
        if hasattr(sys, '_MEIPASS'):
            # Для виконуваного файлу (PyInstaller) - зберігаємо файли поруч з .exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Для розробки
            self.base_path = os.path.dirname(os.path.abspath(__file__))

        # Шляхи до ffmpeg та yt-dlp
        self.ffmpeg_path = os.path.join(self.base_path, "ffmpeg.exe")
        self.ytdlp_path = os.path.join(self.base_path, "yt-dlp.exe")

        self.output_path = "downloads"
        self.current_progress = 0
        self.is_downloading = False

        # Використовуємо сучасну тему ttk
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=10, font=("Helvetica", 10))
        style.configure("TLabel", font=("Helvetica", 10), background="#f0f0f0")
        style.configure("TEntry", padding=5)
        style.configure("TProgressbar", thickness=20, troughcolor="#e0e0e0", background="#4CAF50")

        # Основний контейнер
        self.main_frame = ttk.Frame(self.root, padding="20", style="Main.TFrame")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Налаштування стилю для фрейму
        style.configure("Main.TFrame", background="#f0f0f0")

        # Заголовок
        ttk.Label(
            self.main_frame, 
            text="YouTube Downloader", 
            font=("Helvetica", 16, "bold"), 
            foreground="#333333",
            background="#f0f0f0"
        ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Поле для введення URL
        ttk.Label(self.main_frame, text="URL відео:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(self.main_frame, width=50)
        self.url_entry.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.url_entry.focus_set()

        # Контекстне меню
        self.context_menu = tk.Menu(self.root, tearoff=0, font=("Helvetica", 9))
        self.context_menu.add_command(label="Вставити", command=self.paste_url)
        self.url_entry.bind("<Button-3>", self.show_context_menu)
        self.url_entry.bind("<Control-v>", lambda event: self.paste_url())

        # Вибір папки
        ttk.Label(self.main_frame, text="Папка для збереження:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.folder_label = ttk.Label(self.main_frame, text="За замовчуванням (downloads)", wraplength=300)
        self.folder_label.grid(row=4, column=0, sticky=tk.W, pady=5)
        self.select_folder_button = ttk.Button(self.main_frame, text="Вибрати папку", command=self.select_folder)
        self.select_folder_button.grid(row=4, column=1, sticky=tk.E, pady=5)

        # Вибір формату та біжучий рядок
        ttk.Label(self.main_frame, text="Формат файлу:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.format_var = tk.StringVar(value="mp4")
        formats = ["mp4", "mp3", "wav"]
        self.format_menu = ttk.OptionMenu(self.main_frame, self.format_var, formats[0], *formats)
        self.format_menu.grid(row=6, column=0, sticky=tk.W, pady=5)
        
        # Біжучий рядок навпроти меню форматів
        self.progress = ttk.Progressbar(self.main_frame, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=6, column=1, sticky=tk.E, pady=5)

        # Кнопка завантаження
        self.download_button = ttk.Button(
            self.main_frame, 
            text="Завантажити", 
            command=self.start_download_thread,
            style="Accent.TButton"
        )
        self.download_button.grid(row=7, column=0, columnspan=2, pady=20)
        style.configure("Accent.TButton", background="#4CAF50", foreground="white")

        # Статус
        self.status_label = ttk.Label(self.main_frame, text="Запуск...", foreground="#333333")
        self.status_label.grid(row=8, column=0, columnspan=2, pady=5)

        # Перевірка та оновлення yt-dlp при запуску
        self.root.after(100, self.check_and_update_ytdlp)

    def check_and_update_ytdlp(self):
        """Перевірка наявності та оновлення yt-dlp.exe"""
        self.status_label.config(text="Перевірка yt-dlp...")
        self.root.update()

        try:
            # Перевіряємо, чи існує yt-dlp.exe
            if not os.path.exists(self.ytdlp_path):
                self.status_label.config(text="Завантаження yt-dlp...")
                self.root.update()
                self.download_ytdlp()
            else:
                # Перевіряємо версію та оновлюємо
                self.status_label.config(text="Оновлення yt-dlp...")
                self.root.update()
                self.update_ytdlp()

            # Перевірка ffmpeg
            if not os.path.exists(self.ffmpeg_path):
                messagebox.showwarning(
                    "Увага", 
                    f"FFmpeg не знайдено!\n\nБудь ласка, завантажте ffmpeg.exe та покладіть його в папку:\n{self.base_path}"
                )
            
            self.status_label.config(text="Project by Pavlo Patrylo")
        except Exception as e:
            self.status_label.config(text="Помилка оновлення. Спробуємо працювати...")
            print(f"Помилка при оновленні: {e}")

    def download_ytdlp(self):
        """Завантаження yt-dlp.exe з GitHub"""
        url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
        try:
            urllib.request.urlretrieve(url, self.ytdlp_path)
            self.status_label.config(text="yt-dlp завантажено успішно!")
        except Exception as e:
            messagebox.showerror("Помилка", f"Не вдалося завантажити yt-dlp:\n{str(e)}")

    def update_ytdlp(self):
        """Оновлення yt-dlp до останньої версії"""
        try:
            # Використовуємо вбудовану команду оновлення yt-dlp
            result = subprocess.run(
                [self.ytdlp_path, "-U"],
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            if "Updated" in result.stdout or "Latest" in result.stdout:
                self.status_label.config(text="yt-dlp оновлено!")
        except Exception as e:
            print(f"Помилка оновлення: {e}")

    def show_context_menu(self, event):
        """Показати контекстне меню"""
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def paste_url(self):
        """Вставити URL із буфера обміну"""
        try:
            clipboard = self.root.clipboard_get()
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, clipboard)
        except tk.TclError:
            self.status_label.config(text="Помилка: Буфер обміну порожній")

    def select_folder(self):
        """Відкрити діалог вибору папки"""
        folder = filedialog.askdirectory(title="Вибрати папку для збереження")
        if folder:
            self.output_path = folder
            self.folder_label.config(text=folder)
        else:
            self.output_path = "downloads"
            self.folder_label.config(text="За замовчуванням (downloads)")

    def smooth_progress(self, target):
        """Плавне оновлення прогрес-бару"""
        if self.current_progress < target and self.is_downloading:
            self.current_progress += min(2, target - self.current_progress)
            self.progress['value'] = self.current_progress
            self.root.after(50, self.smooth_progress, target)

    def start_download_thread(self):
        """Запуск завантаження в окремому потоці"""
        if not self.is_downloading:
            thread = threading.Thread(target=self.start_download, daemon=True)
            thread.start()

    def start_download(self):
        """Запуск завантаження"""
        url = self.url_entry.get().strip()
        format_choice = self.format_var.get().lower()

        if not url:
            messagebox.showerror("Помилка", "Введіть URL відео!")
            return

        # Перевірка наявності yt-dlp
        if not os.path.exists(self.ytdlp_path):
            messagebox.showerror("Помилка", "yt-dlp не знайдено! Перезапустіть програму.")
            return

        # Перевірка наявності ffmpeg (для mp4/mp3/wav потрібен ffmpeg)
        if not os.path.exists(self.ffmpeg_path):
            messagebox.showerror(
                "Помилка", 
                f"FFmpeg не знайдено!\n\nЗавантажте ffmpeg.exe з:\nhttps://www.gyan.dev/ffmpeg/builds/\n\nТа покладіть у папку:\n{self.base_path}"
            )
            return

        self.is_downloading = True
        self.current_progress = 0
        self.progress['value'] = 0
        self.status_label.config(text="Починаємо завантаження...")
        self.download_button.config(state="disabled")

        try:
            if not os.path.exists(self.output_path):
                os.makedirs(self.output_path)

            # Формуємо команду для yt-dlp
            if format_choice == 'mp4':
                # ВИПРАВЛЕННЯ: Використовуємо формат, який гарантує звук
                cmd = [
                    self.ytdlp_path,
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
                    "--merge-output-format", "mp4",
                    "--ffmpeg-location", self.ffmpeg_path,
                    "-o", f"{self.output_path}/%(title)s.%(ext)s",
                    url
                ]
            elif format_choice in ['mp3', 'wav']:
                cmd = [
                    self.ytdlp_path,
                    "-f", "bestaudio/best",
                    "--extract-audio",
                    "--audio-format", format_choice,
                    "--audio-quality", "192K",
                    "--ffmpeg-location", self.ffmpeg_path,
                    "-o", f"{self.output_path}/%(title)s.%(ext)s",
                    url
                ]
            else:
                messagebox.showerror("Помилка", "Невідомий формат!")
                self.download_button.config(state="normal")
                self.is_downloading = False
                return

            # Запускаємо процес завантаження
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            # Читаємо вивід для відображення прогресу
            for line in process.stdout:
                if "[download]" in line and "%" in line:
                    try:
                        # Витягуємо відсоток із рядка типу "[download]  45.2% of 10.5MiB"
                        percent_str = line.split("%")[0].split()[-1]
                        percentage = float(percent_str)
                        self.status_label.config(text=f"Завантаження: {percentage:.1f}%")
                        self.smooth_progress(percentage)
                        self.root.update()
                    except (ValueError, IndexError):
                        pass

            process.wait()

            if process.returncode == 0:
                self.current_progress = 100
                self.progress['value'] = 100
                self.status_label.config(text="Завантаження завершено!")
                messagebox.showinfo("Успіх", f"Файл збережено в:\n{os.path.abspath(self.output_path)}")
            else:
                raise Exception("Помилка під час завантаження")

        except Exception as e:
            messagebox.showerror("Помилка", f"Сталася помилка:\n{str(e)}")
            self.status_label.config(text="Помилка під час завантаження")
        finally:
            self.is_downloading = False
            self.download_button.config(state="normal")


if __name__ == "__main__":
    root = tk.Tk()
    app = YoutubeDownloaderApp(root)
    root.mainloop()