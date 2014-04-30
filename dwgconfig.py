#!/usr/bin/env python
# -*- coding: utf-8 -*-

port = 12000                                                    # DWG Gateway port
login = 'test'                                                  # DWG API Login (from API 2.0)
password = 'test'                                               # DWG API Password (from API 2.0)
income_path = '/var/spool/dwgp/incoming/'                       # SMS income path
send_path = '/var/spool/dwgp/send/'                             # SMS send path
ussd_income_path = '/var/spool/dwgp/ussd_incoming/'             # USSD income path
ussd_send_path = '/var/spool/dwgp/ussd_send'                    # USSD send path
run_program = '/etc/local_scripts/radius2.php'                  # External program after receiving SMS
debug = True                                                    # On/OFF Debug

pidfile = '/var/run/dwg_server.pid'                             # PID file path (for daemon)
logfile = '/var/log/dwg_server.log'                             # Log file path (for daemon)
as_daemon = True

if __name__ == '__main__':
    print 'Config file for Dinstar DWG Gateways!'