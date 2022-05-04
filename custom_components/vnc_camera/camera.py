from __future__ import annotations

import logging
from datetime import timedelta
import io

import voluptuous as vol

from homeassistant.components.camera import Camera
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import asyncvnc
from PIL import Image

_LOGGER = logging.getLogger(__name__)

DOMAIN = "vnc_camera"

ICON = "mdi:mdiRemoteDesktop"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

CONF_HOST = 'host'
CONF_PORT = 'port'
CONF_USERNAME = 'username'
CONF_PASSWORD = 'password'


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HOST, default='localhost'): cv.string,
        vol.Optional(CONF_PORT, default='5900'): cv.string,
        vol.Optional(CONF_USERNAME, default=None): cv.string,
        vol.Optional(CONF_PASSWORD, default=None): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the skyfield platform."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    _LOGGER.debug("Setting up VNC Cam.")
    panel = VNCCam(
        host, port, username, password
    )

    _LOGGER.debug("Adding VNC cam")
    add_entities([panel], True)


class VNCCam(Camera):
    def __init__(
        self,
        host, port, username, password
    ):
        Camera.__init__(self)
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def frame_interval(self):
        # this is how often the image will update in the background.
        # When the GUI panel is up, it is always updated every
        # 10 seconds, which is too much. Must figure out how to
        # reduce...
        return 180

    @property
    def name(self):
        return "VNC"

    @property
    def brand(self):
        return "VNC"

    @property
    def model(self):
        return "VNC"

    @property
    def icon(self):
        return ICON

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        async with asyncvnc.connect(self.host, self.port, self.username, self.password) as client:

            # Request a video update
            client.video.refresh()

            # Handle packet
            await client.read()

            # Retrieve pixels as a 3D numpy array
            pixels = client.video.as_rgba()

            # Return PNG using PIL/pillow
            image = Image.fromarray(pixels)

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
