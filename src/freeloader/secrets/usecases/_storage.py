from freeloader.secrets.storage import Storage
from freeloader.shared.system.fl import Freeloader


def load_storage() -> Storage:
    freeloader = Freeloader()
    return Storage(freeloader.secrets_folder, freeloader.session_folder)
