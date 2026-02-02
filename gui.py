import os
import sys
import threading
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

# Drag & drop
from tkinterdnd2 import DND_FILES, TkinterDnD

# Подключаем твою логику
from core.injector import start_injection
from core.extractor import start_decryption

def _clean_dnd_path(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("{") and raw.endswith("}"):
        raw = raw[1:-1]
    # если прилетело несколько путей — берём первый
    parts = raw.split()
    return parts[0] if parts else raw


def _is_image_file(p: str) -> bool:
    ext = Path(p).suffix.lower()
    return ext in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Steganography")
        self.geometry("860x560")
        self.minsize(860, 560)

        # Иконка
        icon_path = Path(__file__).with_name("hide.ico")
        if icon_path.exists():
            try:
                self.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Основной layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)

        self.tab_embed = self.tabview.add("Embed")
        self.tab_extract = self.tabview.add("Extract")

        self._build_embed_tab()
        self._build_extract_tab()

        # статус-бар
        self.status = ctk.StringVar(value="Готово")
        self.status_label = ctk.CTkLabel(self, textvariable=self.status, anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))

    # -------------------- UI: Embed --------------------
    def _build_embed_tab(self):
        t = self.tab_embed
        t.grid_columnconfigure(0, weight=1)
        t.grid_columnconfigure(1, weight=1)
        t.grid_rowconfigure(3, weight=1)

        # Drop zone / input image
        self.embed_in_path = ctk.StringVar(value="")
        drop = ctk.CTkFrame(t)
        drop.grid(row=0, column=0, columnspan=2, sticky="ew", padx=12, pady=(12, 8))
        drop.grid_columnconfigure(0, weight=1)

        self.embed_drop_label = ctk.CTkLabel(
            drop,
            text="Перетащи сюда изображение (PNG/JPG/...) или выбери кнопкой ниже",
            height=60,
            justify="center",
        )
        self.embed_drop_label.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        # enable drop on label + root
        self.embed_drop_label.drop_target_register(DND_FILES)
        self.embed_drop_label.dnd_bind("<<Drop>>", self._on_drop_embed)

        # controls row
        row1 = ctk.CTkFrame(t)
        row1.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=8)
        row1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="Input image:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.embed_in_entry = ctk.CTkEntry(row1, textvariable=self.embed_in_path)
        self.embed_in_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(row1, text="Выбрать", command=self._pick_embed_input).grid(
            row=0, column=2, padx=8, pady=8
        )

        # output row
        self.embed_out_path = ctk.StringVar(value="")
        row2 = ctk.CTkFrame(t)
        row2.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=8)
        row2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row2, text="Output image:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.embed_out_entry = ctk.CTkEntry(row2, textvariable=self.embed_out_path)
        self.embed_out_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(row2, text="Куда сохранить", command=self._pick_embed_output).grid(
            row=0, column=2, padx=8, pady=8
        )

        # text + key area
        mid = ctk.CTkFrame(t)
        mid.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=12, pady=8)
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_columnconfigure(1, weight=1)
        mid.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(mid, text="Текст для скрытия:").grid(row=0, column=0, padx=12, pady=(12, 6), sticky="w")
        ctk.CTkLabel(mid, text="Ключ:").grid(row=0, column=1, padx=12, pady=(12, 6), sticky="w")

        self.embed_text = ctk.CTkTextbox(mid, wrap="word")
        self.embed_text.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        self.embed_key = ctk.CTkEntry(mid, placeholder_text="Например: my-secret-key")
        self.embed_key.grid(row=1, column=1, padx=12, pady=(0, 12), sticky="new")

        # action row
        action = ctk.CTkFrame(t)
        action.grid(row=4, column=0, columnspan=2, sticky="ew", padx=12, pady=(8, 12))
        action.grid_columnconfigure(0, weight=1)

        self.embed_btn = ctk.CTkButton(action, text="Встроить (Encrypt + LSB Inject)", command=self._do_embed)
        self.embed_btn.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

    def _on_drop_embed(self, event):
        path = _clean_dnd_path(event.data)
        if not path:
            return
        if not _is_image_file(path):
            messagebox.showerror("Ошибка", "Это не похоже на изображение.")
            return
        self.embed_in_path.set(path)
        # дефолтный output рядом
        out = str(Path(path).with_name(Path(path).stem + "_encoded.png"))
        self.embed_out_path.set(out)
        self.status.set(f"Выбрано: {path}")

    def _pick_embed_input(self):
        p = filedialog.askopenfilename(
            title="Выбери изображение",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")],
        )
        if p:
            self.embed_in_path.set(p)
            out = str(Path(p).with_name(Path(p).stem + "_encoded.png"))
            self.embed_out_path.set(out)

    def _pick_embed_output(self):
        p = filedialog.asksaveasfilename(
            title="Сохранить как",
            defaultextension=".png",
            filetypes=[("PNG", "*.png")],
        )
        if p:
            self.embed_out_path.set(p)

    def _do_embed(self):
        in_path = self.embed_in_path.get().strip()
        out_path = self.embed_out_path.get().strip()
        text = self.embed_text.get("1.0", "end").strip()
        key = self.embed_key.get().strip()

        if not in_path or not Path(in_path).exists():
            messagebox.showerror("Ошибка", "Укажи входное изображение.")
            return
        if not out_path:
            messagebox.showerror("Ошибка", "Укажи output файл.")
            return
        if not text:
            messagebox.showerror("Ошибка", "Введи текст для скрытия.")
            return
        if not key:
            messagebox.showerror("Ошибка", "Введи ключ.")
            return

        self._set_busy(True, "Встраивание...")

        def worker():
            try:
                result = start_injection(in_path, text, key, out_path)
                self._ui_ok(f"Готово: {out_path}\n\n{result}")
            except Exception as e:
                self._ui_err(f"Ошибка при встраивании:\n{e}")
            finally:
                self._set_busy(False, "Готово")

        threading.Thread(target=worker, daemon=True).start()

    # -------------------- UI: Извлечение текста --------------------
    def _build_extract_tab(self):
        t = self.tab_extract
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(3, weight=1)

        self.extract_in_path = ctk.StringVar(value="")

        drop = ctk.CTkFrame(t)
        drop.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        drop.grid_columnconfigure(0, weight=1)

        self.extract_drop_label = ctk.CTkLabel(
            drop,
            text="Перетащи сюда изображение со скрытым текстом или выбери кнопкой ниже",
            height=60,
            justify="center",
        )
        self.extract_drop_label.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        self.extract_drop_label.drop_target_register(DND_FILES)
        self.extract_drop_label.dnd_bind("<<Drop>>", self._on_drop_extract)

        row1 = ctk.CTkFrame(t)
        row1.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        row1.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row1, text="Image:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.extract_in_entry = ctk.CTkEntry(row1, textvariable=self.extract_in_path)
        self.extract_in_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")
        ctk.CTkButton(row1, text="Выбрать", command=self._pick_extract_input).grid(
            row=0, column=2, padx=8, pady=8
        )

        row2 = ctk.CTkFrame(t)
        row2.grid(row=2, column=0, sticky="ew", padx=12, pady=8)
        row2.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row2, text="Key:").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        self.extract_key = ctk.CTkEntry(row2, placeholder_text="Если пусто — возьмётся из .env (FERNET_KEY)")
        self.extract_key.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        action = ctk.CTkFrame(t)
        action.grid(row=3, column=0, sticky="ew", padx=12, pady=(8, 12))
        action.grid_columnconfigure(0, weight=1)

        self.extract_btn = ctk.CTkButton(action, text="Извлечь (Extract + Decrypt)", command=self._do_extract)
        self.extract_btn.grid(row=0, column=0, padx=12, pady=12, sticky="ew")

        # output box
        self.extract_output = ctk.CTkTextbox(t, wrap="word")
        self.extract_output.grid(row=4, column=0, sticky="nsew", padx=12, pady=(0, 12))
        t.grid_rowconfigure(4, weight=1)

    def _on_drop_extract(self, event):
        path = _clean_dnd_path(event.data)
        if not path:
            return
        if not _is_image_file(path):
            messagebox.showerror("Ошибка", "Это не похоже на изображение.")
            return
        self.extract_in_path.set(path)
        self.status.set(f"Выбрано: {path}")

    def _pick_extract_input(self):
        p = filedialog.askopenfilename(
            title="Выбери изображение",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.webp"), ("All files", "*.*")],
        )
        if p:
            self.extract_in_path.set(p)

    def _do_extract(self):
        in_path = self.extract_in_path.get().strip()
        key = self.extract_key.get().strip() or None

        if not in_path or not Path(in_path).exists():
            messagebox.showerror("Ошибка", "Укажи изображение.")
            return

        self._set_busy(True, "Извлечение...")

        def worker():
            try:
                text = start_decryption(in_path, key_text=key)
                self._ui_set_output(text)
                self.status.set("Готово")
            except Exception as e:
                self._ui_err(f"Ошибка при извлечении:\n{e}")
            finally:
                self._set_busy(False, "Готово")

        threading.Thread(target=worker, daemon=True).start()

    # -------------------- Вспомогательные --------------------
    def _set_busy(self, busy: bool, status: str):
        def apply():
            self.status.set(status)
            state = "disabled" if busy else "normal"
            self.embed_btn.configure(state=state)
            self.extract_btn.configure(state=state)
        self.after(0, apply)

    def _ui_ok(self, msg: str):
        def apply():
            messagebox.showinfo("Успех", msg)
        self.after(0, apply)

    def _ui_err(self, msg: str):
        def apply():
            messagebox.showerror("Ошибка", msg)
        self.after(0, apply)

    def _ui_set_output(self, text: str):
        def apply():
            self.extract_output.delete("1.0", "end")
            self.extract_output.insert("1.0", text)
        self.after(0, apply)


if __name__ == "__main__":
    app = App()
    app.mainloop()
