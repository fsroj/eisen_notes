import os
import json
import hashlib
from datetime import datetime

class NotesManager:
    def __init__(self, notes_dir="notes", calendar_file="calendar_events.json"):
        self.notes_dir = notes_dir
        os.makedirs(self.notes_dir, exist_ok=True)
        self.calendar_file = calendar_file

        self.valid_roles = ["Programador", "Social", "Tesista", "General", "Asistente", "Work-out", "Estudiante", "Trabajo", "Diseñador", "TLP", "Ropa/Accesorios", "Cuidado"]
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
        self.task_types = {
            "IDEA": "Idea",
            "PROYECTO": "Proyecto",
            "TAREA": "Tarea"
        }
        self.task_type_prefixes_map = {f"[T:{k}]": v for k, v in self.task_types.items()}
        self.calendar_events = self._load_calendar_events()

    def _get_note_path(self, title):
        parts = [p.replace(' ', '_').lower() for p in title.split('/')]
        if len(parts) > 1:
            dir_path = os.path.join(self.notes_dir, *parts[:-1])
            os.makedirs(dir_path, exist_ok=True)
        else:
            dir_path = self.notes_dir
        return os.path.join(dir_path, f"{parts[-1]}.md")

    def create_note(self, title):
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
        notes = [f.replace('.md', '') for f in os.listdir(self.notes_dir) if f.endswith('.md')]
        return [note.replace('_', ' ').title() for note in notes]

    def list_notes_hierarchy(self):
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
        original_line = line_text.strip()
        remaining_line = original_line
        classifications = []
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
        for prefix, key in self.eisenhower_prefixes_map.items():
            if remaining_line.startswith(prefix):
                classifications.append(("eisenhower", key))
                remaining_line = remaining_line[len(prefix):].strip()
                break
        for prefix, key in self.task_type_prefixes_map.items():
            if remaining_line.startswith(prefix):
                classifications.append(("task_type", key))
                remaining_line = remaining_line[len(prefix):].strip()
                break
        if not classifications and original_line:
            return [("general_text", None)]
        return classifications

    def filter_note_by_classification(self, title, classification_type, classification_name):
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
                elif detected_type == "task_type" and detected_name == classification_name and classification_type == "task_type":
                    found_match = True
                    primary_tag_to_display = "TASK_TYPE_" + detected_name
                    break
                elif detected_type == "general_text":
                    primary_tag_to_display = "general_text"
            if found_match:
                filtered_lines_with_tags.append((line_stripped, primary_tag_to_display))
        if not filtered_lines_with_tags:
            return [], f"No se encontraron líneas para '{classification_name}' en esta nota."
        return filtered_lines_with_tags, "Filtrado exitoso."

    def _load_calendar_events(self):
        if os.path.exists(self.calendar_file):
            with open(self.calendar_file, 'r', encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return []
        return []

    def _save_calendar_events(self):
        with open(self.calendar_file, 'w', encoding="utf-8") as f:
            json.dump(self.calendar_events, f, indent=4)

    def add_calendar_event(self, note_title, line_text, start_datetime_str, duration_minutes):
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
        events_for_date = []
        for event in self.calendar_events:
            event_date_str = event['start_datetime'].split(' ')[0]
            if event_date_str == target_date_str:
                events_for_date.append(event)
        events_for_date.sort(key=lambda x: datetime.strptime(x['start_datetime'], "%Y-%m-%d %H:%M"))
        return events_for_date

    def update_calendar_event(self, event_id, new_start_datetime_str=None, new_duration_minutes=None):
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
        initial_len = len(self.calendar_events)
        self.calendar_events = [event for event in self.calendar_events if event['id'] != event_id]
        if len(self.calendar_events) < initial_len:
            self._save_calendar_events()
            return True, "Evento eliminado."
        return False, "Evento no encontrado."
        
    def is_note_empty(self, title):
        content, _ = self.get_note_content(title)
        if not content or content.strip() == f"# {title}\n" or content.strip() == f"# {title}":
            return True
        return False