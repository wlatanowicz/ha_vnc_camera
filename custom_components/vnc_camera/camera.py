from __future__ import annotations

import logging
from datetime import timedelta
import io

import voluptuous as vol

from homeassistant.components.camera import Camera
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv

import asyncio
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


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the skyfield platform."""
    host = config.get(CONF_HOST)
    port = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    _LOGGER.debug("Setting up VNC Cam.")
    panel = VNCCam(
        host, port, username, password
    )
    hass.async_create_task(panel.vnc_connection())

    _LOGGER.debug("Adding VNC cam")
    async_add_entities([panel])


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

        self.client = None

    @property
    def frame_interval(self):
        # this is how often the image will update in the background.
        # When the GUI panel is up, it is always updated every
        # 10 seconds, which is too much. Must figure out how to
        # reduce...
        return 1

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

    async def vnc_connection(self):
        while True:
            try:
                async with asyncvnc.connect(self.host, self.port, self.username, self.password) as client:
                    self.client = client

                    while True:
                        # Handle packet
                        await client.read()

            except Exception:
                _LOGGER.exception("VNC Disconnected")

            self.client = None
            await asyncio.sleep(10)


    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:

            if not self.client:
                return None

            # Request a video update
            self.client.video.refresh()

            # Retrieve pixels as a 3D numpy array
            pixels = self.client.video.as_rgba()

            # Return PNG using PIL/pillow
            image = Image.fromarray(pixels)

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            return img_byte_arr.getvalue()
