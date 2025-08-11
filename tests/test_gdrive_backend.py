import pytest

from backend.app.services.gdrive_backend import GoogleDriveStorageBackend


class DummyDrive:
    def __init__(self):
        self.files_created = []
        self.files_content = {}
    def files(self):
        return self
    def create(self, body, media_body, fields):
        # Simule la création d’un fichier
        file_id = f"dummy_{body['name']}"
        self.files_created.append(file_id)
        self.files_content[file_id] = media_body._fd.getvalue()
        # Correction : Resp hérite de dict, possède status et content-location
        class Resp(dict):
            def __init__(self):
                super().__init__()
                self.status = 200
                self["content-location"] = f"mock://{file_id}"
            def execute(self_inner):
                return {"id": file_id}
        return Resp()
    def get_media(self, fileId):
        # Mock complet pour MediaIoBaseDownload
        class DummyProgress:
            def __init__(self):
                self.progress = 1.0
        class DummyHttp:
            def request(self_inner, uri, method, *args, **kwargs):
                class Resp(dict):
                    def __init__(self):
                        super().__init__()
                        self.status = 200
                        self["content-location"] = uri
                return Resp(), self.files_content[fileId]
        class Req:
            def __init__(self_inner):
                self_inner.fileId = fileId
                self_inner.uri = f"mock://{fileId}"
                self_inner.headers = {}
                self_inner.http = DummyHttp()
            def next_chunk(self_inner):
                # Simule un chunk téléchargé (status, done)
                return (DummyProgress(), True)
            def read(self_inner):
                return self.files_content[fileId]
        return Req()

@pytest.fixture
def gdrive_backend(monkeypatch):
    # Patch le build pour retourner DummyDrive
    monkeypatch.setattr("backend.app.services.gdrive_backend.build", lambda *a, **kw: DummyDrive())
    # Patch Credentials
    monkeypatch.setattr("backend.app.services.gdrive_backend.service_account.Credentials", type("DummyCreds", (), {"from_service_account_file": lambda *a, **kw: None}))
    # Patch Path.exists pour toujours retourner True
    monkeypatch.setattr("backend.app.services.gdrive_backend.Path.exists", lambda self: True)
    return GoogleDriveStorageBackend("/tmp/dummy.json", "dummy_folder")

def test_store_and_read_text(gdrive_backend):
    data = b"<h1>GDrive Test</h1>"
    file_id = gdrive_backend.store_bytes(data, filename="test.html", content_type="text/html")
    assert file_id.startswith("dummy_test.html")
    text = gdrive_backend.read_text(file_id)
    assert "GDrive Test" in text
    # Vérifie que le texte est bien lu depuis le mock
