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
RMS = Gauge('rms', 'Sound level in root mean square of signal level', LABELS, namespace=NAMESPACE)
LEVEL = Gauge('level', 'Sound level in dB', LABELS, namespace=NAMESPACE)


logging.basicConfig(
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S%z',
    level=LOG_LEVEL,
    stream=sys.stderr,
)
logger = logging.getLogger('sound-level-exporter')


def compute_rms(data):
    if data.size <= 0:
        return 0
    normalized_data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    return np.sqrt(np.mean(np.square(normalized_data, dtype=np.float64)))


def compute_db(rms):
    if rms <= 0:
        return 0
    return 20 * np.log10(rms)


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
            start_time = time.monotonic()
            max_rms = 0
            max_db = 0

            while time.monotonic() - start_time < SAMPLING_INTERVAL:
                buf = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                data = np.frombuffer(buf, dtype=np.int16)
                rms = compute_rms(data)
                max_rms = max(max_rms, rms)
                db = compute_db(rms)
                max_db = max(max_db, db)

            labels = {'device_name': device_info['name']}
            RMS.labels(**labels).set(max_rms)
            logger.debug(f'Max RMS over {SAMPLING_INTERVAL}s: {max_rms}')
            LEVEL.labels(**labels).set(max_db)
            logger.debug(f'Max dB over {SAMPLING_INTERVAL}s: {max_db} dB')
    except KeyboardInterrupt:
        logger.info("Quit collecting sound level.")
        stream.stop_stream()
        stream.close()
        audio.terminate()


if __name__ == '__main__':
    logger.info(f'Starting the server on port {PORT}.')
    start_http_server(PORT)
    main()
