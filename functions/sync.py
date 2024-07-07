import os
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from loguru import logger
from requests.exceptions import RequestException

from classes.synchronizer import Synchronizer
from functions.scan_local_folder import scan_folder
from functions.scan_remote_folder import scan_remote_folder


def sync(synchronizer: Synchronizer) -> None:
    """
    Synchronise local and remote sync directory
    """
    sync_root = os.getenv("YA_DISK_PATH")
    try:
        synchronizer.get_info().json()["_embedded"]["items"]
    except RequestException:
        logger.error("Can't get remote directory info from server. Synchronisation aborted.")
        return

    remote_data = {"files": {}, "dirs": []}
    scan_remote_folder(synchronizer, remote_data)
    local_data = scan_folder()

    pool = ThreadPool(processes=cpu_count())

    for dir in local_data["dirs"]:
        if dir not in remote_data["dirs"]:
            pool.apply_async(
                synchronizer.create_folder, (os.path.normpath(sync_root + dir),)
            )
    for file in local_data["files"]:
        if (
            file not in remote_data["files"]
            or local_data["files"][file]["md5"] != remote_data["files"][file]["md5"]
        ):
            pool.apply_async(synchronizer.load, (file,))
    for file in remote_data["files"]:
        if file not in local_data["files"]:
            pool.apply_async(synchronizer.delete, (file,))
    for dir in remote_data["dirs"]:
        if dir not in local_data["dirs"]:
            pool.apply_async(synchronizer.delete, (dir,))
    pool.close()
    pool.join()
