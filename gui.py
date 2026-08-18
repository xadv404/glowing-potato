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
    get_lang_profile,
    get_preset,
    normalize_lang,
)
from dorks import run_generator as run_dork_generator
from main import run_scraper

MODES = {
    "pipeline": "Pipeline complet (keywords → dorks)",
    "keywords": "Keywords seulement",
    "dorks": "Dorks seulement",
}


class ToolkitApp(tk.Tk):
    def __init__(self, initial_mode: str = "pipeline") -> None:
        super().__init__()
        self.title("Keyword + Dork Toolkit")
        self.resizable(False, False)
        self.seeds_file: Path | None = None
        self.keywords_file: Path | None = None
        self._build_ui(initial_mode)

    def _build_ui(self, initial_mode: str) -> None:
        pad = {"padx": 12, "pady": 5}

        ttk.Label(
            self,
            text="Keyword + Dork Toolkit",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        # --- Mode ---
        mode_frame = ttk.LabelFrame(self, text="Mode", padding=8)
        mode_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        self.mode_var = tk.StringVar(value=initial_mode if initial_mode in MODES else "pipeline")
        for col, (mode_id, label) in enumerate(MODES.items()):
            ttk.Radiobutton(
                mode_frame,
                text=label,
                variable=self.mode_var,
                value=mode_id,
                command=self._on_mode_change,
            ).grid(row=0, column=col, sticky="w", padx=8)

        # --- Keywords section ---
        self.kw_frame = ttk.LabelFrame(self, text="Keywords (Google autocomplete)", padding=8)
        self.kw_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        ttk.Label(self.kw_frame, text="Fichier seeds (.txt) :").grid(row=0, column=0, sticky="w")
        self.seeds_label = ttk.Label(
            self.kw_frame, text="Aucun fichier", width=48, anchor="w"
        )
        self.seeds_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Button(
            self.kw_frame, text="Parcourir...", command=self._select_seeds
        ).grid(row=2, column=0, sticky="w")

        ttk.Label(self.kw_frame, text="Preset qualité :").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.preset_var = tk.StringVar(value=get_preset(DEFAULT_PRESET_ID).label)
        preset_combo = ttk.Combobox(
            self.kw_frame,
            textvariable=self.preset_var,
            values=[p.label for p in QUALITY_PRESETS.values()],
            state="readonly",
            width=42,
        )
        preset_combo.grid(row=4, column=0, columnspan=2, sticky="w", pady=2)
        preset_combo.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.preset_desc = ttk.Label(
            self.kw_frame,
            text=get_preset(DEFAULT_PRESET_ID).description,
            wraplength=420,
            font=("Segoe UI", 8),
            foreground="#555",
        )
        self.preset_desc.grid(row=5, column=0, columnspan=2, sticky="w")

        ttk.Label(self.kw_frame, text="Langue (Google hl) :").grid(
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
            self.kw_frame,
            textvariable=self.lang_var,
            values=lang_labels,
            width=42,
        )
        self.lang_combo.grid(row=7, column=0, columnspan=2, sticky="w", pady=2)
        ttk.Label(
            self.kw_frame,
            text="Codes hl Google : fr, en, es, de, ja, zh-CN… (saisie libre)",
            wraplength=420,
            font=("Segoe UI", 8),
            foreground="#555",
        ).grid(row=8, column=0, columnspan=2, sticky="w")

        # --- Dorks section ---
        self.dork_frame = ttk.LabelFrame(self, text="Dorks SQL", padding=8)
        self.dork_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=12, pady=4)

        self.enriched_label_text = ttk.Label(
            self.dork_frame, text="Fichier keywords enrichis (.txt) :"
        )
        self.enriched_label_text.grid(row=0, column=0, sticky="w")
        self.enriched_label = ttk.Label(
            self.dork_frame, text="(généré automatiquement en mode pipeline)", width=48, anchor="w"
        )
        self.enriched_label.grid(row=1, column=0, columnspan=2, sticky="w", pady=2)
        self.enriched_browse_btn = ttk.Button(
            self.dork_frame,
            text="Parcourir keywords...",
            command=self._select_keywords,
        )
        self.enriched_browse_btn.grid(row=2, column=0, sticky="w")

        ttk.Label(self.dork_frame, text="Domaine cible (optionnel) :").grid(
            row=3, column=0, sticky="w", pady=(8, 0)
        )
        self.domain_var = tk.StringVar()
        ttk.Entry(self.dork_frame, textvariable=self.domain_var, width=44).grid(
            row=4, column=0, sticky="w", pady=2
        )

        # --- Actions ---
        self.start_button = ttk.Button(
            self, text="Lancer", command=self._start, state="disabled", width=18
        )
        self.start_button.grid(row=4, column=2, sticky="e", padx=12, pady=8)

        self.status_label = ttk.Label(self, text="Prêt.")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky="w", padx=12, pady=(0, 10))

        self._label_to_id = {p.label: p.id for p in QUALITY_PRESETS.values()}
        self._on_mode_change()

    def _on_mode_change(self) -> None:
        mode = self.mode_var.get()

        if mode == "pipeline":
            self.kw_frame.grid()
            self.dork_frame.grid()
            self.enriched_browse_btn.grid_remove()
            self.enriched_label.config(text="(généré automatiquement après enrichissement)")
        elif mode == "keywords":
            self.kw_frame.grid()
            self.dork_frame.grid_remove()
        else:  # dorks
            self.kw_frame.grid_remove()
            self.dork_frame.grid()
            self.enriched_browse_btn.grid()
            self.enriched_label.config(text="Aucun fichier")

        self._update_start_button()

    def _on_preset_change(self, _event: object = None) -> None:
        preset = self._current_preset()
        self.preset_desc.config(text=preset.description)

    def _current_preset(self):
        label = self.preset_var.get()
        preset_id = self._label_to_id.get(label, DEFAULT_PRESET_ID)
        return get_preset(preset_id)

    def _current_preset_id(self) -> str:
        return self._current_preset().id

    def _current_lang(self) -> str:
        raw = self.lang_var.get().strip()
        if " — " in raw:
            return normalize_lang(raw.split(" — ", 1)[0])
        return normalize_lang(raw)

    def _select_seeds(self) -> None:
        path = filedialog.askopenfilename(
            title="Fichier seeds (1 keyword par ligne)",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous", "*.*")],
        )
        if not path:
            return
        self.seeds_file = Path(path)
        self.seeds_label.config(text=str(self.seeds_file))
        self._update_start_button()

    def _select_keywords(self) -> None:
        path = filedialog.askopenfilename(
            title="Fichier keywords enrichis",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous", "*.*")],
        )
        if not path:
            return
        self.keywords_file = Path(path)
        self.enriched_label.config(text=str(self.keywords_file))
        self._update_start_button()

    def _update_start_button(self) -> None:
        mode = self.mode_var.get()
        ready = False
        if mode == "pipeline":
            ready = self.seeds_file is not None
        elif mode == "keywords":
            ready = self.seeds_file is not None
        else:
            ready = self.keywords_file is not None
        self.start_button.config(state="normal" if ready else "disabled")

    def _start(self) -> None:
        mode = self.mode_var.get()
        if mode in ("pipeline", "keywords") and self.seeds_file is None:
            messagebox.showwarning("Attention", "Sélectionne un fichier seeds.")
            return
        if mode == "dorks" and self.keywords_file is None:
            messagebox.showwarning("Attention", "Sélectionne un fichier keywords enrichis.")
            return

        self.start_button.config(state="disabled")
        self.status_label.config(text="En cours...")
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self) -> None:
        mode = self.mode_var.get()
        domain = self.domain_var.get().strip().lower() or None

        try:
            kw_count = 0
            dork_count = 0
            enriched_path: Path | None = None
            dorks_path: Path | None = None

            if mode in ("pipeline", "keywords"):
                assert self.seeds_file is not None
                preset_id = self._current_preset_id()
                self.after(
                    0,
                    lambda: self.status_label.config(
                        text=f"Scraping ({get_preset(preset_id).label})..."
                    ),
                )
                lang = self._current_lang()
                kw_count, enriched_path = run_scraper(
                    self.seeds_file,
                    preset_id=preset_id,
                    lang=lang,
                )

            if mode == "pipeline":
                assert enriched_path is not None
                self.after(0, lambda: self.status_label.config(text="Génération dorks..."))
                dork_count, dorks_path = run_dork_generator(
                    enriched_path, domain=domain
                )
            elif mode == "dorks":
                assert self.keywords_file is not None
                self.after(0, lambda: self.status_label.config(text="Génération dorks..."))
                dork_count, dorks_path = run_dork_generator(
                    self.keywords_file, domain=domain
                )

        except (FileNotFoundError, ValueError) as exc:
            self.after(0, lambda: self._on_error(str(exc)))
            return
        except Exception as exc:
            self.after(0, lambda: self._on_error(f"Erreur : {exc}"))
            return

        self.after(
            0,
            lambda: self._on_success(mode, kw_count, enriched_path, dork_count, dorks_path),
        )

    def _on_success(
        self,
        mode: str,
        kw_count: int,
        enriched_path: Path | None,
        dork_count: int,
        dorks_path: Path | None,
    ) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Terminé.")

        if mode == "pipeline":
            from dorks import SQLI_HQ_TEMPLATES
            tpl = len(SQLI_HQ_TEMPLATES)
            messagebox.showinfo(
                "Terminé",
                f"Preset : {self._current_preset().label}\n\n"
                f"{kw_count} keywords :\n{enriched_path}\n\n"
                f"{kw_count} × {tpl} dorktypes = {dork_count} dorks SQL :\n{dorks_path}",
            )
        elif mode == "keywords":
            profile = get_lang_profile(self._current_lang())
            messagebox.showinfo(
                "Terminé",
                f"Preset : {self._current_preset().label}\n"
                f"Langue : {profile.label}\n\n"
                f"{kw_count} keywords enrichis :\n{enriched_path}",
            )
        else:
            from dorks import SQLI_HQ_TEMPLATES
            tpl = len(SQLI_HQ_TEMPLATES)
            kw_part = dork_count // tpl if tpl else dork_count
            messagebox.showinfo(
                "Terminé",
                f"{kw_part} keywords × {tpl} dorktypes = {dork_count} dorks SQL HQ :\n{dorks_path}",
            )

    def _on_error(self, message: str) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Erreur.")
        messagebox.showerror("Erreur", message)


def main(initial_mode: str = "pipeline") -> None:
    app = ToolkitApp(initial_mode=initial_mode)
    app.mainloop()


if __name__ == "__main__":
    main()
