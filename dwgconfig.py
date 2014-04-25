#!/usr/bin/env python
# -*- coding: utf-8 -*-
port = 12000                                                    # DWG Gateway port
login = 'test'                                                  # DWG API Login (form API 2.0)
password = 'test'                                               # DWG API Password (form API 2.0)
income_path = '/var/spool/dwgp/incoming/'                       # SMS income path
send_path = '/var/spool/dwgp/send/'                             # SMS send path
ussd_income_path = '/var/spool/dwgp/ussd_incoming/'             # USSD income path
ussd_send_path = '/var/spool/dwgp/ussd_send'                    # USSD send path
run_program = '/etc/local_scripts/radius2.php'                  # External program after receiving SMS
debug = True                                                    # ON/OFF debigging in console

if __name__ == '__main__':
    print 'Config file for Dinstar DWG Gateways!'