#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dwgconfig
from threading import Timer
from struct import pack, unpack
from random import randint
from sys import exit
from time import time, strftime
import codecs
import os
import logging
from subprocess import Popen


class DWGD:
    ping_t = None
    check_t = None
    conn = None
    ping_timer = 45.0
    check_timer = 5.0
    ping_count = 0

    def __init__(self, conn):
        self.conn = conn
        Timer(self.ping_timer, self.pingDWG).start()
        Timer(self.check_timer, self.checkSMS).start()
        self.getDWG()

    def getDWG(self):
        """
        Listening DWG Client
        """
        while True:
            try:
                data = self.conn.recv(66560)
                if not data:
                    break
                else:
                    self.parseDWG(data)
            except KeyboardInterrupt:
                exit()
            except:
                break
        self.stop_ping()
        self.conn.close()

    def parseDWG(self, data):
        """
        Parsing DWG Messages
        """
        if data:
            logging.debug('[PROCESS] <- %s' % data.encode("hex"))
            while data:
                header = {'len': unpack('!L', data[0:4])[0],
                          'id': {'mac': unpack('!6s', data[4:10])[0],
                                 'time': unpack('!L', data[12:16])[0],
                                 'serial': unpack('!L', data[16:20])[0]},
                          'type': unpack('!H', data[20:22])[0],
                          'flag': unpack('!H', data[22:24])[0]}
                data_len = 24 + header['len']
                if len(data) < data_len:
                    break
                sdata = self.parseType(header['type'], data[24:data_len])
                if sdata['type']:
                    self.sendDWG(header, sdata)
                data = data[data_len:]

    def parseType(self, htype, data):
        """
        Parsing DWG Types
        """
        sdata = {'type': 0,
                 'body': ''}
        if htype == 0:  # received keep alive
            self.ping_count = 0
        elif htype == 7:   # Status message
            sdata['type'] = 8
            sdata['body'] = pack('!?', False)
        elif htype == 5:   # Receive message
            body = {'number': unpack('!24s', data[0:24])[0].replace('\x00', ''),
                    'type': unpack('!B', data[24])[0],
                    'port': unpack('!B', data[25])[0],
                    'timestamp': unpack('!15s', data[26:41])[0].replace('\x00', ''),
                    'timezone': unpack('!b', data[41])[0],
                    'encoding': unpack('!B', data[42])[0],
                    'length': unpack('!H', data[43:45])[0]}
            body['content'] = unpack('!%ds' % body['length'], data[45:])[0]
            self.saveSMS(body)
            sdata['type'] = 6
            sdata['body'] = pack('!?', False)
        elif htype == 3:  # SMS Result
            sdata['type'] = 4
            sdata['body'] = pack('!?', False)
        elif htype == 11:  # USSD Result
            body = {'port': unpack('!B', data[0])[0],
                    'status': unpack('!B', data[1])[0],
                    'length': unpack('!H', data[2:4])[0],
                    'encoding': unpack('!B', data[4])[0]}
            body['content'] = unpack('!%ds' % body['length'], data[5:])[0]
            self.saveUSSD(body)
            sdata['type'] = 12
            sdata['body'] = pack('!?', False)
        elif htype == 15:   # Auth for API 2.0
            body = {'login': unpack('!16s', data[0:16])[0].replace('\x00', ''),
                    'password': unpack('!16s', data[16:])[0].replace('\x00', '')}
            if body['login'] == dwgconfig.login and body['password'] == dwgconfig.password:
                sdata['type'] = 16
                sdata['body'] = pack('!?', False)
                logging.info('[SYSTEM] Authentication success')
            else:
                logging.info('[SYSTEM] Authentication failed')
        elif htype == 515:  # Call state report
            sdata['type'] = 516
            sdata['body'] = pack('!?', False)
        return sdata

    def pingDWG(self):
        """
        Ping DWG
        """
        if self.ping_count > 2:
            self.stop_ping()
            self.conn.close()
        else:
            sdata = {'type': 0,
                     'body': ''}
            self.ping_count += self.ping_count
            self.sendDWG(self.create_header(), sdata)
            self.ping_t = Timer(self.ping_timer, self.pingDWG)
            self.ping_t.start()

    def sendDWG(self, header, sdata):
        """
        Sending message to DWG
        """
        global ping_t
        pkt = pack('!L', len(sdata['body']))
        pkt += pack('!6s', header['id']['mac']) + "\x00\x00"
        pkt += pack('!L', header['id']['time'])
        pkt += pack('!L', header['id']['serial'])
        pkt += pack('!H', sdata['type'])
        pkt += pack('!H', 0)
        pkt += sdata['body']
        logging.debug('[PROCESS] -> %s' % pkt.encode("hex"))
        self.conn.send(pkt)

    def create_header(self):
        """
        Create headers for DWG
        """
        return {'id': {'mac': '\x00\xfa\xb3\xd2\xd3\xaa',
                       'time': int(time()),
                       'serial': randint(1, 1000000)}}

    def saveSMS(self, body):
        """
        Saving SMS to file
        """
        try:
            sms_partfilename = '%s%s.%s' % (dwgconfig.income_path, body['number'], int(time()))
            sms_filename = '%s.%s' % (sms_partfilename, randint(1, 999999))
            while os.path.isfile(sms_filename):
                sms_filename = '%s.%s' % (sms_partfilename, randint(1, 999999))
            sms = codecs.open(sms_filename, 'w', 'utf-8')
            sms.write('Number: %s\n' % body['number'])
            sms.write('Port: %s\n' % body['port'])
            sms.write('Time: %s\n' % body['timestamp'])
            sms.write('Timezone: %s\n' % body['timezone'])
            sms.write('Encoding: %s\n\n' % body['encoding'])
            if body['encoding'] == 0:
                sms.write(body['content'])
            elif body['encoding'] == 1:
                sms.write(body['content'].decode('utf-16-be'))
            sms.close()
            Popen(dwgconfig.run_program)
            logging.info('[DATA] Received SMS from number %s' % body['number'])
        except:
            logging.info('[DATA] Received unknown SMS')

    def saveUSSD(self, body):
        """
        Saving USSD to file
        """
        try:
            ussd_partfilename = '%s%s.%s' % (dwgconfig.ussd_income_path, body['port'], int(time()))
            ussd_filename = '%s.%s' % (ussd_partfilename, randint(1, 999999))
            while os.path.isfile(ussd_filename):
                ussd_filename = '%s.%s' % (ussd_partfilename, randint(1, 999999))
            ussd = codecs.open(ussd_filename, 'w', 'utf-8')
            ussd.write('Port: %s\n' % body['port'])
            ussd.write('Time: %s\n' % strftime('%d%m%Y%H%M%S'))
            ussd.write('Status: %s\n' % body['status'])
            ussd.write('Encoding: %s\n\n' % body['encoding'])
            if body['encoding'] == 0:
                ussd.write(''.join([unichr(int(body['content'][pos:pos+4], 16)) for pos in range(0, len(body['content']), 4)]))
            elif body['encoding'] == 1:
                ussd.write(body['content'].decode('utf-16-be'))
            ussd.close()
            logging.info('[DATA] Received USSD from port %s' % body['port'])
        except:
            logging.info('[DATA] Received unknown USSD')

    def checkSMS(self):
        """
        Check SMS/USSD in folders
        """
        files = [f for f in os.listdir(dwgconfig.send_path) if os.path.isfile(os.path.join(dwgconfig.send_path, f))]
        port = None
        number = None
        if len(files):
            sms = codecs.open(dwgconfig.send_path + files[0], 'r', 'utf-8').readlines()
            f_send = True
            if len(sms) > 2:
                try:
                    number = str(sms[0].strip())
                    # if not number.isdigit(): f_send = False
                except:
                    f_send = False
                try:
                    port = int(sms[1].strip())
                except:
                    f_send = False
                if f_send:
                    content = ''
                    for line in sms[2:]:
                        content += line.strip() + '\n'
                    content = ''.join([pack('!H', ord(l)) for l in content.strip()])
                    sdata = {'type': 1,
                             'body': pack('!BBBB24sH%ds' % len(content), port, 1, 0, 1, number, len(content), content)}
                    self.sendDWG(self.create_header(), sdata)
                    logging.info('[DATA] Sending SMS to number %s' % number)
            os.remove(dwgconfig.send_path + files[0])
        else:
            files = [f for f in os.listdir(dwgconfig.ussd_send_path) if os.path.isfile(os.path.join(dwgconfig.ussd_send_path, f))]
            if len(files):
                ussd = codecs.open(dwgconfig.ussd_send_path + files[0], 'r', 'utf-8').readlines()
                f_send = True
                if len(ussd) > 1:
                    try:
                        port = int(ussd[0].strip())
                    except:
                        f_send = False
                    try:
                        number = str(ussd[1].strip())
                    except:
                        f_send = False
                    if f_send:
                        sdata = {'type': 9,
                                 'body': pack('!BBH%ds' % len(number), port, 1, len(number), number)}
                        self.sendDWG(self.create_header(), sdata)
                        logging.info('[DATA] Sending USSD to port %s to number %s' % (port, number))
                os.remove(dwgconfig.ussd_send_path + files[0])
        self.check_t = Timer(self.check_timer, self.checkSMS)
        self.check_t.start()

    def stop_ping(self):
        if self.ping_t is not None:
            self.ping_t.cancel()
        if self.check_t is not None:
            self.check_t.cancel()
