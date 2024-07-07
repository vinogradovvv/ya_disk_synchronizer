import hashlib
import os


def compute_hash(filepath: str, struct_dict: dict) -> None:
    """
    Computes md5 hash of given file and puts result in the given dict
    """
    local_path = os.getenv("LOCAL_PATH")
    full_path = os.path.normpath(local_path + filepath)
    with open(full_path, "rb") as file:
        md5 = hashlib.file_digest(file, "md5").hexdigest()
    struct_dict["files"][filepath]["md5"] = md5
