Overview
========

This Script for VoIP GSM Module - Dinstar DWG 2000: sending and receiving SMS/USSD from/to gateway.

**Python2** version here (**NOT** supported): https://github.com/nchizhov/DINSTAR-DWG-PYTHON-D/releases/tag/Python2

How to install
==============

```bash
sudo git clone https://github.com/nchizhov/DINSTAR-DWG-PYTHON-D.git /opt/dwgd
systemctl link /opt/dwgd/dwg.service
systemctl enable dwg --now
```

How to configure
================

Edit **dwgconfig.py**:
- ```port``` - DWG listening port
- ```login```, ```password``` - DWG login and password (only for API 2.1)
- ```income_path```, ```send_path``` - Path for send and receive SMS directories (Should be existed)
- ```run_program``` - Path to external program, what should be executed when SMS received. Set to ```None``` if not want to run external program
- ```ussd_income_path```, ```ussd_income_path``` - Path for send and receive USSD (Should be existed)
- ```debug``` - On/Off debugging
- ```pidfile``` - Path for pidfile, if running as daemon
- ```logfile``` - Path to logfile, if running as daemon
- ```log_format``` - Format of log line (see: https://docs.python.org/3/library/logging.html#logrecord-attributes)
- ```log_date_format``` - Format of date in log line (see: https://docs.python.org/3/library/time.html#time.strftime)
            
How to use
==========
            
- Running: ```/path/to/scripts/dwg.py``` with arguments:
  - **debug**: run in console mode with full debugging
  - **start**: starting script as daemon
  - **stop**: stopping script, when running as daemon
  - **restart**: restarting script as daemon
  - **help**: showing help message for arguments
- Sending SMS format:
  - First line - phone number
  - Second line - port
  - Other lines - message for send
- Received message as eml format.
- Sending USSD-command format:
  - First line - port
  - Second line - USSD-command (ex. *100#)
- Received message as eml format.
                      
Depends
=======
                      
- Required Python 3
                      
                       
If any doubts arises, please visit my blog https://blog.kgd.in or write me an email, I will be answering as soon as I can.