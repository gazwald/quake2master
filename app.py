#!/usr/bin/env python3
import logging
import sys
import os

from protocols import Protocols
from storage import Storage
from transport import Transport

from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all


try:
    xray_recorder.configure(
        service='MasterServer',
        context_missing='LOG_ERROR',
        plugins=('ECSPlugin', 'EC2Plugin'),
    )
    patch_all()
except:
    logging.exception('Failed to import X-ray')


def setup_logging(level='INFO'):
    # logging.getLogger('boto3').propagate = False
    # logging.getLogger('botocore').propagate = False

    log_level = getattr(logging, level.upper())

    logging.basicConfig(stream=sys.stdout,
                        level=log_level,
                        format='%(asctime)s %(levelname)s %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')


def main():
    protocols = Protocols()
    storage = Storage()
    transport = Transport(storage, protocols)

    try:
        transport.loop.run_forever()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    os.environ['STAGE'] = os.getenv('STAGE', 'PRODUCTION')

    if os.getenv('STAGE') == 'TESTING':
        setup_logging('DEBUG')
    else:
        setup_logging('DEBUG')

    logging.info(f"Starting master server.")
    main()
    logging.info(f"Master server stopped.")
