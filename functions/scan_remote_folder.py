import os
from typing import Optional

from requests import RequestException

from classes.synchronizer import Synchronizer


def scan_remote_folder(
    synchronizer: Synchronizer, remote_data: dict, dir_path: Optional[str] = None
):
    try:
        if dir_path:
            response = synchronizer.get_info(
                os.path.normpath(os.getenv("YA_DISK_PATH") + dir_path)
            ).json()["_embedded"]["items"]
        else:
            response = synchronizer.get_info().json()["_embedded"]["items"]
    except RequestException:
        return

    prefix = os.getenv("YA_DISK_PATH_PREFIX")
    dirs = []
    for item in response:
        if item["type"] == "dir":
            remote_data["dirs"].append(item["path"].replace(prefix, "/") + "/")
            dirs.append(item["path"].replace(prefix, "/") + "/")
        elif item["type"] == "file":
            remote_data["files"][item["path"].replace(prefix, "")] = {
                "md5": item["md5"],
                "mod_time": item["modified"],
            }
    for dir in dirs:
        scan_remote_folder(synchronizer, remote_data, dir)
