#!/usr/bin/env python3

import logging
import numpy as np
import os
from prometheus_client import Gauge, start_http_server
import pyaudio
import sys
import time


PORT = int(os.getenv('SOUND_LEVEL_EXPORTER_PORT', '9854'))
LOG_LEVEL = os.getenv('SOUND_LEVEL_EXPORTER_LOG_LEVEL', 'INFO')
SAMPLING_INTERVAL = int(os.getenv('SOUND_LEVEL_EXPORTER_SAMPLING_INTERVAL', '3'))
NAMESPACE = 'sound_level'
CHUNK_SIZE = 1024
LABELS = ['device_name']
LEVEL = Gauge('level', 'Sound level in dB', LABELS, namespace=NAMESPACE)


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
    level=LOG_LEVEL,
    stream=sys.stderr,
)
logger = logging.getLogger('switchbot-local-exporter')


def main():
    audio = pyaudio.PyAudio()
    device_info = audio.get_default_input_device_info()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=44100,
        input=True,
        frames_per_buffer=CHUNK_SIZE,
    )
    try:
        while True:
            buf = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            data = np.frombuffer(buf, dtype=np.int16)
            rms = np.sqrt(np.mean(np.square(data)))
            db = 20 * np.log10(rms) if rms > 0 else 0
            labels = {
                'device_name': device_info['name'],
            }
            LEVEL.labels(**labels).set(db)
            time.sleep(SAMPLING_INTERVAL)
    except KeyboardInterrupt:
        logger.info("Quit collecting sound level.")
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == '__main__':
    logger.info(f'Starting the server on port {PORT}.')
    start_http_server(PORT)
    main()
