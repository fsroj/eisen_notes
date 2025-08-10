
import tkinter as tk
from tkcalendar import Calendar
from datetime import datetime
from tkinter import ttk, Toplevel, messagebox

class CalendarApp(ttk.Frame):
    def __init__(self, parent, notes_manager, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.notes_manager = notes_manager
        self.parent = parent
        self.selected_date = datetime.now().date()
        self._build_ui()
        self._refresh_events()

    def _build_ui(self):
        self.calendar = Calendar(self, selectmode='day', date_pattern='yyyy-mm-dd')
        self.calendar.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.calendar.bind("<<CalendarSelected>>", self._on_date_selected)

        self.events_frame = ttk.LabelFrame(self, text="Eventos para el día")
        self.events_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.events_listbox = tk.Listbox(self.events_frame, width=50, height=15)
        self.events_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.edit_button = ttk.Button(self.events_frame, text="Editar Evento", command=self._edit_event)
        self.edit_button.pack(side=tk.LEFT, padx=5, pady=5)
        self.delete_button = ttk.Button(self.events_frame, text="Eliminar Evento", command=self._delete_event)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

    def _on_date_selected(self, event=None):
        self.selected_date = datetime.strptime(self.calendar.get_date(), "%Y-%m-%d").date()
        self._refresh_events()

    def _refresh_events(self):
        self.events_listbox.delete(0, tk.END)
        date_str = self.selected_date.strftime("%Y-%m-%d")
        events = self.notes_manager.get_events_for_date(date_str)
        self.current_events = events
        for event in events:
            display = f"{event['start_datetime']} | {event['note_title']} | {event['task_line']} ({event['duration_minutes']} min)"
            self.events_listbox.insert(tk.END, display)

    def _edit_event(self):
        selection = self.events_listbox.curselection()
        if not selection:
            messagebox.showinfo("Editar Evento", "Seleccione un evento para editar.")
            return
        idx = selection[0]
        event = self.current_events[idx]
        self._open_edit_dialog(event)

    def _open_edit_dialog(self, event):
        edit_win = tk.Toplevel(self)
        edit_win.title("Editar Evento")
        edit_win.geometry("350x200")

        ttk.Label(edit_win, text="Nueva Fecha y Hora (YYYY-MM-DD HH:MM):").pack(pady=5)
        dt_var = tk.StringVar(value=event['start_datetime'])
        dt_entry = ttk.Entry(edit_win, textvariable=dt_var)
        dt_entry.pack(pady=5)

        ttk.Label(edit_win, text="Nueva Duración (minutos):").pack(pady=5)
        dur_var = tk.IntVar(value=event['duration_minutes'])
        dur_entry = ttk.Entry(edit_win, textvariable=dur_var)
        dur_entry.pack(pady=5)

        def save_changes():
            new_dt = dt_var.get()
            try:
                datetime.strptime(new_dt, "%Y-%m-%d %H:%M")
            except ValueError:
                messagebox.showerror("Error", "Formato de fecha y hora inválido.")
                return
            try:
                new_dur = int(dur_var.get())
            except ValueError:
                messagebox.showerror("Error", "Duración inválida.")
                return
            ok, msg = self.notes_manager.update_calendar_event(event['id'], new_start_datetime_str=new_dt, new_duration_minutes=new_dur)
            if ok:
                messagebox.showinfo("Éxito", msg)
                edit_win.destroy()
                self._refresh_events()
            else:
                messagebox.showerror("Error", msg)

        ttk.Button(edit_win, text="Guardar Cambios", command=save_changes).pack(pady=10)

    def _delete_event(self):
        selection = self.events_listbox.curselection()
        if not selection:
            messagebox.showinfo("Eliminar Evento", "Seleccione un evento para eliminar.")
            return
        idx = selection[0]
        event = self.current_events[idx]
        confirm = messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este evento?")
        if confirm:
            ok, msg = self.notes_manager.delete_calendar_event(event['id'])
            if ok:
                messagebox.showinfo("Éxito", msg)
                self._refresh_events()
            else:
                messagebox.showerror("Error", msg)
