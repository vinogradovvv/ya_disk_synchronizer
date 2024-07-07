import json
import os
import time
from datetime import datetime
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from os.path import normpath

from functions.md5_hash import compute_hash


def scan_folder() -> dict:
    """
    Scans folder, and computes hashes if it is needs
    """
    local_path = os.getenv("LOCAL_PATH")
    scan_file = os.getenv("SCAN_FILE")
    try:
        with open(scan_file, "r") as file:
            scan_data = json.load(file)
    except FileNotFoundError:
        scan_data = {"dirs": [], "files": {}}
        for dir in os.walk(local_path):
            dir_path = dir[0].replace(local_path, "/")
            if dir_path != "/":
                scan_data["dirs"].append(dir_path + "/")
            for file in dir[2]:
                if dir_path != "/":
                    scan_data["files"][normpath(dir_path + "/" + file)[1:]] = {
                        "mod_time": time.ctime(
                            os.path.getmtime(normpath(dir[0] + "/" + file))
                        )
                    }
                else:
                    scan_data["files"][normpath(dir_path + file)[1:]] = {
                        "mod_time": time.ctime(
                            os.path.getmtime(normpath(dir[0] + "/" + file))
                        )
                    }
        pool = ThreadPool(processes=cpu_count())
        files = scan_data["files"].keys()
        for file in files:
            pool.apply_async(compute_hash, (file, scan_data))
        pool.close()
        pool.join()
        with open(scan_file, "w") as file:
            json.dump(scan_data, file, indent=4)
        return scan_data

    modified: bool = False
    deleted = {"files": [], "dirs": []}
    pool = ThreadPool(processes=cpu_count())
    for file in scan_data["files"]:
        if not os.path.exists(normpath(local_path + file)):
            modified = True
            deleted["files"].append(file)
        elif (
            datetime.strptime(
                scan_data["files"][file]["mod_time"], "%a %b %d %H:%M:%S %Y"
            )
        ) < (
            datetime.strptime(
                time.ctime(os.path.getmtime(normpath(local_path + file))),
                "%a %b %d %H:%M:%S %Y",
            )
        ):
            modified = True
            pool.apply_async(compute_hash, (file, scan_data))
    pool.close()
    pool.join()
    for dir in scan_data["dirs"]:
        if not os.path.exists(normpath(local_path + dir)):
            modified = True
            deleted["dirs"].append(dir)

    local_files = []
    local_dirs = []
    for dir in os.walk(local_path):
        dir_path = dir[0].replace(local_path, "/")
        if dir_path != "/":
            local_dirs.append(dir_path + "/")
        for file in dir[2]:
            if dir_path != "/":
                local_files.append(normpath(dir_path + "/" + file)[1:])
            else:
                local_files.append(normpath(dir_path + file)[1:])

    pool = ThreadPool(processes=cpu_count())
    for file in local_files:
        if file not in scan_data["files"].keys():
            modified = True
            scan_data["files"][file] = {
                "mod_time": time.ctime(os.path.getmtime(normpath(local_path + file)))
            }
            pool.apply_async(compute_hash, (file, scan_data))
    pool.close()
    pool.join()
    for dir in local_dirs:
        if dir not in scan_data["dirs"]:
            modified = True
            scan_data["dirs"].append(dir)

    if modified:
        for file in deleted["files"]:
            scan_data["files"].pop(file)
        for dir in deleted["dirs"]:
            scan_data["dirs"].remove(dir)
        with open(scan_file, "w") as file:
            json.dump(scan_data, file, indent=4)
    return scan_data
