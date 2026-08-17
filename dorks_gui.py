#!/usr/bin/env python3
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from dorks import DORK_TYPES, run_generator


class DorkGeneratorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Google Dork Generator")
        self.resizable(False, False)
        self.keywords_file: Path | None = None
        self.domains_file: Path | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        ttk.Label(
            self,
            text="Google Dork Generator",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", **padding)

        ttk.Label(self, text="Fichier keywords (.txt, optionnel) :").grid(
            row=1, column=0, columnspan=2, sticky="w", **padding
        )

        self.keywords_label = ttk.Label(
            self,
            text="Aucun — dorks Google purs",
            width=50,
            anchor="w",
        )
        self.keywords_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=12)

        ttk.Button(
            self,
            text="Parcourir keywords...",
            command=self._select_keywords,
        ).grid(row=3, column=0, sticky="w", **padding)

        ttk.Button(
            self,
            text="Retirer keywords",
            command=self._clear_keywords,
        ).grid(row=3, column=1, sticky="e", **padding)

        ttk.Label(self, text="Fichier domaines (.txt, optionnel) :").grid(
            row=4, column=0, columnspan=2, sticky="w", **padding
        )

        self.domains_label = ttk.Label(
            self,
            text="Aucun (sans site:)",
            width=50,
            anchor="w",
        )
        self.domains_label.grid(row=5, column=0, columnspan=2, sticky="w", padx=12)

        ttk.Button(
            self,
            text="Parcourir domaines...",
            command=self._select_domains,
        ).grid(row=6, column=0, sticky="w", **padding)

        ttk.Button(
            self,
            text="Retirer domaines",
            command=self._clear_domains,
        ).grid(row=6, column=1, sticky="e", **padding)

        type_frame = ttk.LabelFrame(self, text="Dorktype Google")
        type_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

        self.dorktype_var = tk.StringVar(value="google")
        ttk.Combobox(
            type_frame,
            textvariable=self.dorktype_var,
            values=list(DORK_TYPES),
            state="readonly",
            width=20,
        ).grid(row=0, column=0, sticky="w", padx=8, pady=6)

        ttk.Label(
            type_frame,
            text="google = dorks purs + keywords (inurl, intitle, filetype, site:)",
        ).grid(row=0, column=1, sticky="w", padx=8, pady=6)

        options_frame = ttk.LabelFrame(self, text="Options")
        options_frame.grid(row=8, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

        self.urls_var = tk.BooleanVar(value=False)
        self.filetypes_var = tk.BooleanVar(value=True)
        self.inurl_var = tk.BooleanVar(value=True)
        self.intitle_var = tk.BooleanVar(value=True)
        self.site_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(
            options_frame, text="Exporter URLs Google", variable=self.urls_var
        ).grid(row=0, column=0, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(
            options_frame, text="Filetypes", variable=self.filetypes_var
        ).grid(row=0, column=1, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(
            options_frame, text="Inurl", variable=self.inurl_var
        ).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(
            options_frame, text="Intitle", variable=self.intitle_var
        ).grid(row=1, column=1, sticky="w", padx=8, pady=4)
        ttk.Checkbutton(
            options_frame, text="Site:", variable=self.site_var
        ).grid(row=2, column=0, sticky="w", padx=8, pady=4)

        self.start_button = ttk.Button(
            self,
            text="Générer les Google dorks",
            command=self._start_generation,
        )
        self.start_button.grid(row=9, column=0, columnspan=2, sticky="e", **padding)

        self.status_label = ttk.Label(self, text="Prêt.")
        self.status_label.grid(row=10, column=0, columnspan=2, sticky="w", **padding)

    def _select_keywords(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier de keywords",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not file_path:
            return

        self.keywords_file = Path(file_path)
        self.keywords_label.config(text=str(self.keywords_file))
        self.status_label.config(text="Keywords sélectionnés.")

    def _clear_keywords(self) -> None:
        self.keywords_file = None
        self.keywords_label.config(text="Aucun — dorks Google purs")
        self.status_label.config(text="Mode dorks purs.")

    def _select_domains(self) -> None:
        file_path = filedialog.askopenfilename(
            title="Sélectionner un fichier de domaines",
            filetypes=[
                ("Fichiers texte", "*.txt"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not file_path:
            return

        self.domains_file = Path(file_path)
        self.domains_label.config(text=str(self.domains_file))
        self.status_label.config(text="Domaines sélectionnés.")

    def _clear_domains(self) -> None:
        self.domains_file = None
        self.domains_label.config(text="Aucun (sans site:)")
        self.status_label.config(text="Domaines retirés.")

    def _start_generation(self) -> None:
        self.start_button.config(state="disabled")
        self.status_label.config(text="Génération en cours...")

        thread = threading.Thread(target=self._run_generator, daemon=True)
        thread.start()

    def _run_generator(self) -> None:
        try:
            count, output_path = run_generator(
                input_path=self.keywords_file,
                domains_path=self.domains_file,
                dork_types=[self.dorktype_var.get()],
                pure=self.keywords_file is None,
                as_urls=self.urls_var.get(),
                include_filetypes=self.filetypes_var.get(),
                include_inurl=self.inurl_var.get(),
                include_intitle=self.intitle_var.get(),
                include_site=self.site_var.get(),
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
        label = "URLs Google" if self.urls_var.get() else "Google dorks"
        messagebox.showinfo(
            "Terminé",
            f"{count} {label} générés dans :\n{output_path}",
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
