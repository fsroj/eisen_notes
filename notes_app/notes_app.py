
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
		self.notes_listbox = tk.Listbox(self, width=30, height=20)
		self.notes_listbox.grid(row=0, column=0, rowspan=6, padx=10, pady=10, sticky="ns")
		self.notes_listbox.bind("<<ListboxSelect>>", self._on_note_selected)

		self.add_button = ttk.Button(self, text="Nueva Nota", command=self._add_note)
		self.add_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

		self.save_button = ttk.Button(self, text="Guardar Nota", command=self._save_note)
		self.save_button.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

		self.delete_button = ttk.Button(self, text="Eliminar Nota", command=self._delete_note)
		self.delete_button.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

		self.filter_button = ttk.Button(self, text="Filtrar Nota", command=self._filter_note)
		self.filter_button.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

		self.text_area = scrolledtext.ScrolledText(self, width=60, height=20, wrap=tk.WORD)
		self.text_area.grid(row=0, column=2, rowspan=6, padx=10, pady=10, sticky="nsew")

		self.grid_rowconfigure(5, weight=1)
		self.grid_columnconfigure(2, weight=1)

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
			self.text_area.delete(1.0, tk.END)
			self.text_area.insert(tk.END, content)

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
