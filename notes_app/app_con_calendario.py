import os
import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog, Toplevel, filedialog  # Asegúrate de importar filedialog
from tkinter import ttk, PhotoImage
from datetime import datetime, timedelta
import json
import hashlib
from tkcalendar import Calendar
import tkinter.colorchooser

# --- Lógica de Notas y Calendario ---
class NotesManager:
    def __init__(self, notes_dir="notes", calendar_file="calendar_events.json"):
        self.notes_dir = notes_dir
        os.makedirs(self.notes_dir, exist_ok=True)
        self.calendar_file = calendar_file

        self.valid_roles = ["Programador", "Social", "Tesista", "General", "Asistente", "Work-out", "Estudiante", "Diseñador"]
        self.eisenhower_categories = {
            "HACER_AHORA": "Urgente e Importante",
            "PLANIFICAR": "Importante, no Urgente",
            "DELEGAR": "Urgente, no Importante",
            "ELIMINAR": "No Urgente, no Importante"
        }
        self.eisenhower_abbreviations = {
            "HA": "HACER_AHORA",
            "P": "PLANIFICAR",
            "D": "DELEGAR",
            "E": "ELIMINAR"
        }
        self.eisenhower_prefixes_map = {f"[E:{k}]": v for k, v in self.eisenhower_abbreviations.items()}

        self.calendar_events = self._load_calendar_events()

    def _get_note_path(self, title):
        """
        Genera la ruta completa del archivo de la nota.
        Soporta jerarquía: 'padre/hijo' -> notes/padre/hijo.md
        """
        # Soporta rutas tipo 'padre/hijo'
        parts = [p.replace(' ', '_').lower() for p in title.split('/')]
        if len(parts) > 1:
            dir_path = os.path.join(self.notes_dir, *parts[:-1])
            os.makedirs(dir_path, exist_ok=True)
        else:
            dir_path = self.notes_dir
        return os.path.join(dir_path, f"{parts[-1]}.md")

    def create_note(self, title):
        """Crea una nueva nota si no existe."""
        note_path = self._get_note_path(title)
        if not os.path.exists(note_path):
            try:
                with open(note_path, 'w', encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                return True, f"Nota '{title}' creada."
            except Exception as e:
                return False, f"Error al crear la nota: {e}"
        return True, f"La nota '{title}' ya existe."

    def save_note_content(self, title, content):
        """Guarda el contenido completo en una nota, sobrescribiendo el archivo."""
        note_path = self._get_note_path(title)
        if not os.path.exists(note_path):
            return False, f"Error: La nota '{title}' no existe para guardar."
        try:
            with open(note_path, 'w', encoding="utf-8") as f:
                f.write(content)
            return True, f"Nota '{title}' guardada exitosamente."
        except Exception as e:
            return False, f"Error al guardar la nota: {e}"

    def list_notes(self):
        """Lista todas las notas disponibles."""
        notes = [f.replace('.md', '') for f in os.listdir(self.notes_dir) if f.endswith('.md')]
        return [note.replace('_', ' ').title() for note in notes]

    def list_notes_hierarchy(self):
        """
        Devuelve la jerarquía de notas como un diccionario:
        { 'padre': [hijo1, hijo2, ...], ... }
        Las notas en subcarpetas se consideran hijas.
        """
        hierarchy = {}
        for root, dirs, files in os.walk(self.notes_dir):
            parent = os.path.relpath(root, self.notes_dir)
            if parent == ".":
                parent = ""
            md_files = [f[:-3] for f in files if f.endswith('.md')]
            if parent not in hierarchy:
                hierarchy[parent] = []
            hierarchy[parent].extend(md_files)
        return hierarchy

    def get_note_content(self, title):
        """Obtiene el contenido completo de una nota."""
        note_path = self._get_note_path(title)
        if not os.path.exists(note_path):
            return None, f"Error: La nota '{title}' no existe."
        try:
            with open(note_path, 'r', encoding="utf-8") as f:
                content = f.read()
            return content, "Contenido cargado."
        except Exception as e:
            return None, f"Error al leer la nota: {e}"

    def get_line_classification(self, line_text):
        """
        Determina todas las clasificaciones (roles y Eisenhower) en una línea.
        Ahora soporta múltiples roles al inicio de la línea.
        Devuelve una lista de tuplas (tipo, nombre_clasificacion).
        """
        original_line = line_text.strip()
        remaining_line = original_line
        classifications = []

        # Detectar múltiples roles al inicio
        found_role = True
        while found_role:
            found_role = False
            for r in self.valid_roles:
                role_prefix = f"[{r}]"
                if remaining_line.startswith(role_prefix):
                    classifications.append(("role", r))
                    remaining_line = remaining_line[len(role_prefix):].strip()
                    found_role = True
                    break

        # Solo una categoría Eisenhower por línea (puedes cambiar esto si quieres varias)
        for prefix, key in self.eisenhower_prefixes_map.items():
            if remaining_line.startswith(prefix):
                classifications.append(("eisenhower", key))
                remaining_line = remaining_line[len(prefix):].strip()
                break

        if not classifications and original_line:
            return [("general_text", None)]

        return classifications


    def filter_note_by_classification(self, title, classification_type, classification_name):
        """
        Filtra las líneas de una nota por rol o categoría de Eisenhower.
        Ahora verifica si ALGUNA de las clasificaciones de la línea coincide.
        """
        content, msg = self.get_note_content(title)
        if content is None:
            return [], msg

        filtered_lines_with_tags = []
        lines = content.split('\n')

        for line in lines:
            line_stripped = line.strip()
            detected_classifications = self.get_line_classification(line_stripped)

            found_match = False
            primary_tag_to_display = "general_text"

            for detected_type, detected_name in detected_classifications:
                if detected_type == "role" and detected_name == classification_name and classification_type == "role":
                    found_match = True
                    primary_tag_to_display = detected_name
                    break
                elif detected_type == "eisenhower" and detected_name == classification_name and classification_type == "eisenhower":
                    found_match = True
                    primary_tag_to_display = "EISENHOWER_" + detected_name
                    break
                elif detected_type == "general_text":
                    primary_tag_to_display = "general_text"

            if found_match:
                filtered_lines_with_tags.append((line_stripped, primary_tag_to_display))

        if not filtered_lines_with_tags:
            return [], f"No se encontraron líneas para '{classification_name}' en esta nota."

        return filtered_lines_with_tags, "Filtrado exitoso."

    # --- Métodos para el Calendario ---
    def _load_calendar_events(self):
        """Carga los eventos del calendario desde un archivo JSON."""
        if os.path.exists(self.calendar_file):
            with open(self.calendar_file, 'r', encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return [] # Archivo vacío o corrupto
        return []

    def _save_calendar_events(self):
        """Guarda los eventos del calendario en un archivo JSON."""
        with open(self.calendar_file, 'w', encoding="utf-8") as f:
            json.dump(self.calendar_events, f, indent=4)

    def add_calendar_event(self, note_title, line_text, start_datetime_str, duration_minutes):
        """
        Añade un evento al calendario.
        start_datetime_str: string en formato "YYYY-MM-DD HH:MM"
        """
        # Para evitar duplicados en el calendario si se programa la misma línea
        # a la misma hora desde una nota
        event_id = hashlib.md5(f"{note_title}-{line_text}-{start_datetime_str}".encode()).hexdigest()

        for event in self.calendar_events:
            if event['id'] == event_id:
                return False, "Esta tarea ya está programada con la misma fecha y hora."

        event = {
            "id": event_id,
            "note_title": note_title,
            "task_line": line_text,
            "start_datetime": start_datetime_str,
            "duration_minutes": duration_minutes
        }
        self.calendar_events.append(event)
        self._save_calendar_events()
        return True, "Evento añadido al calendario."

    def get_events_for_date(self, target_date_str):
        """
        Obtiene todos los eventos para una fecha específica.
        target_date_str: string en formato "YYYY-MM-DD"
        """
        events_for_date = []
        for event in self.calendar_events:
            event_date_str = event['start_datetime'].split(' ')[0] # Obtener solo la fecha
            if event_date_str == target_date_str:
                events_for_date.append(event)

        # Ordenar eventos por hora
        events_for_date.sort(key=lambda x: datetime.strptime(x['start_datetime'], "%Y-%m-%d %H:%M"))
        return events_for_date

    def update_calendar_event(self, event_id, new_start_datetime_str=None, new_duration_minutes=None):
        """Actualiza un evento existente del calendario."""
        for event in self.calendar_events:
            if event['id'] == event_id:
                if new_start_datetime_str:
                    event['start_datetime'] = new_start_datetime_str
                if new_duration_minutes is not None:
                    event['duration_minutes'] = new_duration_minutes
                self._save_calendar_events()
                return True, "Evento actualizado."
        return False, "Evento no encontrado."

    def delete_calendar_event(self, event_id):
        """Elimina un evento del calendario por su ID."""
        initial_len = len(self.calendar_events)
        self.calendar_events = [event for event in self.calendar_events if event['id'] != event_id]
        if len(self.calendar_events) < initial_len:
            self._save_calendar_events()
            return True, "Evento eliminado."
        return False, "Evento no encontrado."

# --- Interfaz Gráfica del Calendario ---
class CalendarApp:
    def __init__(self, master, notes_manager):
        self.master = master
        self.master.title("Calendario de Tareas")
        self.master.geometry("700x600") # Ajustar tamaño para el calendario gráfico

        self.notes_manager = notes_manager
        self.selected_date = datetime.now() # Fecha por defecto: hoy

        # Colores de la app
        self.bg_color = "#2E2E2E"
        self.fg_color = "#F5F5F5"
        self.panel_bg = "#3A3A3A"
        self.accent_color = "#007AFF"
        self.text_input_bg = "#444444"
        self.border_color = "#555555"
        self.calendar_selected_day_color = "#6B9BFF" # Color para el día seleccionado en el calendario
        self.calendar_today_color = "#FF6B6B" # Color para el día de hoy en el calendario
        self.calendar_fg_color = "#FFFFFF" # Color del texto en el calendario
        self.calendar_bg_color = "#3A3A3A" # Color de fondo del calendario
        self.calendar_header_color = "#555555" # Color del encabezado (mes/año)
        self.calendar_separator_color = "#666666"

        self.font_bold = ("Helvetica Neue", 12, "bold")
        self.font_normal = ("Helvetica Neue", 11)
        self.font_small = ("Helvetica Neue", 10)

        self.setup_ui()
        self.update_calendar_view()

    def setup_ui(self):
        # Destruir todos los widgets existentes antes de recrear la UI
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.config(bg=self.bg_color)

        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            self.style.theme_use('alt')

        self.style.configure('.', background=self.bg_color, foreground=self.fg_color, font=self.font_normal)
        self.style.configure('TFrame', background=self.panel_bg)

        self.style.configure('TButton',
                             background=self.panel_bg,
                             foreground=self.fg_color,
                             font=self.font_normal,
                             borderwidth=0,
                             focusthickness=0,
                             relief="flat",
                             padding=[10, 5])
        self.style.map('TButton',
                        background=[('active', self.accent_color)],
                        foreground=[('active', 'white')])

        # --- Paneles principales ---
        main_pane = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, bg=self.bg_color, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left Frame (Calendar Widget)
        left_frame = ttk.Frame(main_pane, style='TFrame', padding=(15, 15, 10, 15))
        main_pane.add(left_frame, width=350) # Ancho fijo para el calendario

        tk.Label(left_frame, text="Seleccionar Fecha", font=("Helvetica Neue", 16, "bold"), bg=self.panel_bg, fg=self.fg_color).pack(pady=(0, 10))

        self.calendar = Calendar(left_frame,
                                 selectmode='day',
                                 year=self.selected_date.year,
                                 month=self.selected_date.month,
                                 day=self.selected_date.day,
                                 date_pattern='dd/mm/yyyy', # Formato de fecha
                                 bg=self.calendar_bg_color,
                                 fg=self.calendar_fg_color,
                                 headersbackground=self.calendar_header_color,
                                 headersforeground=self.calendar_fg_color,
                                 normalbackground=self.calendar_bg_color,
                                 normalforeground=self.calendar_fg_color,
                                 weekendbackground=self.calendar_bg_color,
                                 weekendforeground=self.calendar_fg_color,
                                 othermonthforeground=self.fg_color, # Colores más sutiles para otros meses
                                 othermonthbackground=self.panel_bg,
                                 othermonthweforeground=self.fg_color,
                                 othermonthwebackground=self.panel_bg,
                                 selectbackground=self.calendar_selected_day_color,
                                 selectforeground="white",
                                 tooltipfg="black", # Tooltip del día
                                 bordercolor=self.border_color,
                                 showweeknumbers=False,
                                 font=self.font_normal)
        self.calendar.pack(pady=10, padx=5, fill=tk.BOTH, expand=True)
        self.calendar.bind("<<CalendarSelected>>", self.on_calendar_date_select)

        # Right Frame (Events List)
        right_frame = ttk.Frame(main_pane, style='TFrame', padding=(15, 15, 15, 15))
        main_pane.add(right_frame)

        self.date_label = ttk.Label(right_frame, text="", font=("Helvetica Neue", 14, "bold"))
        self.date_label.pack(pady=(0, 10), anchor="w")

        tk.Label(right_frame, text="Eventos del Día:", font=self.font_bold, bg=self.panel_bg, fg=self.fg_color).pack(pady=(0, 5), anchor="w")

        self.events_listbox = tk.Listbox(right_frame, font=self.font_normal,
                                         bg=self.text_input_bg, fg=self.fg_color,
                                         selectbackground=self.accent_color, selectforeground="white",
                                         highlightbackground=self.border_color, highlightthickness=1,
                                         bd=0, relief="flat", height=15)
        self.events_listbox.pack(fill=tk.BOTH, expand=True)

        # Botones de acción para eventos
        button_frame_bottom = ttk.Frame(right_frame, style='TFrame')
        button_frame_bottom.pack(fill=tk.X, pady=10)

        ttk.Button(button_frame_bottom, text="Editar Evento", command=self.edit_selected_event).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame_bottom, text="Eliminar Evento", command=self.delete_selected_event).pack(side=tk.LEFT, padx=5)

    def on_calendar_date_select(self, event):
        # Callback cuando se selecciona una fecha en el widget Calendar
        selected_date_str = self.calendar.get_date()
        # tkcalendar devuelve la fecha en 'dd/mm/yy' o 'dd/mm/yyyy'
        # Necesitamos convertirla a datetime object para almacenarla
        try:
            self.selected_date = datetime.strptime(selected_date_str, "%d/%m/%Y")
        except ValueError:
            # Fallback para 'dd/mm/yy' si 'dd/mm/yyyy' falla
            self.selected_date = datetime.strptime(selected_date_str, "%d/%m/%y")
        self.update_calendar_view()

    def update_calendar_view(self):
        self.date_label.config(text=self.selected_date.strftime("%A, %d de %B de %Y"))

        self.events_listbox.delete(0, tk.END)

        date_str = self.selected_date.strftime("%Y-%m-%d")
        events = self.notes_manager.get_events_for_date(date_str)

        if not events:
            self.events_listbox.insert(tk.END, "No hay eventos programados para este día.")
            return

        for event in events:
            time_str = datetime.strptime(event['start_datetime'], "%Y-%m-%d %H:%M").strftime("%H:%M")
            display_text = f"{time_str} - {event['task_line']} (Nota: {event['note_title']})"
            self.events_listbox.insert(tk.END, display_text)
            # No almacenamos el ID directamente en el item_config, lo buscaremos dinámicamente

    def _get_selected_event_id(self):
        selected_index = self.events_listbox.curselection()
        if not selected_index:
            return None, None

        item_data = self.events_listbox.get(selected_index[0])

        # Necesitamos el ID del evento para editarlo/eliminarlo.
        # Ya que no lo almacenamos directamente en el Listbox (lo cual es complejo con Tkinter),
        # lo buscaremos a partir del texto y la fecha seleccionada.

        current_events = self.notes_manager.get_events_for_date(self.selected_date.strftime("%Y-%m-%d"))
        for event in current_events:
            time_str = datetime.strptime(event['start_datetime'], "%Y-%m-%d %H:%M").strftime("%H:%M")
            display_text = f"{time_str} - {event['task_line']} (Nota: {event['note_title']})"
            if display_text == item_data:
                return event['id'], event # Retornar el ID y el objeto evento completo
        return None, None


    def edit_selected_event(self):
        event_id, original_event = self._get_selected_event_id()
        if not event_id:
            messagebox.showwarning("Editar Evento", "Selecciona un evento para editar.", parent=self.master)
            return

        # Abrir un diálogo similar al de programar, pero con valores pre-rellenados
        self._open_schedule_dialog(original_event['note_title'], original_event['task_line'], event_id, original_event['start_datetime'])


    def delete_selected_event(self):
        event_id, _ = self._get_selected_event_id()
        if not event_id:
            messagebox.showwarning("Eliminar Evento", "Selecciona un evento para eliminar.", parent=self.master)
            return

        if messagebox.askyesno("Confirmar Eliminación", "¿Estás seguro de que quieres eliminar este evento?", parent=self.master):
            success, msg = self.notes_manager.delete_calendar_event(event_id)
            if success:
                messagebox.showinfo("Eliminar Evento", msg, parent=self.master)
                self.update_calendar_view()
            else:
                messagebox.showerror("Eliminar Evento", msg, parent=self.master)

    # Método auxiliar para abrir el diálogo de programación/edición
    def _open_schedule_dialog(self, note_title, task_line, event_id=None, initial_datetime_str=None):
        dialog = Toplevel(self.master)
        dialog.title("Programar Tarea" if event_id is None else "Editar Tarea")
        dialog.geometry("400x300")
        dialog.transient(self.master)
        dialog.grab_set()

        dialog.config(bg=self.panel_bg)

        tk.Label(dialog, text=f"Tarea: '{task_line}'", bg=self.panel_bg, fg=self.fg_color, font=self.font_bold).pack(pady=5)
        tk.Label(dialog, text=f"De Nota: '{note_title}'", bg=self.panel_bg, fg=self.fg_color, font=self.font_small).pack(pady=2)

        current_datetime = datetime.now()
        if initial_datetime_str:
            current_datetime = datetime.strptime(initial_datetime_str, "%Y-%m-%d %H:%M")

        # Calendar Widget para selección de fecha
        cal_frame = ttk.Frame(dialog, style='TFrame')
        cal_frame.pack(pady=5)
        cal = Calendar(cal_frame, selectmode='day',
                       year=current_datetime.year, month=current_datetime.month, day=current_datetime.day,
                       date_pattern='dd/mm/yyyy',
                       bg=self.calendar_bg_color, fg=self.calendar_fg_color,
                       headersbackground=self.calendar_header_color, headersforeground=self.calendar_fg_color,
                       normalbackground=self.calendar_bg_color, normalforeground=self.calendar_fg_color,
                       weekendbackground=self.calendar_bg_color, weekendforeground=self.calendar_fg_color,
                       othermonthforeground=self.fg_color, othermonthbackground=self.panel_bg,
                       othermonthweforeground=self.fg_color, othermonthwebackground=self.panel_bg,
                       selectbackground=self.calendar_selected_day_color, selectforeground="white",
                       tooltipfg="black", bordercolor=self.border_color,
                       font=self.font_small)
        cal.pack()

        # Spinboxes para selección de hora
        time_frame = ttk.Frame(dialog, style='TFrame')
        time_frame.pack(pady=5)

        tk.Label(time_frame, text="Hora:", bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=5)
        hour_var = tk.StringVar(value=str(current_datetime.hour).zfill(2))
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, wrap=True, width=3,
                                   textvariable=hour_var, font=self.font_normal, justify='center')
        hour_spinbox.pack(side=tk.LEFT, padx=2)

        tk.Label(time_frame, text=":", bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT)

        minute_var = tk.StringVar(value=str(current_datetime.minute).zfill(2))
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, wrap=True, width=3,
                                     textvariable=minute_var, font=self.font_normal, justify='center')
        minute_spinbox.pack(side=tk.LEFT, padx=2)

        def save_schedule():
            selected_date_str = cal.get_date()
            try:
                # tkcalendar devuelve la fecha en 'dd/mm/yyyy'
                selected_date_obj = datetime.strptime(selected_date_str, "%d/%m/%Y").date()
            except ValueError:
                selected_date_obj = datetime.strptime(selected_date_str, "%d/%m/%y").date() # Fallback

            hour = int(hour_var.get())
            minute = int(minute_var.get())

            final_datetime = datetime(selected_date_obj.year, selected_date_obj.month, selected_date_obj.day, hour, minute)
            full_datetime_str = final_datetime.strftime("%Y-%m-%d %H:%M")

            if event_id is None: # Si es una nueva tarea
                success, msg = self.notes_manager.add_calendar_event(note_title, task_line, full_datetime_str, 60) # Duración por defecto 60 min
            else: # Si es una edición
                success, msg = self.notes_manager.update_calendar_event(event_id, new_start_datetime_str=full_datetime_str)

            messagebox.showinfo("Programar Tarea" if event_id is None else "Editar Tarea", msg, parent=dialog)

            if success:
                # Si el calendario ya está abierto, actualízalo
                if self.master.winfo_exists(): # Check if calendar window is still open
                    self.update_calendar_view()

            dialog.destroy()

        # Botón de 'Guardar' añadido
        ttk.Button(dialog, text="Guardar", command=save_schedule).pack(pady=10)
        dialog.wait_window(dialog)

# --- Interfaz Gráfica de Notas ---
class NotesApp:
    def __init__(self, master, notes_manager, calendar_app_instance=None):
        self.master = master
        master.title("Gestor de Notas")
        master.geometry("600x600")

        self.notes_manager = notes_manager
        self.active_note_title = None
        self.display_mode = "role"
        self.calendar_app_instance = calendar_app_instance

        # Colores
        self.bg_color = "#2E2E2E"
        self.fg_color = "#F5F5F5"
        self.panel_bg = "#3A3A3A"
        self.accent_color = "#007AFF"
        self.text_input_bg = "#444444"
        self.border_color = "#555555"

        # Fuentes
        self.font_bold = ("Helvetica Neue", 11, "bold")
        self.font_normal = ("Helvetica Neue", 10)
        self.font_small = ("Helvetica Neue", 10)
        self.font_code = ("Menlo", 11)

        # Crea el objeto Style solo una vez
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            self.style.theme_use('alt')

        self.role_colors = {
            "Programador": "#D270DB",
            "Social": "#00bcd4",
            "Tesista": "#43aa8b",
            "General": "#90be6d",
            "Asistente": "#f9c74f",
            "Work-out": "#f8961e",
            "Estudiante": "#f3722c",
            "Diseñador": "#f94144"
        }

        self.eisenhower_tag_colors = {
            "EISENHOWER_HACER_AHORA": "#FF6B6B",
            "EISENHOWER_PLANIFICAR": "#6B9BFF",
            "EISENHOWER_DELEGAR": "#FFB86B",
            "EISENHOWER_ELIMINAR": "#A0A0A0"
        }

        self.selected_roles = set()
        self.selected_eisenhowers = set()
        self.theme_mode = "dark"

        self.setup_ui()
        self.load_notes_list()

    def setup_ui(self):
        # Destruir todos los widgets existentes antes de recrear la UI
        for widget in self.master.winfo_children():
            widget.destroy()

        self.master.config(bg=self.bg_color)

        # Solo actualiza colores, NO fuentes ni crees self.style de nuevo
        self.style.configure('.', background=self.bg_color, foreground=self.fg_color)
        self.style.configure('TFrame', background=self.panel_bg)
        self.style.configure('TButton',
                             background=self.panel_bg,
                             foreground=self.fg_color,
                             borderwidth=0,
                             focusthickness=0,
                             relief="flat",
                             padding=[5, 2])
        self.style.map('TButton',
                        background=[('active', self.accent_color)],
                        foreground=[('active', 'white')])

        # --- Paneles principales ---
        main_pane = tk.PanedWindow(self.master, orient=tk.HORIZONTAL, bg=self.bg_color, sashrelief=tk.RAISED)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)  # Padding reducido

        # Left Frame (Sidebar)
        left_frame = ttk.Frame(main_pane, style='TFrame', padding=(5, 5, 5, 5))  # Padding reducido
        main_pane.add(left_frame, width=300)  # Ancho fijo para el panel izquierdo

        tk.Label(left_frame, text="Notas", font=("Helvetica Neue", 11, "bold"), bg=self.panel_bg, fg=self.fg_color).pack(pady=(0, 5))

        # Estilo para Treeview (ventana de selección de notas)
        self.style.configure("Custom.Treeview",
                             background=self.panel_bg,
                             foreground=self.fg_color,
                             fieldbackground=self.panel_bg,
                             bordercolor=self.border_color,
                             font=self.font_normal)
        self.style.map("Custom.Treeview",
                       background=[('selected', self.accent_color)],
                       foreground=[('selected', 'white')])
        self.style.configure("Custom.Treeview.Heading",
                             background=self.panel_bg,
                             foreground=self.fg_color,
                             font=self.font_bold)

        # Reemplaza el Listbox por un Treeview para jerarquía
        self.notes_tree = ttk.Treeview(left_frame, show="tree", selectmode="browse", style="Custom.Treeview")
        self.notes_tree.pack(pady=2, fill=tk.BOTH, expand=True)
        self.notes_tree.bind("<<TreeviewSelect>>", self.on_note_tree_select)

        # Botones de gestión de notas en el panel izquierdo
        button_frame_left = ttk.Frame(left_frame, style='TFrame')
        button_frame_left.pack(fill=tk.X, pady=3)
        ttk.Button(button_frame_left, text="Recargar", command=self.load_notes_list).pack(side=tk.TOP, fill=tk.X, pady=1)
        ttk.Button(button_frame_left, text="Nueva Nota", command=self.create_new_note).pack(side=tk.TOP, fill=tk.X, pady=1)
        ttk.Button(button_frame_left, text="Calendario", command=self.open_calendar_window).pack(side=tk.TOP, fill=tk.X, pady=3)
        ttk.Button(button_frame_left, text="Configurar Roles", command=self.open_roles_config_dialog).pack(side=tk.TOP, fill=tk.X, pady=1)

        # Right Frame (Main Content Area)
        right_frame = ttk.Frame(main_pane, style='TFrame', padding=(5, 5, 5, 5))
        main_pane.add(right_frame)

        # Botones de color arriba
        show_all_frame = ttk.Frame(right_frame, style='TFrame')
        show_all_frame.pack(pady=(0, 5), fill=tk.X)
        tk.Label(show_all_frame, text="Mostrar Todo:", font=self.font_small, bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=2)
        ttk.Button(show_all_frame, text="Rol", command=lambda: self.set_display_mode("role")).pack(side=tk.LEFT, padx=2)
        ttk.Button(show_all_frame, text="Eisenhower", command=lambda: self.set_display_mode("eisenhower")).pack(side=tk.LEFT, padx=2)

        tk.Label(right_frame, text="Contenido de la Nota", font=("Helvetica Neue", 11, "bold"), bg=self.panel_bg, fg=self.fg_color).pack(pady=(0, 5))

        self.note_content_display = scrolledtext.ScrolledText(right_frame, wrap=tk.WORD, font=self.font_code,
                                                               bg=self.text_input_bg, fg=self.fg_color,
                                                               insertbackground=self.fg_color,
                                                               highlightbackground=self.border_color, highlightthickness=1,
                                                               bd=0, relief="flat", padx=5, pady=5, height=10)
        self.note_content_display.pack(pady=2, fill=tk.BOTH, expand=True)

        for role, color in self.role_colors.items():
            self.note_content_display.tag_config(role, foreground=color)
        for tag, color in self.eisenhower_tag_colors.items():
            self.note_content_display.tag_config(tag, foreground=color)
        self.note_content_display.tag_config("general_text", foreground=self.fg_color)

        ttk.Button(right_frame, text="Guardar", command=self.save_current_note).pack(pady=2, fill=tk.X)
        ttk.Button(right_frame, text="Programar en Calendario", command=self.schedule_task_in_calendar).pack(pady=2, fill=tk.X)

        # Filter Frames
        filter_role_frame = ttk.Frame(right_frame, style='TFrame')
        filter_role_frame.pack(pady=(5, 2), fill=tk.X)
        tk.Label(filter_role_frame, text="Filtrar por Rol:", font=self.font_small, bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=2)

        self.role_buttons = {}
        for role in self.notes_manager.valid_roles:
            btn_color = self.role_colors.get(role, self.fg_color)
            style_name = f'Role.{role}.TButton'
            self.style.configure(style_name, background=self.panel_bg, foreground=btn_color)
            self.style.map(style_name,
                            background=[('active', self.accent_color)],
                            foreground=[('active', 'white')])
            btn = ttk.Button(filter_role_frame, text=role, command=lambda r=role: self.toggle_role_filter(r),
                             style=style_name)
            btn.pack(side=tk.LEFT, padx=1)
            self.role_buttons[role] = btn

        filter_eisenhower_frame = ttk.Frame(right_frame, style='TFrame')
        filter_eisenhower_frame.pack(pady=2, fill=tk.X)
        tk.Label(filter_eisenhower_frame, text="Filtrar Eisenhower:", font=self.font_small, bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=2)

        for abbr, category_key in self.notes_manager.eisenhower_abbreviations.items():
            category_name = self.notes_manager.eisenhower_categories[category_key]
            btn_text = f"{category_name.split(',')[0]} (E:{abbr})"
            tag_name_for_color = "EISENHOWER_" + category_key
            btn_color = self.eisenhower_tag_colors.get(tag_name_for_color, self.fg_color)
            style_name = f'Eisenhower.{category_key}.TButton'
            self.style.configure(style_name, background=self.panel_bg, foreground=btn_color)
            self.style.map(style_name,
                            background=[('active', self.accent_color)],
                            foreground=[('active', 'white')])
            btn = ttk.Button(
                filter_eisenhower_frame,
                text=btn_text,
                command=lambda c=category_key: self.toggle_eisenhower_filter(c),
                style=style_name
            )
            btn.pack(side=tk.LEFT, padx=1)
            if not hasattr(self, 'eisenhower_buttons'):
                self.eisenhower_buttons = {}
            self.eisenhower_buttons[category_key] = btn

        ttk.Button(filter_eisenhower_frame, text="Ejemplo", command=self.show_eisenhower_example).pack(side=tk.LEFT, padx=2)

        # --- Botones para cambiar tema ---
        theme_frame = ttk.Frame(right_frame, style='TFrame')
        theme_frame.pack(pady=(0, 5), fill=tk.X)
        ttk.Button(theme_frame, text="Tema Claro", command=lambda: self.set_theme("light")).pack(side=tk.LEFT, padx=2)
        ttk.Button(theme_frame, text="Tema Oscuro", command=lambda: self.set_theme("dark")).pack(side=tk.LEFT, padx=2)

    def load_notes_list(self):
        self.notes_tree.delete(*self.notes_tree.get_children())
        hierarchy = self.notes_manager.list_notes_hierarchy()
        node_map = {}

        # Primero, agrega los padres (carpetas raíz)
        for parent, children in hierarchy.items():
            if parent == "":
                for note in children:
                    node_map[note] = self.notes_tree.insert("", "end", text=note, values=(note,))
            else:
                # Asegura que el padre esté creado
                parent_node = node_map.get(parent)
                if not parent_node:
                    parent_node = self.notes_tree.insert("", "end", text=parent, open=True)
                    node_map[parent] = parent_node
                for note in children:
                    node_map[f"{parent}/{note}"] = self.notes_tree.insert(parent_node, "end", text=note, values=(f"{parent}/{note}",))

    def create_new_note(self):
        title = simpledialog.askstring("Crear Nota", "Introduce el título de la nueva nota:",
                                         parent=self.master, bg=self.panel_bg, fg=self.fg_color,
                                         font=self.font_normal)
        if title:
            success, message = self.notes_manager.create_note(title.strip())
            messagebox.showinfo("Crear Nota", message, parent=self.master)
            if success:
                self.load_notes_list()

    def on_note_tree_select(self, event):
        selected = self.notes_tree.selection()
        if selected:
            item = self.notes_tree.item(selected[0])
            # Si el ítem no tiene 'values', es una carpeta/padre
            if not item['values']:
                # Deselecciona el ítem para evitar confusión visual
                self.notes_tree.selection_remove(selected[0])
                return
            note_path = item['values'][0]
            self.active_note_title = note_path
            self.show_all_content()

    def display_content(self, content_lines_with_tags):
        """
        Muestra el contenido en el ScrolledText, aplicando colores según los tags.
        Si hay varios roles, colorea cada prefijo [Rol] con su color.
        Si se está filtrando, colorea toda la línea con el tag recibido.
        """
        self.note_content_display.config(state=tk.NORMAL)
        self.note_content_display.delete(1.0, tk.END)

        for line, tag in content_lines_with_tags:
            # Si estamos filtrando (el tag no es "general_text"), colorea toda la línea con ese tag
            if tag != "general_text":
                self.note_content_display.insert(tk.END, line + "\n", tag)
                continue

            temp_line = line
            # Detectar y colorear todos los roles al inicio
            while True:
                found = False
                for role in self.notes_manager.valid_roles:
                    prefix = f"[{role}]"
                    if temp_line.startswith(prefix):
                        self.note_content_display.insert(tk.END, prefix, role)
                        temp_line = temp_line[len(prefix):]
                        found = True
                        break
                if not found:
                    break
            # Detectar y colorear la categoría Eisenhower si está presente
            eisenhower_tag = None
            for abbr, key in self.notes_manager.eisenhower_abbreviations.items():
                prefix = f"[E:{abbr}]"
                if temp_line.startswith(prefix):
                    eisenhower_tag = "EISENHOWER_" + key
                    self.note_content_display.insert(tk.END, prefix, eisenhower_tag)
                    temp_line = temp_line[len(prefix):]
                    break
            # El resto de la línea: color del primer rol, o Eisenhower, o general
            tag_to_apply = "general_text"
            detected = self.notes_manager.get_line_classification(line)
            for d_type, d_name in detected:
                if d_type == "role":
                    tag_to_apply = d_name
                    break
                elif d_type == "eisenhower" and tag_to_apply == "general_text":
                    tag_to_apply = "EISENHOWER_" + d_name
            self.note_content_display.insert(tk.END, temp_line + "\n", tag_to_apply)

    def set_display_mode(self, mode):
        """
        Establece el modo de visualización para "Mostrar Todo".
        'mode' puede ser "role" o "eisenhower".
        Al seleccionar, limpia los filtros de rol y eisenhower.
        """
        self.display_mode = mode

        # Limpiar filtros de roles
        for role in self.selected_roles.copy():
            self.role_buttons[role].configure(style=f'Role.{role}.TButton')
        self.selected_roles.clear()

        # Limpiar filtros de eisenhower
        for category_key in self.selected_eisenhowers.copy():
            self.eisenhower_buttons[category_key].configure(style=f'Eisenhower.{category_key}.TButton')
        self.selected_eisenhowers.clear()

        self.show_all_content()

    def show_all_content(self):
        if not self.active_note_title:
            self.display_content([("Selecciona una nota para ver su contenido.", "general_text")])
            return

        content, msg = self.notes_manager.get_note_content(self.active_note_title)
        if content is not None:  # Cambia aquí: permite cadena vacía
            lines = content.split('\n')
            display_data = []
            for line in lines:
                detected_classifications = self.notes_manager.get_line_classification(line)

                tag_to_apply = "general_text"

                if self.display_mode == "role":
                    for d_type, d_name in detected_classifications:
                        if d_type == "role":
                            tag_to_apply = d_name
                            break
                        elif d_type == "eisenhower" and tag_to_apply == "general_text":
                            tag_to_apply = "EISENHOWER_" + d_name
                elif self.display_mode == "eisenhower":
                    for d_type, d_name in detected_classifications:
                        if d_type == "eisenhower":
                            tag_to_apply = "EISENHOWER_" + d_name
                            break
                        elif d_type == "role" and tag_to_apply == "general_text":
                            tag_to_apply = d_name

                display_data.append((line, tag_to_apply))
            self.display_content(display_data)
        else:
            messagebox.showerror("Error al Cargar Nota", msg, parent=self.master)
            self.display_content([(msg, "general_text")])

    def save_current_note(self):
        if not self.active_note_title:
            messagebox.showwarning("Guardar Nota", "No hay una nota seleccionada para guardar.", parent=self.master)
            return

        current_content = self.note_content_display.get(1.0, tk.END).strip()

        success, message = self.notes_manager.save_note_content(self.active_note_title, current_content)
        if success:
            messagebox.showinfo("Guardar Nota", message, parent=self.master)
            self.show_all_content()
        else:
            messagebox.showerror("Guardar Nota", message, parent=self.master)

    def filter_note(self, classification_type, classification_name):
        if not self.active_note_title:
            messagebox.showwarning("Filtrar Nota", "Por favor, selecciona una nota primero.", parent=self.master)
            return

        filtered_lines_with_tags, msg = self.notes_manager.filter_note_by_classification(self.active_note_title, classification_type, classification_name)

        if filtered_lines_with_tags:
            self.display_content(filtered_lines_with_tags)
        else:
            messagebox.showinfo("Filtrar Nota", msg, parent=self.master)
            self.display_content([(msg, "general_text")])

    def show_eisenhower_example(self):
        example_text = """
        Ejemplos para la Matriz de Eisenhower:

        [E:HA] Tarea crítica, fecha límite inminente.
        (Urgente e Importante - Color: Rojo)

        [E:P] Proyecto a largo plazo, sin prisa inmediata.
        (Importante, no Urgente - Color: Azul Claro)

        [E:D] Reunión de rutina que otro puede atender.
        (Urgente, no Importante - Color: Naranja)

        [E:E] Actividad que no aporta valor o puede posponerse indefinidamente.
        (No Urgente, no Importante - Color: Gris)
        """
        messagebox.showinfo("Ejemplo Matriz de Eisenhower", example_text, parent=self.master)

    def schedule_task_in_calendar(self):
        if not self.active_note_title:
            messagebox.showwarning("Programar Tarea", "Selecciona una nota primero.", parent=self.master)
            return

        # Obtener la línea actual del cursor
        try:
            line_index = self.note_content_display.index(tk.INSERT + " linestart")
            line_text = self.note_content_display.get(line_index, line_index + " lineend").strip()
            if not line_text:
                messagebox.showwarning("Programar Tarea", "El cursor no está en una línea válida para programar.", parent=self.master)
                return
        except Exception:
            messagebox.showwarning("Programar Tarea", "Haz clic en la línea que deseas programar.", parent=self.master)
            return

        # Llama al método auxiliar para abrir el diálogo del calendario
        # Se asegura de que la instancia del calendario exista
        if not (self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists()):
            self.open_calendar_window() # Abre la ventana del calendario si no está abierta
            # Pequeña espera para que la ventana se cree antes de intentar usarla
            self.master.update_idletasks()

        self.calendar_app_instance._open_schedule_dialog(self.active_note_title, line_text)

    def open_calendar_window(self):
        if self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists():
            self.calendar_app_instance.master.lift()
        else:
            calendar_root = Toplevel(self.master)
            self.calendar_app_instance = CalendarApp(calendar_root, self.notes_manager)
            calendar_root.protocol("WM_DELETE_WINDOW", self._on_calendar_window_close)

    def _on_calendar_window_close(self):
        """Maneja el cierre de la ventana del calendario."""
        if self.calendar_app_instance:
            self.calendar_app_instance.master.destroy()
            self.calendar_app_instance = None # Limpiar la referencia

    def toggle_role_filter(self, role):
        if role in self.selected_roles:
            self.selected_roles.remove(role)
            self.role_buttons[role].configure(style=f'Role.{role}.TButton')
        else:
            self.selected_roles.add(role)
            # Cambia el fondo para indicar selección
            selected_style = f'Role.{role}.Selected.TButton'
            self.style.configure(selected_style, background=self.accent_color, foreground='white')
            self.role_buttons[role].configure(style=selected_style)
        self.apply_role_filters()

    def toggle_eisenhower_filter(self, category_key):
        if category_key in self.selected_eisenhowers:
            self.selected_eisenhowers.remove(category_key)
            self.eisenhower_buttons[category_key].configure(style=f'Eisenhower.{category_key}.TButton')
        else:
            self.selected_eisenhowers.add(category_key)
            selected_style = f'Eisenhower.{category_key}.Selected.TButton'
            self.style.configure(selected_style, background=self.accent_color, foreground='white')
            self.eisenhower_buttons[category_key].configure(style=selected_style)
        self.apply_role_filters()

    def apply_role_filters(self):
        if not self.active_note_title:
            self.display_content([("Selecciona una nota para ver su contenido.", "general_text")])
            return
        if not self.selected_roles and not self.selected_eisenhowers:
            self.show_all_content()
            return
        content, msg = self.notes_manager.get_note_content(self.active_note_title)
        if content:
            lines = content.split('\n')
            display_data = []
            for line in lines:
                detected_classifications = self.notes_manager.get_line_classification(line)
                matched = False
                for d_type, d_name in detected_classifications:
                    if d_type == "role" and d_name in self.selected_roles:
                        display_data.append((line, d_name))
                        matched = True
                        break
                    elif d_type == "eisenhower" and d_name in self.selected_eisenhowers:
                        display_data.append((line, "EISENHOWER_" + d_name))
                        matched = True
                        break
                # Si quieres mostrar líneas generales cuando no hay match, omite este else
            if display_data:
                self.display_content(display_data)
            else:
                self.display_content([("No se encontraron líneas para los filtros seleccionados.", "general_text")])
        else:
            self.display_content([(msg, "general_text")])

    def open_roles_config_dialog(self):
        dialog = Toplevel(self.master)
        dialog.title("Gestión de Roles")
        dialog.geometry("400x440")
        dialog.transient(self.master)
        dialog.grab_set()
        dialog.config(bg=self.panel_bg)

        tk.Label(dialog, text="Roles actuales:", bg=self.panel_bg, fg=self.fg_color, font=self.font_bold).pack(pady=5)

        roles_listbox = tk.Listbox(dialog, font=self.font_normal, bg=self.text_input_bg, fg=self.fg_color, selectbackground=self.accent_color)
        roles_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        for role in self.notes_manager.valid_roles:
            roles_listbox.insert(tk.END, role)

        entry_var = tk.StringVar()
        entry = ttk.Entry(dialog, textvariable=entry_var, foreground="black")  # Texto negro
        entry.pack(pady=5, padx=10, fill=tk.X)

        color_var = tk.StringVar(value=self.fg_color)
        color_btn = ttk.Button(dialog, text="Seleccionar color", command=lambda: choose_color())
        color_btn.pack(pady=2, padx=10, fill=tk.X)

        color_preview = tk.Label(dialog, text=" ", bg=color_var.get(), width=10, height=1, relief="ridge")
        color_preview.pack(pady=2, padx=10, fill=tk.X)

        def update_color_preview():
            color_preview.config(bg=color_var.get())

        def choose_color():
            color_code = tkinter.colorchooser.askcolor(title="Elige un color para el rol")[1]
            if color_code:
                color_var.set(color_code)
                color_btn.config(text=f"Color: {color_code}")
                update_color_preview()

        def add_role():
            new_role = entry_var.get().strip()
            new_color = color_var.get()
            if new_role and new_role not in self.notes_manager.valid_roles:
                self.notes_manager.valid_roles.append(new_role)
                self.role_colors[new_role] = new_color
                roles_listbox.insert(tk.END, new_role)
                entry_var.set("")
                color_var.set(self.fg_color)
                color_btn.config(text="Seleccionar color")
                update_color_preview()
                self.refresh_roles_ui()
            else:
                messagebox.showwarning("Rol existente", "El rol ya existe o es inválido.", parent=dialog)

        def edit_role():
            sel = roles_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            old_role = self.notes_manager.valid_roles[idx]
            new_role = entry_var.get().strip()
            new_color = color_var.get()
            if not new_role:
                messagebox.showwarning("Nombre inválido", "El nombre no puede estar vacío.", parent=dialog)
                return
            if new_role != old_role and new_role in self.notes_manager.valid_roles:
                messagebox.showwarning("Rol existente", "El rol ya existe.", parent=dialog)
                return
            # Actualiza nombre y color
            self.notes_manager.valid_roles[idx] = new_role
            roles_listbox.delete(idx)
            roles_listbox.insert(idx, new_role)
            entry_var.set("")
            # NO reinicies color_var ni color_btn aquí
            self.role_colors[new_role] = new_color
            if old_role in self.role_colors:
                del self.role_colors[old_role]
            if old_role in self.selected_roles:
                self.selected_roles.remove(old_role)
                self.selected_roles.add(new_role)
            update_color_preview()  # Previsualiza el color actual
            color_btn.config(text=f"Color: {new_color}")  # Actualiza el texto del botón
            self.refresh_roles_ui()

        def delete_role():
            sel = roles_listbox.curselection()
            if not sel:
                return
            idx = sel[0]
            role = self.notes_manager.valid_roles[idx]
            if messagebox.askyesno("Eliminar rol", f"¿Eliminar el rol '{role}'?", parent=dialog):
                del self.notes_manager.valid_roles[idx]
                roles_listbox.delete(idx)
                if role in self.selected_roles:
                    self.selected_roles.remove(role)
                if role in self.role_colors:
                    del self.role_colors[role]
                self.refresh_roles_ui()

        def move_up():
            sel = roles_listbox.curselection()
            if not sel or sel[0] == 0:
                return
            idx = sel[0]
            self.notes_manager.valid_roles[idx - 1], self.notes_manager.valid_roles[idx] = \
                self.notes_manager.valid_roles[idx], self.notes_manager.valid_roles[idx - 1]
            # Actualiza la lista visual
            roles_listbox.delete(0, tk.END)
            for role in self.notes_manager.valid_roles:
                roles_listbox.insert(tk.END, role)
            roles_listbox.selection_set(idx - 1)
            on_select(None)
            self.refresh_roles_ui()

        def move_down():
            sel = roles_listbox.curselection()
            if not sel or sel[0] == len(self.notes_manager.valid_roles) - 1:
                return
            idx = sel[0]
            self.notes_manager.valid_roles[idx + 1], self.notes_manager.valid_roles[idx] = \
                self.notes_manager.valid_roles[idx], self.notes_manager.valid_roles[idx + 1]
            # Actualiza la lista visual
            roles_listbox.delete(0, tk.END)
            for role in self.notes_manager.valid_roles:
                roles_listbox.insert(tk.END, role)
            roles_listbox.selection_set(idx + 1)
            on_select(None)
            self.refresh_roles_ui()

        btn_frame = ttk.Frame(dialog, style='TFrame')
        btn_frame.pack(pady=5)

        # Fila 1: Añadir, Editar, Eliminar (centrados)
        btn_row1 = ttk.Frame(btn_frame, style='TFrame')
        btn_row1.pack(pady=2)
        ttk.Button(btn_row1, text="Añadir", command=add_role, width=14, style='RolesDialog.TButton').pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row1, text="Editar", command=edit_role, width=14, style='RolesDialog.TButton').pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_row1, text="Eliminar", command=delete_role, width=14, style='RolesDialog.TButton').pack(side=tk.LEFT, padx=6)

        # Fila 2: Subir y Bajar (centrados debajo)
        btn_row2 = ttk.Frame(btn_frame, style='TFrame')
        btn_row2.pack(pady=2)
        ttk.Button(btn_row2, text="↑", command=move_up, width=7, style='RolesDialog.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_row2, text="↓", command=move_down, width=7, style='RolesDialog.TButton').pack(side=tk.LEFT, padx=10)

        def on_select(event):
            sel = roles_listbox.curselection()
            if sel:
                role = roles_listbox.get(sel[0])
                entry_var.set(role)
                color_var.set(self.role_colors.get(role, self.fg_color))
                color_btn.config(text=f"Color: {color_var.get()}")
                update_color_preview()
        roles_listbox.bind("<<ListboxSelect>>", on_select)

    def refresh_roles_ui(self):
        # Limpia los botones antiguos
        for btn in self.role_buttons.values():
            btn.destroy()
        self.role_buttons.clear()

        # Limpia todos los widgets hijos del frame de filtros de roles (incluyendo el label)
        for widget in self.filter_role_frame.winfo_children():
            widget.destroy()

        # Vuelve a poner el label
        tk.Label(self.filter_role_frame, text="Filtrar por Rol:", font=self.font_small, bg=self.panel_bg, fg=self.fg_color).pack(side=tk.LEFT, padx=2)

        self.selected_roles.clear()

        # Crea los nuevos botones de roles en el frame correcto
        for role in self.notes_manager.valid_roles:
            btn_color = self.role_colors.get(role, self.fg_color)
            style_name = f'Role.{role}.TButton'
            self.style.configure(style_name, background=self.panel_bg, foreground=btn_color)
            self.style.map(style_name,
                            background=[('active', self.accent_color)],
                            foreground=[('active', 'white')])
            btn = ttk.Button(self.filter_role_frame, text=role, command=lambda r=role: self.toggle_role_filter(r),
                             style=style_name)
            btn.pack(side=tk.LEFT, padx=1)
            self.role_buttons[role] = btn

        self.show_all_content()

# --- Aplicación Principal (para lanzar ambas ventanas) ---
class MainApplication:
    def __init__(self, master):
        self.master = master
        master.title("Gestor de Notas Maestro")
        master.withdraw() # Oculta la ventana principal, ya que usaremos Toplevels

        self.notes_manager = NotesManager() # Instancia única de NotesManager

        self.calendar_app_instance = None # Para mantener la referencia a la ventana del calendario

        # Abrir la ventana de notas al inicio
        self.open_notes_window()

    def open_notes_window(self):
        notes_root = Toplevel(self.master)
        notes_root.state('zoomed')
        # Pasar la instancia del calendario si ya existe
        self.notes_app_instance = NotesApp(notes_root, self.notes_manager, self.calendar_app_instance)

        # Actualizar la referencia del calendario si NotesApp la crea
        if self.calendar_app_instance:
            self.notes_app_instance.calendar_app_instance = self.calendar_app_instance

        notes_root.protocol("WM_DELETE_WINDOW", self._on_notes_window_close)


    def open_calendar_window(self):
        if self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists():
            self.calendar_app_instance.master.lift()
        else:
            calendar_root = Toplevel(self.master)
            self.calendar_app_instance = CalendarApp(calendar_root, self.notes_manager)

            # Asegurarse de que NotesApp tenga la referencia correcta al calendario
            if hasattr(self, 'notes_app_instance') and self.notes_app_instance:
                self.notes_app_instance.calendar_app_instance = self.calendar_app_instance

            calendar_root.protocol("WM_DELETE_WINDOW", self._on_calendar_window_close)

    def _on_notes_window_close(self):
        if self.notes_app_instance:
            self.notes_app_instance.master.destroy()
            self.notes_app_instance = None
        # Si ambas ventanas se cierran, salir completamente
        self._check_and_quit()

    def _on_calendar_window_close(self):
        if self.calendar_app_instance:
            self.calendar_app_instance.master.destroy()
            self.calendar_app_instance = None
        self._check_and_quit()

    def _check_and_quit(self):
        # Verifica si ambas ventanas Toplevel se han cerrado
        notes_open = (self.notes_app_instance and self.notes_app_instance.master.winfo_exists())
        calendar_open = (self.calendar_app_instance and self.calendar_app_instance.master.winfo_exists())

        if not (notes_open or calendar_open):
            self.master.quit() # Cierra el proceso principal de Tkinter

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()