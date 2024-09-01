import asyncio
import time
from io import BytesIO
from threading import Thread

import cv2
import playwright.async_api
from PIL import Image
from playwright.async_api import async_playwright

from MediaServer import MediaServer


class MediaDevice:
    def __init__(self):
        """
        Media device interface class
        """
        pass

    def get_inject_code(self) -> str:
        """
        Code to inject in page
        :return: str - code to inject
        """
        return """"""


class MediaDeviceStream(MediaDevice):
    def __init__(self, port, video_stream, audio_file):
        """
        Use MediaServer for MediaDevice
        :param port: port to run server on.
        :param video_stream: opencv stream for video.
        :param audio_file: .wav file for audio
        """
        super().__init__()
        self.audio_file = audio_file
        self.video_stream = video_stream
        self.port = port
        self.running = False
        ret, frame = video_stream.read()
        self.media_server = MediaServer(self.port, frame.shape[0], frame.shape[1])
        self.media_server.add_audio_path(self.audio_file)
        self.server_thread = Thread(target=self.media_server.run)
        self.server_thread.daemon = True
        self.reading_thread = Thread(target=self.read_stream)
        self.reading_thread.daemon = True

    def read_stream(self):
        """
        read video stream and append frame
        :return: None
        """
        spf = 1 / self.video_stream.get(cv2.CAP_PROP_FPS)
        while self.running:
            start = time.time()
            ret, frame = self.video_stream.read()
            if ret:
                self.media_server.add_next_frame(frame)
            else:
                self.video_stream.set(cv2.CAP_PROP_POS_FRAMES, 0)
            wait_time = spf - (time.time() - start)
            if wait_time > 0:
                time.sleep(wait_time)

    def get_inject_code(self):
        """
        Code to inject in page
        :return: str - code to inject
        """
        return """var fps = 60;

const canvas = document.createElement("canvas");
canvas.setAttribute('id', 'fake_camera_stream');
const context = canvas.getContext('2d');

const stream = canvas.captureStream(fps);

var audio = new Audio("https://127.0.0.1:PORT/audio_file");
loaded = false;
audio.loop = true;
audio.play();
audio.onloadeddata = function(){
    const audio_stream = audio.captureStream()
    const track = audio_stream.getAudioTracks()[0];

    stream.addTrack(track);
    loaded = true;
}


canvas.style.display="none";

var img = new Image;
img.onload = function(){
  canvas.width = this.naturalWidth;
  canvas.height = this.naturalHeight;

  setInterval(draw, 1./fps);

};
img.src = "https://127.0.0.1:PORT/video_stream";

function draw() {
  context.drawImage(img, 0,0);
}

navigator.mediaDevices.getUserMedia = () => Promise.resolve(stream);

document.querySelector("body").appendChild(canvas);
""".replace("PORT", str(self.port))

    def run(self):
        """
        Run MediaServer
        :return:
        """
        self.running = True
        self.server_thread.start()
        self.reading_thread.start()


class SferumSelectors:
    JOIN_CALL_INPUT_SELECTOR = ("#join-calls-root > div > div > div.JoinScreenAnonym-module__footer--UJIJy > "
                                "div.JoinScreenAnonym-module__form--fagvI > div:nth-child(1) > div > span > div > div"
                                " > input")
    JOIN_CALL_BUTTON_SELECTOR = ("#join-calls-root > div > div > div.JoinScreenAnonym-module__footer--UJIJy > "
                                 "div.JoinScreenAnonym-module__form--fagvI > div:nth-child(2) > button")
    CALL_CONTENT_WRAPPER_SELECTOR = ".Call__contentWrapper"
    WAITING_ROOM_CONTAINER_SELECTOR = ".waiting-room-container"
    FAKE_CAMERA_STREAM_SELECTOR = "#fake_camera_stream"
    MICROPHONE_TURN_BUTTON_SELECTOR = ("body > div.BaseModal.CallModal.CallModal--withAnimation > "
                                       "div.BaseModal__content > div > div.FocusTrap__content > div > section > "
                                       "footer > div:nth-child(2) > section > div > div:nth-child(3) > div > div > "
                                       "button")
    CAMERA_TURN_BUTTON_SELECTOR = ("body > div.BaseModal.CallModal.CallModal--withAnimation > div.BaseModal__content > "
                                   "div > div.FocusTrap__content > div > section > footer > div:nth-child(2) > "
                                   "section > div > div:nth-child(2) > div > div > button")
    DISCONNECT_BUTTON_SELECTOR = ("body > div.BaseModal.CallModal.CallModal--withAnimation > div.BaseModal__content > "
                                  "div > div.FocusTrap__content > div > section > footer > div:nth-child(2) > section "
                                  "> div > div:nth-child(4) > div > div > button")


class SferumBot:
    page: playwright.async_api.Page

    def __init__(self, call_id, name, media_stream=None):
        self.playwright = None
        self.call_id = call_id
        self.media_stream = media_stream
        self.iframe = None
        self.name = name
        self.browser = None
        self.context = None

    async def set_context(self, context):
        """
        Setting context and adding new page. Helpful for multiple bots in one context
        :param context:
        :return:
        """
        self.context = context
        print("New page...")
        self.page = await self.context.new_page()
        print("Created!")

    async def set_browser(self, browser):
        """
        Setting browser and adding new context. Helpful for multiple bots in one browser
        :param browser:
        :return:
        """
        self.browser = browser
        await self.set_context(await self.browser.new_context())

    async def launch_browser(self):
        """
        Creates new browser
        :return:
        """
        self.playwright = await async_playwright().start()
        await self.set_browser(await self.playwright.chromium.launch(headless=True, args=[
            "--use-fake-ui-for-media-stream",
            "--use-fake-device-for-media-stream",
            "--mute-audio",
            "--disable-web-security",
            "--allow-running-insecure-content",
            '--ignore-certificate-errors',
            '--autoplay-policy=no-user-gesture-required',
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--disable-crash-reporter",
            "--disable-oopr-debug-crash-dump",
            "--no-crash-upload",
            "--disable-gpu",
            "--disable-extensions",
            "--disable-low-res-tiling",
            "--log-level=3",
            "--silent"
        ]))

    async def connect(self):
        """
        Connect to sferum conference.
        :return: Exception if bot already connected
        """
        if await self.is_connected():
            raise Exception("Bot already connected!")
        await self.page.goto(f"https://web.vk.me/call/join/{self.call_id}")
        await self.page.wait_for_selector(SferumSelectors.JOIN_CALL_INPUT_SELECTOR)
        await self.page.fill(SferumSelectors.JOIN_CALL_INPUT_SELECTOR, self.name)
        await self.page.wait_for_selector(SferumSelectors.JOIN_CALL_BUTTON_SELECTOR)
        await self.page.click(SferumSelectors.JOIN_CALL_BUTTON_SELECTOR)
        await self.page.wait_for_selector(SferumSelectors.CALL_CONTENT_WRAPPER_SELECTOR)

    async def disconnect(self):
        """
        Disconnect bot from conference (without closing page).
        :return:
        """
        if not self.iframe or not await self.is_connected():
            return
        await self.page.click(SferumSelectors.DISCONNECT_BUTTON_SELECTOR)

    async def is_in_wait_room(self) -> bool:
        """
        NOT WORK FOR CURRENT MOMENT
        :return:
        """
        try:
            await self.page.query_selector(SferumSelectors.WAITING_ROOM_CONTAINER_SELECTOR)
        except Exception:
            return False
        return True

    async def is_connected(self) -> bool:
        """
        Check if bot connected
        :return: True if connected otherwise False
        """
        if (await self.page.query_selector(SferumSelectors.CALL_CONTENT_WRAPPER_SELECTOR)) is None:
            return False
        return True

    async def wait_to_connect(self, timeout=10) -> bool:
        """
        Wait some time to bot connect.
        :param timeout: timeout in seconds
        :return:
        """
        start_time = time.time()
        while not await self.is_connected():
            await asyncio.sleep(0.5)
            if time.time() - start_time > timeout:
                return False
        return True

    async def _move_mouse(self):
        """
        NOT USED
        :return:
        """
        await self.page.mouse.move(13, 15)
        await self.page.mouse.move(-13, -15)

    async def inject_stream(self):
        """
        Injects media stream on page (run when you use other functions like turn_camera, not needed to use manually).
        :return:
        """
        if (await self.page.query_selector(SferumSelectors.FAKE_CAMERA_STREAM_SELECTOR)) is None:
            if self.media_stream:
                await self.page.evaluate(self.media_stream.get_inject_code())

    async def check_microphone_turn(self):
        """
        Checks microphone turn.
        :return: True if microphone is on otherwise False
        """
        elem = await self.page.query_selector(SferumSelectors.MICROPHONE_TURN_BUTTON_SELECTOR)
        print(await elem.get_attribute("aria-label"))
        if (await elem.get_attribute("aria-label")).find("Выключить") != -1:
            return True
        return False

    async def turn_microphone(self, state):
        """
        Turn microphone
        :param state: True for turn on, False for turn off
        :return: Exception if bot not connected
        """
        if not await self.is_connected():
            raise Exception("Bot doesn't connected!")
        await self.inject_stream()
        print(await self.check_microphone_turn(), state)
        if (await self.check_microphone_turn()) != state:
            await self._wait_and_click_selector(SferumSelectors.MICROPHONE_TURN_BUTTON_SELECTOR)

    async def turn_camera(self):
        """
        Turn camera on/off
        :return: Exception if bot not connected
        """
        if not await self.is_connected():
            raise Exception("Bot doesn't connected!")
        await self.inject_stream()
        await self._wait_and_click_selector(SferumSelectors.CAMERA_TURN_BUTTON_SELECTOR)

    async def screenshot(self) -> Image:
        """
        Make screenshot
        :return: Exception if bot not connected, PILLOW image otherwise
        """
        if not await self.is_connected():
            raise Exception("Bot doesn't connected!")
        png = await self.page.screenshot()
        return Image.open(BytesIO(png))

    async def close(self):
        """
        Closes browser
        :return:
        """
        await self.browser.close()

    async def _wait_and_click_selector(self, selector):
        """
        Wait for selector and then click
        :param selector:
        :return:
        """
        await self.page.wait_for_selector(selector)
        await self.page.click(selector)
