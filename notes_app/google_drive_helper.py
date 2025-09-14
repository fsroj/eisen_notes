# Utilidades para subir, descargar y listar notas en Google Drive
# Requiere: pip install pydrive

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class GoogleDriveHelper:
    def __init__(self):
        self.gauth = GoogleAuth()
        self.gauth.LocalWebserverAuth()  # Abre navegador para autenticación
        self.drive = GoogleDrive(self.gauth)

    def upload_note(self, filename, content):
        file = self.drive.CreateFile({'title': filename})
        file.SetContentString(content)
        file.Upload()
        return file['id']

    def list_notes(self):
        # Buscar todos los archivos no eliminados y filtrar los que terminan en .md
        file_list = self.drive.ListFile({'q': "trashed=false"}).GetList()
        return [(f['title'], f['id']) for f in file_list if f['title'].lower().endswith('.md')]

    def download_note(self, file_id):
        file = self.drive.CreateFile({'id': file_id})
        file.FetchMetadata(fields='title')
        file.FetchContent()
        return file['title'], file.GetContentString()
