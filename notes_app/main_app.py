# Modular imports
import tkinter as tk
from notes_manager import NotesManager
from notes_app import NotesApp
from calendar_app import CalendarApp

class MainApp:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Notas Maestro")
        master.withdraw()  # Oculta la ventana principal, ya que usaremos Toplevels
        self.notes_manager = NotesManager()  # Instancia única de NotesManager
        self.calendar_app_instance = None
        self.open_notes_window()

    def open_notes_window(self):
        notes_root = tk.Toplevel(self.master)
        notes_root.state('zoomed')
        self.notes_app_instance = NotesApp(notes_root, self.notes_manager)
        self.notes_app_instance.pack(fill="both", expand=True)
        if self.calendar_app_instance:
            self.notes_app_instance.calendar_app_instance = self.calendar_app_instance
        notes_root.protocol("WM_DELETE_WINDOW", self._on_notes_window_close)

    def open_calendar_window(self):
        if self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists():
            self.calendar_app_instance.master.lift()
        else:
            calendar_root = tk.Toplevel(self.master)
            self.calendar_app_instance = CalendarApp(calendar_root, self.notes_manager)
            if hasattr(self, 'notes_app_instance') and self.notes_app_instance:
                self.notes_app_instance.calendar_app_instance = self.calendar_app_instance
            calendar_root.protocol("WM_DELETE_WINDOW", self._on_calendar_window_close)

    def _on_notes_window_close(self):
        if self.notes_app_instance:
            self.notes_app_instance.master.destroy()
            self.notes_app_instance = None
        self._check_and_quit()

    def _on_calendar_window_close(self):
        if self.calendar_app_instance:
            self.calendar_app_instance.master.destroy()
            self.calendar_app_instance = None
        self._check_and_quit()

    def _check_and_quit(self):
        notes_open = (self.notes_app_instance and self.notes_app_instance.master.winfo_exists())
        calendar_open = (self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists())
        if not (notes_open or calendar_open):
            self.master.quit()

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()
