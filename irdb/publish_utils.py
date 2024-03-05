# -*- coding: utf-8 -*-
"""
Copied directly from ScopeSim. This is obviously not ideal and should use some
form of common sub-package to deal with this...
"""
import re
import logging
from datetime import date
from typing import List, Tuple, Set, Dict
from collections.abc import Iterator, Iterable, Mapping

from more_itertools import first, last, groupby_transform

import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import bs4

from scopesim import rc
# from .download_utils import initiate_download, handle_download, handle_unzipping

_GrpVerType = Mapping[str, Iterable[str]]
_GrpItrType = Iterator[Tuple[str, List[str]]]


HTTP_RETRY_CODES = [403, 404, 429, 500, 501, 502, 503]


class ServerError(Exception):
    """Some error with the server or connection to the server."""


def get_server_folder_contents(dir_name: str,
                               unique_str: str = ".zip$") -> Iterator[str]:
    url = rc.__config__["!SIM.file.server_base_url"] + dir_name

    retry_strategy = Retry(total=2,
                           status_forcelist=HTTP_RETRY_CODES,
                           allowed_methods=["GET"])
    adapter = HTTPAdapter(max_retries=retry_strategy)

    try:
        with requests.Session() as session:
            session.mount("https://", adapter)
            result = session.get(url).content
    except (requests.exceptions.ConnectionError,
            requests.exceptions.RetryError) as error:
        logging.error(error)
        raise ServerError("Cannot connect to server. "
                          f"Attempted URL was: {url}.") from error
    except Exception as error:
        logging.error(("Unhandled exception occured while accessing server."
                      "Attempted URL was: %s."), url)
        logging.error(error)
        raise error

    soup = bs4.BeautifulSoup(result, features="lxml")
    hrefs = soup.find_all("a", href=True, string=re.compile(unique_str))
    pkgs = (href.string for href in hrefs)

    return pkgs


def _parse_raw_version(raw_version: str) -> str:
    """Catch initial package version which has no date info

    Set initial package version to basically "minus infinity".
    """
    if raw_version in ("", "zip"):
        return str(date(1, 1, 1))
    return raw_version.strip(".zip")


def _parse_package_version(package: str) -> Tuple[str, str]:
    p_name, p_version = package.split(".", maxsplit=1)
    return p_name, _parse_raw_version(p_version)


def _is_stable(package_version: str) -> bool:
    return not package_version.endswith("dev")


def get_stable(versions: Iterable[str]) -> str:
    """Return the most recent stable (not "dev") version."""
    return max(version for version in versions if _is_stable(version))


def group_package_versions(all_packages: Iterable[Tuple[str, str]]) -> _GrpItrType:
    """Group different versions of packages by package name"""
    version_groups = groupby_transform(sorted(all_packages),
                                       keyfunc=first,
                                       valuefunc=last,
                                       reducefunc=list)
    return version_groups


def crawl_server_dirs() -> Iterator[Tuple[str, Set[str]]]:
    """Search all folders on server for .zip files"""
    for dir_name in get_server_folder_contents("", "/"):
        logging.info("Searching folder '%s'", dir_name)
        try:
            p_dir = get_server_folder_package_names(dir_name)
        except ValueError as err:
            logging.info(err)
            continue
        logging.info("Found packages %s.", p_dir)
        yield dir_name, p_dir


def get_all_package_versions() -> Dict[str, List[str]]:
    """Gather all versions for all packages present in any folder on server"""
    grouped = {}
    folders = list(dict(crawl_server_dirs()).keys())
    for dir_name in folders:
        p_list = [_parse_package_version(package) for package
                  in get_server_folder_contents(dir_name)]
        grouped.update(group_package_versions(p_list))
    return grouped


def get_server_folder_package_names(dir_name: str) -> Set[str]:
    """
    Retrieve all unique package names present on server in `dir_name` folder.

    Parameters
    ----------
    dir_name : str
        Name of the folder on the server.

    Raises
    ------
    ValueError
        Raised if no valid packages are found in the given folder.

    Returns
    -------
    package_names : set of str
        Set of unique package names in `dir_name` folder.

    """
    package_names = {package.split(".", maxsplit=1)[0] for package
                     in get_server_folder_contents(dir_name)}

    if not package_names:
        raise ValueError(f"No packages found in directory \"{dir_name}\".")

    return package_names
