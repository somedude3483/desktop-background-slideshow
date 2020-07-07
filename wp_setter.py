"""wp_setter.py
Uses Imgur's API Client ID key and a link to get a random image from a specified gallery
and sets it as your desktop background.
This script only works for Windows machines."""

import requests
import warnings
import platform
import random
import ctypes
import time
import sys
import os
from requests.exceptions import MissingSchema

if not sys.warnoptions:
    warnings.simplefilter("default")
_details = {"link": None, "client_id": None}


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
        raise WallPaperError("Unknown error")


class LinkError(APIError):
    """LinkError
    Problem parsing the link."""

    def __init__(self, link, real_error):
        self.link = link
        self.real_error = real_error

    def __str__(self):
        if self.link != linkify(self.link):
            return (
                f"{self.link} is not a valid Imgur API link. " \
                f"Read on built in function help(wp_setter.linkify) " \
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
        """Get links from imgur Windows Spotlight gallery"""
        response = requests.get(
            link, headers={"Authorization": f"Client-ID {client_id}"}
        )
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
                image = requests.get(class_._random_image())
            except MissingSchema as error:
                raise APIError(_details, ["link", "client_id"], None, error) from None
            wp_file.write(image.content)


def linkify(link: str = None):
    """Converts imgur link to api link"""
    if not link.endswith(".json"):
        return f"https://api.imgur.com/3/{'/'.join(link.split('/')[-2:])}.json"
    return f"https://api.imgur.com/3/{'/'.join(link.split('/')[-2:])}"


def set_new_background(*, minutes: float = 0, repeat: bool = False):
    """set_new_background(*, minutes: float=0, repeat: bool=False)
       Set a random image from the imgur link you specified as your background."""
    if minutes != 0 and not repeat:
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


if __name__ == "__main__":
    if _details["link"] is None:
        raise APIError(_details, list(_details.keys()), None, None)
    set_new_background()
