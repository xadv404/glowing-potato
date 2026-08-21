#!/usr/bin/env python3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from config import (
    DEFAULT_LANG,
    DEFAULT_PRESET_ID,
    LANGUAGE_OPTIONS,
    QUALITY_PRESETS,
    UnsupportedLanguageError,
    get_lang_profile,
    get_preset,
    normalize_lang,
)
from main import run_scraper


class ToolkitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Keyword Scraper")
        self.resizable(False, False)
        self.seeds_file: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        pad = {"padx": 12, "pady": 5}

        ttk.Label(
            self,
            text="Keyword Scraper",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        # --- Keywords section ---
        kw_frame = ttk.LabelFrame(self, text="Google Autocomplete", padding=8)
        kw_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        ttk.Label(kw_frame, text="Fichier seeds (.txt) :").grid(row=0, column=0, sticky="w")
        self.seeds_label = ttk.Label(kw_frame, text="Aucun fichier", width=48, anchor="w")
        self.seeds_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Button(kw_frame, text="Parcourir...", command=self._select_seeds).grid(
            row=2, column=0, sticky="w"
        )

        ttk.Label(kw_frame, text="Preset qualité :").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.preset_var = tk.StringVar(value=get_preset(DEFAULT_PRESET_ID).label)
        preset_combo = ttk.Combobox(
            kw_frame,
            textvariable=self.preset_var,
            values=[p.label for p in QUALITY_PRESETS.values()],
            state="readonly",
            width=42,
        )
        preset_combo.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.preset_desc = ttk.Label(
            kw_frame,
            text=get_preset(DEFAULT_PRESET_ID).description,
            wraplength=420,
            font=("Segoe UI", 8),
            foreground="#555",
        )
        self.preset_desc.grid(row=5, column=0, columnspan=2, sticky="w")

        ttk.Label(kw_frame, text="Langue (Google hl) :").grid(
            row=6, column=0, sticky="w", pady=(8, 0)
        )
        lang_labels = [f"{code} — {label}" for code, label in LANGUAGE_OPTIONS]
        self.lang_var = tk.StringVar(
            value=next(
                (f"{code} — {label}" for code, label in LANGUAGE_OPTIONS if code == DEFAULT_LANG),
                lang_labels[0],
            )
        )
        self.lang_combo = ttk.Combobox(
            kw_frame,
            textvariable=self.lang_var,
            values=lang_labels,
            width=42,
        )
        self.lang_combo.grid(row=7, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(
            kw_frame,
            text="Variantes régionales acceptées (en-US, pt-BR, zh-TW…). Autre langue → refus.",
            wraplength=420,
            font=("Segoe UI", 8),
            foreground="#555",
        ).grid(row=8, column=0, columnspan=2, sticky="w")

        # --- Actions ---
        self.start_button = ttk.Button(
            self, text="Lancer", command=self._start, state="disabled", width=18
        )
        self.start_button.grid(row=2, column=2, sticky="e", padx=12, pady=8)

        self.status_label = ttk.Label(self, text="Prêt.")
        self.status_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10))

        self._label_to_id = {p.label: p.id for p in QUALITY_PRESETS.values()}

    def _on_preset_change(self, _event: object = None) -> None:
        preset = self._current_preset()
        self.preset_desc.config(text=preset.description)

    def _current_preset(self):
        label = self.preset_var.get()
        preset_id = self._label_to_id.get(label, DEFAULT_PRESET_ID)
        return get_preset(preset_id)

    def _current_preset_id(self) -> str:
        return self._current_preset().id

    def _current_lang_raw(self) -> str:
        raw = self.lang_var.get().strip()
        if " — " in raw:
            return raw.split(" — ", 1)[0].strip()
        return raw

    def _current_lang(self) -> str:
        return normalize_lang(self._current_lang_raw())

    def _validate_lang(self) -> str | None:
        raw = self._current_lang_raw()
        if not raw:
            return "Indique une langue (code hl Google)."
        try:
            get_lang_profile(raw)
        except UnsupportedLanguageError as exc:
            return str(exc)
        return None

    def _select_seeds(self) -> None:
        path = filedialog.askopenfilename(
            title="Fichier seeds (1 keyword par ligne)",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous", "*.*")],
        )
        if not path:
            return
        self.seeds_file = Path(path)
        self.seeds_label.config(text=str(self.seeds_file))
        self.start_button.config(state="normal")

    def _start(self) -> None:
        if self.seeds_file is None:
            messagebox.showwarning("Attention", "Sélectionne un fichier seeds.")
            return
        lang_error = self._validate_lang()
        if lang_error:
            messagebox.showwarning("Langue non maîtrisée", lang_error)
            return
        self.start_button.config(state="disabled")
        self.status_label.config(text="En cours...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        try:
            assert self.seeds_file is not None
            preset_id = self._current_preset_id()
            self.after(
                0,
                lambda: self.status_label.config(
                    text=f"Scraping ({get_preset(preset_id).label})..."
                ),
            )
            lang = self._current_lang()
            kw_count, output_path = run_scraper(self.seeds_file, preset_id=preset_id, lang=lang)
        except (FileNotFoundError, ValueError, UnsupportedLanguageError) as exc:
            self.after(0, lambda: self._on_error(str(exc)))
            return
        except Exception as exc:
            self.after(0, lambda: self._on_error(f"Erreur : {exc}"))
            return
        self.after(0, lambda: self._on_success(kw_count, output_path))

    def _on_success(self, kw_count: int, output_path: Path | None) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Terminé.")
        profile = get_lang_profile(self._current_lang())
        messagebox.showinfo(
            "Terminé",
            f"Preset : {self._current_preset().label}\n"
            f"Langue : {profile.label}\n\n"
            f"{kw_count} keywords :\n{output_path}",
        )

    def _on_error(self, message: str) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Erreur.")
        messagebox.showerror("Erreur", message)


def main() -> None:
    app = ToolkitApp()
    app.mainloop()


if __name__ == "__main__":
    main()
