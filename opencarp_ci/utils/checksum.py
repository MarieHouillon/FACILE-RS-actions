import hashlib


def get_sha256(file_path):
    m = hashlib.sha256()
    m.update(file_path.read_text().encode())
    return m.hexdigest()


def get_sha512(file_path):
    m = hashlib.sha512()
    m.update(file_path.read_text().encode())
    return m.hexdigest()
