"""wp_setter.py
Uses Imgur's API Client ID key and a link to get a random image from a specified gallery
and sets it as your desktop background.
This script only works for Windows machines."""

import concurrent.futures
import threading
import requests
import warnings
import platform
import random
import ctypes
import shutil
import glob
import time
import json
import sys
import os
from requests.exceptions import MissingSchema
from requests.exceptions import ConnectionError as ConnectionError_

if not sys.warnoptions:
    warnings.simplefilter("default")
_details = {"link": None, "client_id": None}
_cache_path = {"CP": None}
_running = [False]
_bg = None


class WallpaperError(Exception):
    """WallpaperError"""


class WPSystemError(WallpaperError):
    def __init__(self, name, real_error):
        self.name = name
        self.real_error = real_error

    def __str__(self):
        if self.name in ["Linux", "Darwin"]:
            return repr(
                f"{self.name} is not a Windows version. {self.name} is not supported by the script. Error raised from {self.real_error}"
            )
        return repr(f"Unrecognized system with an RE of {self.real_error}")


class APIError(WallpaperError):
    def __init__(self, details, key, value, real_error):
        self.final_details = [details, key, value]
        self.real_error = real_error

    def __str__(self):
        con1 = self.final_details[0][self.final_details[1][0]] is self.final_details[2]
        con2 = self.final_details[0][self.final_details[1][1]] is self.final_details[2]
        if con1 and con2:
            return repr(
                " ".join(
                    [
                        f"API details must be set with the set_details() function.",
                        "Read help(wp_setter.set_details).",
                        f"Error info: details: {self.final_details[0]},",
                        f"keys: {self.final_details[1]}, value: {self.final_details[2]}",
                        f"with an RE of {self.real_error}",
                    ]
                )
            )
        raise WallpaperError("Unknown error")


class CacheError(WallpaperError):
    """CacheError
    Cache was not initialized"""

    def __init__(self, core_var, _slice, value, real_error):
        self.current_state = [core_var, _slice, value]
        self.real_error = real_error
        print(self.current_state, self.real_error)

    def __str__(self):
        if self.current_state[0][self.current_state[1]] is self.current_state[2]:
            return repr(
                f"Cache was not initialized on background call. "
                "Initialize the cache first by exeucting wp_setter.cache(filepath), "
                f"and then call the function. Called from {self.real_error}"
            )
        raise WallpaperError("Unknown Error")


class LinkError(APIError):
    """LinkError
    Problem parsing the link."""

    def __init__(self, link, real_error):
        self.link = link
        self.real_error = real_error

    def __str__(self):
        if self.link != linkify(self.link):
            return (
                f"{self.link} is not a valid Imgur API link. "
                f"Read on built in function help(wp_setter.linkify) "
                f"Raised from {self.real_error}"
            )
        return WallpaperError("Unknown error")


def set_details(*, sd_link, sd_client_id):
    """set_details(*, sd_link, sd_client_id)
    This script uses imgur's API to get images off of their site.
    To use this script, you need to specify the link of the imgur site and your client ID"""
    _details["link"] = sd_link
    _details["client_id"] = sd_client_id


class _MainFunctions:
    def _get_links(*, link, client_id):
        """Get links from the imgur gallery"""
        try:
            response = requests.get(
                link, headers={"Authorization": f"Client-ID {client_id}"}
            )

        except ConnectionError_ as error:
            raise ConnectionError from None
        try:
            resp_json = lambda x: response.json()["data"]["images"][x]["link"]

            for i in range(len(resp_json(0))):
                yield resp_json(i)
        except KeyError as error:
            raise LinkError(_details["link"], error) from None

    @classmethod
    def _random_image(class_):
        """Pick a random images from the get_links list"""
        return random.choice(
            list(
                class_._get_links(
                    link=_details["link"], client_id=_details["client_id"],
                )
            )
        )

    @classmethod
    def _make_file(class_):
        """Create image file"""
        with open("wallpaper.bmp", "wb+") as wp_file:
            try:
                try:
                    with requests.Session() as session:
                        image = session.get(class_._random_image())
                except ConnectionError_:
                    raise ConnectionError from None
        
            except MissingSchema as error:
                raise APIError(_details, ["link", "client_id"], None, error) from None
            wp_file.write(image.content)

    def _background(
    minutes: float = 10, repeat: bool = False
):
        """set_new_background(*, minutes: float=0, repeat: bool=False)
           Set a random image from the imgur link you specified as your background."""
        if minutes != 10 and not repeat:
            warnings.warn(
                "Next time if you want to enable repeat, "
                "call the function with repeat set as True. "
                "set_new_background(minutes=minutes, repeat=True)",
                DeprecationWarning,
            )
            repeat = True
        _MainFunctions._make_file()
        try:
            if repeat:
                while True:
                    ctypes.windll.user32.SystemParametersInfoW(
                        20, 0, os.path.join(os.getcwd(), "wallpaper.bmp"), 1
                    )
                    time.sleep(minutes * 60)
                    _MainFunctions._make_file()
            else:
                ctypes.windll.user32.SystemParametersInfoW(
                    20, 0, os.path.join(os.getcwd(), "wallpaper.bmp"), 1
                )
        except AttributeError as error:
            raise WPSystemError(platform.system(), error) from None

    def _offline_background(
        minutes, repeat
        ):

        with open("cache_path.json") as file:
            _cache_path = json.load(file)

        if minutes != 10 and not repeat:
            warnings.warn(
                "Next time if you want to enable repeat, "
                "call the function with repeat set as True. "
                "set_new_background(minutes=minutes, repeat=True)",
                DeprecationWarning,
            )
            repeat = True

        try:
            if repeat:
                while True:
                    with open("cache_path.json") as file:
                        ctypes.windll.user32.SystemParametersInfoW(
                            20, 0, random.choice(json.load(file)), 1
                        )
                        time.sleep(minutes * 60)
            else:
                with open("cache_path.json") as file:
                    ctypes.windll.user32.SystemParametersInfoW(
                        20, 0, random.choice(json.load(file)), 1
                    )
        except AttributeError as error:
            raise WPSystemError(platform.system(), error) from None  
        

    def _cache(filepath, limit, clear):
        start = time.time()
        if _details["client_id"] is not None:
            if clear:
                shutil.rmtree(filepath)
                return
            if not os.path.isdir(filepath):
                os.mkdir(filepath)

                for index, item in enumerate(
                    _MainFunctions._get_links(
                        link=_details["link"], client_id=_details["client_id"]
                    )
                ):
                    space = sum(
                        [
                            os.stat(item).st_size
                            for item in glob.glob(os.path.join(filepath, "*.bmp"))
                        ]
                    )
                    if space > limit:
                        _cache_path["CP"] = glob.glob(os.path.join(filepath, "*.bmp"))
                        with open("cache_path.json", "w+") as file:
                            json.dump(_cache_path["CP"], file)
                        return
                    resp = requests.get(item)
                    with open(
                        os.path.join(filepath, f"wallpaper{index}.bmp"), "wb+"
                    ) as file:
                        file.write(resp.content)
            _cache_path["CP"] = glob.glob(os.path.join(filepath, "*.bmp"))
            with open("cache_path.json", "w+") as file:
                json.dump(_cache_path["CP"], file)
            print(f"Finished in {round(time.time() - start, 3)}s")
            return
        raise APIError(_details, list(_details.keys()), None, None)


def cache(*, filepath, limit: int=100_000_000_000, clear: bool=False):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(_MainFunctions._cache, (filepath,), (limit,), (clear,))
    


def linkify(link: str = None):
    if not link.endswith(".json"):
        return f"https://api.imgur.com/3/{'/'.join(link.split('/')[-2:])}.json"
    return f"https://api.imgur.com/3/{'/'.join(link.split('/')[-2:])}"

def set_new_background(minutes: float=10, repeat: bool=False, from_cache: bool=False):
    if len(threading.enumerate()) < 3:
        if not from_cache:
            bg = threading.Thread(name="bg", target=_MainFunctions._background, args=(minutes, repeat))
            bg.start()
            return
        bg = threading.Thread(name="offline_bg", target=_MainFunctions._offline_background, args=(minutes, repeat))
        bg.start()
    return False
    
if __name__ == "__main__":
    if _details["link"] is None:
        raise APIError(_details, list(_details.keys()), None, None)
    set_new_background()
