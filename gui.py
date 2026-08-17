#!/usr/bin/env python3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from main import run_scraper


class KeywordScraperApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Keyword Scraper")
        self.resizable(False, False)
        self.selected_file: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        ttk.Label(
            self,
            text="Keyword Scraper",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", **padding)

        ttk.Label(self, text="Fichier source (.txt) :").grid(
            row=1, column=0, sticky="w", **padding
        )

        self.file_label = ttk.Label(
            self,
            text="Aucun fichier sélectionné",
            width=45,
            anchor="w",
        )
        self.file_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=12)

        ttk.Button(
            self,
            text="Parcourir...",
            command=self._select_file,
        ).grid(row=3, column=0, sticky="w", **padding)

        self.start_button = ttk.Button(
            self,
            text="Lancer le scraping",
            command=self._start_scraping,
            state="disabled",
        )
        self.start_button.grid(row=3, column=1, sticky="e", **padding)

        self.status_label = ttk.Label(self, text="Prêt.")
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w", **padding)

    def _select_file(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier de keywords",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not file_path:
            return

        self.selected_file = Path(file_path)
        self.file_label.config(text=str(self.selected_file))
        self.start_button.config(state="normal")
        self.status_label.config(text="Fichier sélectionné. Clique sur Lancer.")

    def _start_scraping(self) -> None:
        if self.selected_file is None:
            messagebox.showwarning("Attention", "Sélectionne d'abord un fichier txt.")
            return

        self.start_button.config(state="disabled")
        self.status_label.config(text="Scraping en cours...")

        thread = threading.Thread(target=self._run_scraper, daemon=True)
        thread.start()

    def _run_scraper(self) -> None:
        assert self.selected_file is not None

        try:
            count, output_path = run_scraper(self.selected_file)
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
            f"{count} keywords sauvegardés dans :\n{output_path}",
        )

    def _on_error(self, message: str) -> None:
        self.start_button.config(state="normal")
        self.status_label.config(text="Erreur.")
        messagebox.showerror("Erreur", message)


def main() -> None:
    app = KeywordScraperApp()
    app.mainloop()


if __name__ == "__main__":
    main()
