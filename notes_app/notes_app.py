
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, simpledialog, Toplevel



class NotesApp(ttk.Frame):

	def __init__(self, parent, notes_manager, *args, **kwargs):
		super().__init__(parent, *args, **kwargs)
		self.notes_manager = notes_manager
		self.parent = parent
		self.selected_note = None
		self._build_ui()
		self._refresh_notes_list()

	def _build_ui(self):
		# Colores Apple-like para tags
		self.role_colors = {
			"Programador": "#007AFF", "Social": "#34C759", "Tesista": "#AF52DE", "General": "#FF9500",
			"Asistente": "#FF2D55", "Work-out": "#FFCC00", "Estudiante": "#5AC8FA", "Trabajo": "#5856D6",
			"Diseñador": "#FF375F", "TLP": "#FF9F0A", "Ropa/Accesorios": "#FFD60A"
		}
		self.eisenhower_colors = {
			"HACER_AHORA": "#FF3B30", "PLANIFICAR": "#34C759", "DELEGAR": "#FF9500", "ELIMINAR": "#8E8E93"
		}
		self.type_colors = {
			"IDEA": "#5AC8FA", "PROYECTO": "#AF52DE", "TAREA": "#FFCC00"
		}

		# Lista de notas
		self.notes_listbox = tk.Listbox(self, width=30, height=20, font=("San Francisco", 13))
		self.notes_listbox.grid(row=0, column=0, rowspan=8, padx=10, pady=10, sticky="ns")
		self.notes_listbox.bind("<<ListboxSelect>>", self._on_note_selected)

		# Botones principales (a la izquierda)
		self.add_button = ttk.Button(self, text="Nueva Nota", command=self._add_note)
		self.add_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
		self.save_button = ttk.Button(self, text="Guardar Nota", command=self._save_note)
		self.save_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
		self.delete_button = ttk.Button(self, text="Eliminar Nota", command=self._delete_note)
		self.delete_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

		# Frame para colorear todo por...
		self.colorear_frame = ttk.Frame(self)
		self.colorear_frame.grid(row=1, column=2, padx=10, pady=(0,0), sticky="ew")
		ttk.Label(self.colorear_frame, text="Colorear todo por:", font=("San Francisco", 11, "bold")).pack(side=tk.LEFT, padx=2)
		ttk.Button(self.colorear_frame, text="Rol", command=self._color_all_by_role).pack(side=tk.LEFT, padx=1)
		ttk.Button(self.colorear_frame, text="Eisenhower", command=self._color_all_by_eisenhower).pack(side=tk.LEFT, padx=1)
		ttk.Button(self.colorear_frame, text="Tipo", command=self._color_all_by_type).pack(side=tk.LEFT, padx=1)

		# Área de texto con scroll
		self.text_area = scrolledtext.ScrolledText(self, width=60, height=20, wrap=tk.WORD, font=("San Francisco", 13))
		self.text_area.grid(row=2, column=2, rowspan=1, padx=10, pady=10, sticky="nsew")

		# Botones de filtro individuales para cada valor de roles (debajo del área de texto)
		self.filter_roles_frame = ttk.Frame(self)
		self.filter_roles_frame.grid(row=3, column=2, padx=10, pady=(0,0), sticky="ew")
		ttk.Label(self.filter_roles_frame, text="Filtrar por Rol:", font=("San Francisco", 11, "bold")).pack(side=tk.LEFT, padx=2)
		for role in self.role_colors:
			btn = ttk.Button(self.filter_roles_frame, text=role, command=lambda r=role: self._filter_by_role(r))
			btn.pack(side=tk.LEFT, padx=1)

		# Botones de filtro individuales para cada valor de Eisenhower (debajo del área de texto)
		self.filter_eisenhower_frame = ttk.Frame(self)
		self.filter_eisenhower_frame.grid(row=4, column=2, padx=10, pady=(0,0), sticky="ew")
		ttk.Label(self.filter_eisenhower_frame, text="Filtrar por Eisenhower:", font=("San Francisco", 11, "bold")).pack(side=tk.LEFT, padx=2)
		for key in self.eisenhower_colors:
			btn = ttk.Button(self.filter_eisenhower_frame, text=key, command=lambda k=key: self._filter_by_eisenhower(k))
			btn.pack(side=tk.LEFT, padx=1)

		# Botones de filtro individuales para cada tipo (debajo del área de texto)
		self.filter_types_frame = ttk.Frame(self)
		self.filter_types_frame.grid(row=5, column=2, padx=10, pady=(0,10), sticky="ew")
		ttk.Label(self.filter_types_frame, text="Filtrar por Tipo:", font=("San Francisco", 11, "bold")).pack(side=tk.LEFT, padx=2)
		for key in self.type_colors:
			btn = ttk.Button(self.filter_types_frame, text=key, command=lambda k=key: self._filter_by_type(k))
			btn.pack(side=tk.LEFT, padx=1)

		self.grid_rowconfigure(6, weight=1)
		self.grid_columnconfigure(2, weight=1)

		# Configurar tags de colores
		for role, color in self.role_colors.items():
			self.text_area.tag_config(f"role_{role}", foreground=color)
		for key, color in self.eisenhower_colors.items():
			self.text_area.tag_config(f"eisen_{key}", foreground=color)
		for key, color in self.type_colors.items():
			self.text_area.tag_config(f"type_{key}", foreground=color)

		self.text_area.tag_config("default", foreground="#1C1C1E")

	def _color_all_by_role(self):
		self._show_note_with_highlight_filter(self.text_area.get(1.0, tk.END), "role", None, color_all=True)

	def _color_all_by_eisenhower(self):
		self._show_note_with_highlight_filter(self.text_area.get(1.0, tk.END), "eisenhower", None, color_all=True)

	def _color_all_by_type(self):
		self._show_note_with_highlight_filter(self.text_area.get(1.0, tk.END), "type", None, color_all=True)

	def _show_note_with_highlight_filter(self, content, filter_type, filter_value, color_all=False):
		self.text_area.config(state="normal")
		self.text_area.delete(1.0, tk.END)
		lines = content.split("\n")
		for i, line in enumerate(lines):
			start = f"{i+1}.0"
			end = f"{i+1}.end"
			tag = None
			if color_all:
				if filter_type == "role":
					for role in self.role_colors:
						if f"[{role}]" in line:
							tag = f"role_{role}"
							break
				elif filter_type == "eisenhower":
					for key in self.eisenhower_colors:
						if f"[E:{key[0]}]" in line or f"[E:{key}]" in line:
							tag = f"eisen_{key}"
							break
				elif filter_type == "type":
					for key in self.type_colors:
						if f"[T:{key}]" in line:
							tag = f"type_{key}"
							break
			else:
				if filter_type == "role":
					if filter_value and f"[{filter_value}]" in line:
						tag = f"role_{filter_value}"
				elif filter_type == "eisenhower":
					if filter_value and (f"[E:{filter_value[0]}]" in line or f"[E:{filter_value}]" in line):
						tag = f"eisen_{filter_value}"
				elif filter_type == "type":
					if filter_value and f"[T:{filter_value}]" in line:
						tag = f"type_{filter_value}"
			if not color_all and tag is None:
				continue  # filtrar: no mostrar líneas no relevantes
			self.text_area.insert(tk.END, line + "\n")
			if tag:
				self.text_area.tag_add(tag, start, end)
			else:
				self.text_area.tag_add("default", start, end)
		self.text_area.config(state="normal")


	def _refresh_notes_list(self):
		self.notes_listbox.delete(0, tk.END)
		notes = self.notes_manager.list_notes()
		for note in notes:
			self.notes_listbox.insert(tk.END, note)

	def _on_note_selected(self, event=None):
		selection = self.notes_listbox.curselection()
		if not selection:
			return
		idx = selection[0]
		note_title = self.notes_listbox.get(idx)
		self.selected_note = note_title
		content, msg = self.notes_manager.get_note_content(note_title)
		if content is not None:
			self._show_note_with_highlight(content)

	def _show_note_with_highlight(self, content):
		self.text_area.config(state="normal")
		self.text_area.delete(1.0, tk.END)
		lines = content.split("\n")
		for i, line in enumerate(lines):
			start = f"{i+1}.0"
			end = f"{i+1}.end"
			tag = self._get_line_tag(line)
			self.text_area.insert(tk.END, line + "\n")
			if tag:
				self.text_area.tag_add(tag, start, end)
			else:
				self.text_area.tag_add("default", start, end)
		self.text_area.config(state="normal")

	def _get_line_tag(self, line):
		# Detecta el tag principal de la línea
		for role in self.role_colors:
			if f"[{role}]" in line:
				return f"role_{role}"
		for key in self.eisenhower_colors:
			if f"[E:{key[0]}]" in line or f"[E:{key}]" in line:
				return f"eisen_{key}"
		for key in self.type_colors:
			if f"[T:{key}]" in line:
				return f"type_{key}"
		return None

	def _show_all_roles(self):
		if not self.selected_note:
			messagebox.showinfo("Mostrar Roles", "Seleccione una nota para mostrar.")
			return
		content, _ = self.notes_manager.get_note_content(self.selected_note)
		if content:
			self._show_note_with_highlight(content)

	def _show_all_eisenhower(self):
		if not self.selected_note:
			messagebox.showinfo("Mostrar Eisenhower", "Seleccione una nota para mostrar.")
			return
		content, _ = self.notes_manager.get_note_content(self.selected_note)
		if content:
			self._show_note_with_highlight_eisenhower(content)

	def _show_note_with_highlight_eisenhower(self, content):
		self.text_area.config(state="normal")
		self.text_area.delete(1.0, tk.END)
		lines = content.split("\n")
		for i, line in enumerate(lines):
			start = f"{i+1}.0"
			end = f"{i+1}.end"
			tag = None
			for key in self.eisenhower_colors:
				if f"[E:{key[0]}]" in line or f"[E:{key}]" in line:
					tag = f"eisen_{key}"
					break
			self.text_area.insert(tk.END, line + "\n")
			if tag:
				self.text_area.tag_add(tag, start, end)
			else:
				self.text_area.tag_add("default", start, end)
		self.text_area.config(state="normal")

	def _show_all_types(self):
		if not self.selected_note:
			messagebox.showinfo("Mostrar Tipos", "Seleccione una nota para mostrar.")
			return
		content, _ = self.notes_manager.get_note_content(self.selected_note)
		if content:
			self._show_note_with_highlight_type(content)

	def _show_note_with_highlight_type(self, content):
		self.text_area.config(state="normal")
		self.text_area.delete(1.0, tk.END)
		lines = content.split("\n")
		for i, line in enumerate(lines):
			start = f"{i+1}.0"
			end = f"{i+1}.end"
			tag = None
			for key in self.type_colors:
				if f"[T:{key}]" in line:
					tag = f"type_{key}"
					break
			self.text_area.insert(tk.END, line + "\n")
			if tag:
				self.text_area.tag_add(tag, start, end)
			else:
				self.text_area.tag_add("default", start, end)
		self.text_area.config(state="normal")

	def _add_note(self):
		title = simpledialog.askstring("Nueva Nota", "Título de la nota:")
		if not title:
			return
		ok, msg = self.notes_manager.create_note(title)
		if ok:
			self._refresh_notes_list()
			messagebox.showinfo("Éxito", msg)
		else:
			messagebox.showerror("Error", msg)

	def _save_note(self):
		if not self.selected_note:
			messagebox.showinfo("Guardar Nota", "Seleccione una nota para guardar.")
			return
		content = self.text_area.get(1.0, tk.END)
		ok, msg = self.notes_manager.save_note_content(self.selected_note, content)
		if ok:
			messagebox.showinfo("Éxito", msg)
		else:
			messagebox.showerror("Error", msg)

	def _delete_note(self):
		if not self.selected_note:
			messagebox.showinfo("Eliminar Nota", "Seleccione una nota para eliminar.")
			return
		confirm = messagebox.askyesno("Confirmar", f"¿Está seguro de eliminar la nota '{self.selected_note}'?")
		if confirm:
			note_path = self.notes_manager._get_note_path(self.selected_note)
			try:
				import os
				os.remove(note_path)
				self._refresh_notes_list()
				self.text_area.delete(1.0, tk.END)
				self.selected_note = None
				messagebox.showinfo("Éxito", "Nota eliminada.")
			except Exception as e:
				messagebox.showerror("Error", f"No se pudo eliminar la nota: {e}")

	def _filter_note(self):
		if not self.selected_note:
			messagebox.showinfo("Filtrar Nota", "Seleccione una nota para filtrar.")
			return
		filter_win = Toplevel(self)
		filter_win.title("Filtrar Nota")
		filter_win.geometry("300x200")

		ttk.Label(filter_win, text="Tipo de filtro:").pack(pady=5)
		filter_type_var = tk.StringVar(value="role")
		filter_type_combo = ttk.Combobox(filter_win, textvariable=filter_type_var, values=["role", "eisenhower", "task_type"])
		filter_type_combo.pack(pady=5)

		ttk.Label(filter_win, text="Valor:").pack(pady=5)
		filter_value_var = tk.StringVar()
		filter_value_entry = ttk.Entry(filter_win, textvariable=filter_value_var)
		filter_value_entry.pack(pady=5)

		result_text = scrolledtext.ScrolledText(filter_win, width=35, height=6, wrap=tk.WORD)
		result_text.pack(pady=5)

		def do_filter():
			filter_type = filter_type_var.get()
			filter_value = filter_value_var.get()
			lines, msg = self.notes_manager.filter_note_by_classification(self.selected_note, filter_type, filter_value)
			result_text.delete(1.0, tk.END)
			if lines:
				for line, tag in lines:
					result_text.insert(tk.END, f"[{tag}] {line}\n")
			else:
				result_text.insert(tk.END, msg)

		ttk.Button(filter_win, text="Filtrar", command=do_filter).pack(pady=5)
