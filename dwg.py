#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dwgconfig
import socket
import logging
from sys import argv
from dwgc import DWGD
from daemon import Daemon
from logger import create_logger


def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', dwgconfig.port))
    sock.listen(1)
    logging.info('[SYSTEM] Server listening...')

    try:
        while True:
            conn, addr = sock.accept()
            logging.info('[SYSTEM] Gateway connected %s' % addr[0])
            DWGD(conn)
            logging.info('[SYSTEM] Gateway disconnected')
    except KeyboardInterrupt:
        logging.info('[SYSTEM] Daemon keyboard interrupted')
        exit()
    finally:
        logging.info('[SYSTEM] Daemon socket closed')
        sock.close()


def usage():
    print """
Script usage parameters:
    debug - Run script in current console with debug mode.
    start - Run script as daemon
    stop - Stop daemon
    restart - Rerun script as daemon
    help - Show this help
"""


class DWGDaemon(Daemon):
    def run(self):
        main()


"""
Check agrvs
"""
if __name__ == "__main__":
    daemon = DWGDaemon(dwgconfig.pidfile)
    if len(argv) == 2:
        allowed_argv = ['debug', 'start', 'stop', 'restart']
        if argv[1] not in allowed_argv:
            usage()
            exit(2)
        else:
            create_logger(argv[1] == 'debug')
            if argv[1] == 'debug':
                logging.debug('[SYSTEM] Debug mode is on')
                main()
            elif argv[1] == 'start':
                logging.info('[SYSTEM] Daemon started')
                daemon.start()
            elif argv[1] == 'stop':
                logging.info('[SYSTEM] Daemon stopped')
                daemon.stop()
            elif argv[1] == 'restart':
                logging.info('[SYSTEM] Daemon restarted')
                daemon.restart()
            exit(0)
    else:
        usage()
        exit(2)
