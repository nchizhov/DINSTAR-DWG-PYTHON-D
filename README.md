Overview
========

This Script for VoIP GSM Module - Dinstar DWG 2000: sending and receiveing SMS/USSD from/to gateway (written on Python2).

How to compile
==============

- Clone the repo or download the sources.

How to install
==============

- Edit dwgconfig.py 
- DWG listening port (dwg_port)
- DWG login and password (login, password) - only for API 2.1
- Path for send and receive SMS directories (send_path, income_path)
- Path to external program, what shoud be executed when SMS received (run_program)
- Path for send and receive USSD (ussd_send_path, ussd_income_path)
- On/Off debugging (debug)
            
How to use
==========
            
- Running: /path/to/scripts/main.py (Recommending run in screen)
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