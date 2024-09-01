
Introduction
---------------

Sferum Bot is a Python library that allows you to automate interactions with Sferum conferences. It uses the Playwright library to control a headless browser and simulate user interactions.

Usage
-----

To use Sferum Bot, you need to create an instance of the `SferumBot` class and call its methods to interact with the conference.

Classes
---------

### MediaDevice

The `MediaDevice` class is an interface for media devices. It has one method: `get_inject_code`, which returns the code to inject in the page.

### MediaDeviceStream

The `MediaDeviceStream` class is a subclass of `MediaDevice`. It uses a `MediaServer` to stream video and audio. It has the following methods:

#### MediaDeviceStream Methods

* `__init__`: Initializes the `MediaDeviceStream` object.
* `read_stream`: Reads the video stream and appends frames.
* `get_inject_code`: Returns the code to inject in the page.
* `run`: Runs the `MediaServer`.

### SferumSelectors

The `SferumSelectors` class contains selectors for Sferum conference elements.

### SferumBot

The `SferumBot` class is the main class of the library. It has the following methods:

#### SferumBot Methods

* `__init__`: Initializes the `SferumBot` object.
* `set_context`: Sets the context and adds a new page.
* `set_browser`: Sets the browser and adds a new context.
* `launch_browser`: Launches a new browser.
* `connect`: Connects to the Sferum conference.
* `disconnect`: Disconnects from the Sferum conference.
* `is_in_wait_room`: Checks if the bot is in the wait room.
* `is_connected`: Checks if the bot is connected.
* `wait_to_connect`: Waits for the bot to connect.
* `inject_stream`: Injects the media stream on the page.
* `check_microphone_turn`: Checks if the microphone is turned on.
* `turn_microphone`: Turns the microphone on or off.
* `turn_camera`: Turns the camera on/off.
* `screenshot`: Takes a screenshot.
* `close`: Closes the browser.

Examples
--------

### Example 1: Connect to a Sferum Conference

```python
import asyncio
from SferumBot import SferumBot

async def main():
    bot = SferumBot("conference_id", "bot_name")
    await bot.launch_browser()
    await bot.connect()
    await bot.wait_to_connect()
    await bot.turn_microphone(True)
    await bot.turn_camera()

asyncio.run(main())
```

### Example 2: Use a MediaDeviceStream

```python
import asyncio
from SferumBot import SferumBot, MediaDeviceStream
import cv2

async def main():
    video_stream = cv2.VideoCapture("video.mp4")
    audio_file = "audio.wav"
    media_stream = MediaDeviceStream(8080, video_stream, audio_file)
    media_stream.run()

    bot = SferumBot("conference_id", "bot_name", media_stream)
    await bot.launch_browser()
    await bot.connect()
    await bot.wait_to_connect()
    await bot.turn_microphone(True)
    await bot.turn_camera()

asyncio.run(main())
```