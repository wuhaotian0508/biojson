from __future__ import annotations


def test_personal_library_service_delegates_file_operations():
    from nutrimaster.rag.personal_library import PersonalLibraryService

    class FakeLibrary:
        def __init__(self):
            self.calls = []

        def upload_pdf(self, file_storage, filename):
            self.calls.append(("upload", file_storage, filename))
            return {"num_chunks": 2}

        def list_files(self):
            self.calls.append(("list",))
            return [{"filename": "paper.pdf"}]

        def delete_file(self, filename):
            self.calls.append(("delete", filename))
            return True

        def rename_file(self, filename, new_name):
            self.calls.append(("rename", filename, new_name))
            return True

    library = FakeLibrary()
    service = PersonalLibraryService(library)

    assert service.upload_pdf("file-object", "paper.pdf") == {"num_chunks": 2}
    assert service.list_files() == [{"filename": "paper.pdf"}]
    assert service.delete_file("paper.pdf") is True
    assert service.rename_file("paper.pdf", "renamed.pdf") is True
    assert library.calls == [
        ("upload", "file-object", "paper.pdf"),
        ("list",),
        ("delete", "paper.pdf"),
        ("rename", "paper.pdf", "renamed.pdf"),
    ]


def test_personal_library_service_delegates_search():
    from nutrimaster.rag.personal_library import PersonalLibraryService

    class FakeLibrary:
        def search(self, query_embedding, top_k=5):
            return [{"title": "paper", "score": 0.9, "embedding": query_embedding, "top_k": top_k}]

    service = PersonalLibraryService(FakeLibrary())

    assert service.search([0.1, 0.2], top_k=3) == [
        {"title": "paper", "score": 0.9, "embedding": [0.1, 0.2], "top_k": 3}
    ]
