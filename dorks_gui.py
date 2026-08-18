#!/usr/bin/env python3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dorks import SQLI_SQL_TEMPLATES, run_generator


class DorkGeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SQL Dork Generator — HQ")
        self.resizable(False, False)
        self.keywords_file: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        ttk.Label(
            self,
            text="SQLi Dork Generator",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", **padding)

        ttk.Label(
            self,
            text="Étape 2 — fichier keywords enrichis (*_keywords.txt du scraper)",
            font=("Segoe UI", 9),
        ).grid(row=1, column=0, columnspan=2, sticky="w", padx=12)

        ttk.Label(self, text="Fichier keywords enrichis (.txt) :").grid(
            row=2, column=0, columnspan=2, sticky="w", **padding
        )

        self.keywords_label = ttk.Label(
            self,
            text="Aucun fichier sélectionné",
            width=50,
            anchor="w",
        )
        self.keywords_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=12)

        ttk.Button(
            self,
            text="Parcourir keywords...",
            command=self._select_keywords,
        ).grid(row=4, column=0, columnspan=2, sticky="w", **padding)

        ttk.Label(self, text="Domaine (optionnel, ex: example.com) :").grid(
            row=5, column=0, columnspan=2, sticky="w", **padding
        )

        self.domain_var = tk.StringVar()
        ttk.Entry(self, textvariable=self.domain_var, width=40).grid(
            row=6, column=0, columnspan=2, sticky="w", padx=12, pady=4
        )

        self.start_button = ttk.Button(
            self,
            text="Générer les dorks SQLi",
            command=self._start_generation,
            state="disabled",
        )
        self.start_button.grid(row=7, column=0, columnspan=2, sticky="e", **padding)

        self.status_label = ttk.Label(self, text="Prêt.")
        self.status_label.grid(row=8, column=0, columnspan=2, sticky="w", **padding)

    def _select_keywords(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Sélectionner le fichier keywords enrichis",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not file_path:
            return

        self.keywords_file = Path(file_path)
        self.keywords_label.config(text=str(self.keywords_file))
        self.start_button.config(state="normal")
        self.status_label.config(text="Keywords sélectionnés. Clique sur Générer.")

    def _start_generation(self) -> None:
        if self.keywords_file is None:
            messagebox.showwarning("Attention", "Sélectionne d'abord un fichier keywords.")
            return

        self.start_button.config(state="disabled")
        self.status_label.config(text="Génération en cours...")

        thread = threading.Thread(target=self._run_generator, daemon=True)
        thread.start()

    def _run_generator(self) -> None:
        assert self.keywords_file is not None
        domain = self.domain_var.get().strip().lower() or None

        try:
            count, output_path = run_generator(
                input_path=self.keywords_file,
                domain=domain,
            )
        except FileNotFoundError as exc:
            self.after(0, lambda: self._on_error(str(exc)))
            return
        except ValueError as exc:
            self.after(0, lambda: self._on_error(str(exc)))
            return
        except Exception as exc:
            self.after(0, lambda: self._on_error(f"Erreur inattendue : {exc}"))
            return

        self.after(0, lambda: self._on_success(count, output_path))

    def _on_success(self, count: int, output_path: Path) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Terminé.")
        messagebox.showinfo(
            "Terminé",
            f"{count} dorks SQL HQ générés (1 par keyword) :\n{output_path}",
        )

    def _on_error(self, message: str) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Erreur.")
        messagebox.showerror("Erreur", message)


def main() -> None:
    app = DorkGeneratorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
