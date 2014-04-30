Overview
========

This Script for VoIP GSM Module - Dinstar DWG 2000: sending and receiveing SMS/USSD from/to gateway (written on Python2).

How to compile
==============

- Clone the repo or download the sources.

How to install
==============

- Edit dwgconfig.py 
- DWG listening port (port)
- DWG login and password (login, password) - only for API 2.1
- Path for send and receive SMS directories (send_path, income_path)
- Path to external program, what shoud be executed when SMS received (run_program)
- Path for send and receive USSD (ussd_send_path, ussd_income_path)
- On/Off debugging (debug)
- Path for pidfile, if running as daemon (pidfile)
- Path to logfile, if running as daemon (logfile)
            
How to use
==========
            
- Running: /path/to/scripts/dwg.py with arguments:
  - debug: run in console mode with full debugging
  - start: starting script as daemon
  - stop: stopping script, when running as daemon
  - restart: restarting script as daemon
  - help: showing help message for arguments
- Sending SMS format:
- First line - phone number
- Second line - port
- Other lines - message for send
- Received message as eml format.
- Sending USSD-command format
- First line - port
- Second line - USSD-command (ex. *100#)
- Received message as eml format.
                      
Depends
=======
                      
- Required Python 2
                      
                       
If any doubts arises, please visit my blog http://blog.kgd.in or write me an email, I will be answering as soon as I can.