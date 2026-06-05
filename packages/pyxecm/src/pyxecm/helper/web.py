"""Module to implement functions to execute Web Requests."""

__author__ = "Dr. Marc Diefenbruch"
__copyright__ = "Copyright (C) 2024-2025, OpenText"
__credits__ = ["Kai-Philip Gatzweiler"]
__maintainer__ = "Dr. Marc Diefenbruch"
__email__ = "mdiefenb@opentext.com"

import logging
from pathlib import Path
import socket
import time

from pyxecm.helper.useragent import build_user_agent
from urllib.parse import urlparse

import requests
from lxml import html


MODULE_NAME = APP_NAME + ".helper.web"
USER_AGENT = build_user_agent("pyxecm.helper.web")

REQUEST_FORM_HEADERS = {
    "User-Agent": USER_AGENT,
    "Content-Type": "application/x-www-form-urlencoded",
}
REQUEST_TIMEOUT = 120.0
REQUEST_RETRY_DELAY = 20.0
REQUEST_MAX_RETRIES = 2

default_logger = logging.getLogger(MODULE_NAME)


class HTTP:
    """Class HTTP is used to issue HTTP request and test if hosts are reachable."""

    logger: logging.Logger = default_logger

    def __init__(
        self,
        logger: logging.Logger = default_logger,
    ) -> None:
        """Initialize the HTTP object."""

        if logger != default_logger:
            self.logger = logger.getChild("http")
            for logfilter in logger.filters:
                self.logger.addFilter(logfilter)

    # end method definition

    def check_host_reachable(self, hostname: str, port: int = 80) -> bool:
        """Check if a server / web address is reachable.

        Args:
            hostname (str):
                The endpoint hostname.
            port (int):
                The endpoint port.

        Results:
            bool:
                True is reachable, False otherwise

        """

        self.logger.debug(
            "Test if host -> '%s' is reachable on port -> %s ...",
            hostname,
            str(port),
        )
        try:
            socket.getaddrinfo(hostname, port)
        except socket.gaierror as exception:
            self.logger.warning(
                "Address-related error - cannot reach host -> %s; error -> %s",
                hostname,
                exception.strerror,
            )
            return False
        except OSError as exception:
            self.logger.warning(
                "Connection error - cannot reach host -> %s; error -> %s",
                hostname,
                exception.strerror,
            )
            return False
        else:
            self.logger.debug("Host is reachable at -> %s:%s", hostname, str(port))
            return True

    # end method definition

    def http_request(
        self,
        url: str,
        method: str = "POST",
        payload: dict | None = None,
        headers: dict | None = None,
        timeout: float | None = REQUEST_TIMEOUT,
        retries: int = REQUEST_MAX_RETRIES,
        wait_time: float = REQUEST_RETRY_DELAY,
        wait_on_status: list | None = None,
        show_error: bool = True,
        stream: bool = False,
    ) -> dict | None:
        """Issues an http request to a given URL.

        Args:
            url (str):
                The URL of the request.
            method (str, optional):
                Method of the request (POST, PUT, GET, ...). Defaults to "POST".
            payload (dict, optional):
                Request payload. Defaults to None.
            headers (dict, optional):
                Request header. Defaults to None. If None then a default
                value defined in REQUEST_FORM_HEADERS is used.
            timeout (float | None, optional):
                The timeout in seconds. Defaults to REQUEST_TIMEOUT.
            retries (int, optional):
                The number of retries. If -1 then unlimited retries.
                Defaults to REQUEST_MAX_RETRIES.
            wait_time (int, optional):
                The number of seconds to wait after each try.
                Defaults to REQUEST_RETRY_DELAY.
            wait_on_status (list, optional):
                A list of status codes we want to wait on.
                If None or empty then we wait for all return codes if
                wait_time > 0.
            show_error (bool, optional):
                Whether to show an error or a warning message in case of an error.
            stream (bool, optional):
                Enable stream for response content (e.g. for downloading large files).

        Returns:
            dict | None:
                Response of call

        """

        if not headers:
            headers = REQUEST_FORM_HEADERS

        message = f"Make HTTP request to URL -> '{url}' using -> {method} method"
        if payload:
            message += f" with payload -> {payload}"
        if retries:
            message += f" (max number of retries -> {retries}, wait time between retries -> {wait_time})"
            try:
                retries = int(retries)
            except ValueError:
                self.logger.warning(
                    "HTTP request -> retries is not a valid integer value: %s, defaulting to 0 retries ",
                    retries,
                )
                retries = 0

        self.logger.debug(message)

        try_counter = 1

        while True:
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    data=payload,
                    headers=headers,
                    timeout=timeout,
                    stream=stream,
                )
            except requests.RequestException as exc:
                response = None
                self.logger.warning(
                    "HTTP request -> %s to url -> %s failed (try %s); error -> %s",
                    method,
                    url,
                    try_counter,
                    exc,
                )

            if response is not None:
                # Do we have a successful result?
                if response.ok:
                    self.logger.debug(
                        "HTTP request -> %s to url -> %s succeeded with status -> %s!",
                        method,
                        url,
                        response.status_code,
                    )

                    if wait_on_status and response.status_code in wait_on_status:
                        self.logger.debug(
                            "%s is in wait_on_status list -> %s",
                            response.status_code,
                            wait_on_status,
                        )
                    else:
                        return response

                else:
                    message = "HTTP request -> {} to url -> {} failed; status -> {}; error -> {}".format(
                        method,
                        url,
                        response.status_code,
                        (
                            response.text
                            if response.headers.get("content-type") == "application/json"
                            else "see debug log"
                        ),
                    )
                    if show_error and retries == 0:
                        self.logger.error(message)
                    else:
                        self.logger.warning(message)
            # end if response is not None

            # Check if another retry is allowed, if not return None
            if retries == 0:
                return None

            if wait_time > 0.0:
                self.logger.warning(
                    "Sleeping %s seconds and then trying once more...",
                    str(wait_time * try_counter),
                )
                time.sleep(wait_time * try_counter)

            retries -= 1
            try_counter += 1
        # end while True:

    # end method definition

    def download_file(
        self,
        url: str,
        filename: str,
        timeout: float = REQUEST_TIMEOUT,
        retries: int | None = REQUEST_MAX_RETRIES,
        wait_time: float = REQUEST_RETRY_DELAY,
        wait_on_status: list | None = None,
        chunk_size: int = 8192,
        show_error: bool = True,
    ) -> bool:
        """Download a file from a URL.

        Args:
            url (str):
                The URL to open / load.
            filename (str):
                The filename to save the content.
            timeout (float, optional):
                The timeout in seconds.
            retries (int, optional):
                The number of retries. If -1 then unlimited retries.
            wait_time (float, optional):
                The number of seconds to wait after each try.
            wait_on_status (list, optional):
                The list of status codes we want to wait on.
                If None or empty then we wait for all return codes if
                wait_time > 0.
            chunk_size (int, optional):
                Chunk size for reading file content. Default is 8192.
            show_error (bool, optional):
                Whether or not an error show logged if download fails.
                Default is True.

        Returns:
            bool:
                True if successful, False otherwise.

        """

        # Validate the URL:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            self.logger.error("Invalid URL -> '%s' to download a file!", url)
            return False

        response = self.http_request(
            url=url,
            method="GET",
            retries=retries,
            timeout=timeout,
            wait_time=wait_time,
            wait_on_status=wait_on_status,
            show_error=show_error,
            stream=True,  # for downloads we want streaming
        )

        if not response or not response.ok:
            self.logger.error(
                "Failed to request download file -> '%s' from site -> %s%s",
                filename,
                url,
                f"; error -> {response.text}" if response else "",
            )
            return False

        try:
            directory = str(Path(filename).parent)
            if not Path(directory).exists():
                self.logger.info(
                    "Download directory -> '%s' does not exist, creating it.",
                    directory,
                )
                Path(directory).mkdir(parents=True, exist_ok=True)
            with Path(filename).open("wb") as download_file:
                download_file.writelines(response.iter_content(chunk_size=chunk_size))
            self.logger.debug(
                "File downloaded successfully as -> '%s' (size -> %s).",
                filename,
                self.human_readable_size(Path(filename).stat().st_size),
            )
        except (OSError, requests.exceptions.RequestException):
            self.logger.error(
                "Cannot write content to file -> '%s' in directory -> '%s'!",
                filename,
                directory,
            )
            return False
        else:
            return True

    # end method definition

    def human_readable_size(self, size_in_bytes: int) -> str:
        """Return a file size in human readable form.

        Args:
            size_in_bytes (int): The file size in bytes.

        Returns:
            str:
                The formatted size using units.

        """

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_in_bytes < 1024:
                return f"{size_in_bytes:.2f} {unit}"
            size_in_bytes /= 1024

        # We should never get here but linter wants it:
        return f"{size_in_bytes:.2f}"

    # end method definition

    def extract_content(self, url: str, xpath: str) -> str | None:
        """Extract a string from a response of a HTTP request based on an XPath.

        Args:
            url (str):
                The URL to open / load.
            xpath (str):
                The XPath expression to apply to the result.

        Returns:
            str | None:
                Extracted string or None in case of an error.

        """

        # Send a GET request to the URL:
        response = self.http_request(
            url=url,
            method="GET",
        )

        # Check if request was successful
        if response and response.ok:
            # Parse the HTML content
            tree = html.fromstring(response.content)

            # Extract content using XPath
            elements = tree.xpath(xpath)

            # Get text content of all elements and join them
            return "\n".join([elem.text_content().strip() for elem in elements])

            # Return the extracted content:

        # If request was not successful, print error message:
        self.logger.error(
            "Cannot extract content from URL -> '%s'; error code -> %s",
            url,
            response.status_code,
        )

        return None
