#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dwgconfig
import socket
from sys import argv
from dwgc import DWGD, logger
from daemon import Daemon

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', dwgconfig.port))
    sock.listen(1)
    logger('[SYSTEM] Server listening...', False)

    try:
        while True:
            conn, addr = sock.accept()
            logger('[SYSTEM] Gateway connected %s' % addr[0], False)
            DWGD(conn)
            logger('[SYSTEM] Gateway disconnected', False)
    except KeyboardInterrupt:
        exit()
    finally:
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
        if argv[1] == 'debug':
            dwgconfig.debug = True
            dwgconfig.as_daemon = False
            logger('[SYSTEM] Debug mode is on', True)
            main()
        elif argv[1] == 'start':
            logger('[SYSTEM] Daemon started', True)
            daemon.start()
        elif argv[1] == 'stop':
            logger('[SYSTEM] Daemon stopped', True)
            daemon.stop()
        elif argv[1] == 'restart':
            logger('[SYSTEM] Daemon restarted', True)
            daemon.restart()
        else:
            usage()
            exit(2)
        exit(0)
    else:
        usage()
        exit(2)