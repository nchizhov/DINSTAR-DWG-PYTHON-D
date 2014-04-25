#!/usr/bin/env python
# -*- coding: utf-8 -*-
import dwgconfig
import socket
from struct import pack, unpack
from time import time, strftime
from random import randint
from sys import maxint, exit
from threading import Timer
import codecs
import os
from subprocess import Popen

ping_t = None
check_t = None

def listenDWG(conn):
    global ping_t, check_t
    Timer(45.0, pingDWG, [conn]).start()
    Timer(5.0, checkSMS, [conn]).start()
    while True:
        try:
            data = conn.recv(66560)
            if not data:
                break
            else:
                parseDWG(conn, data)
        except KeyboardInterrupt:
            exit()
        except:
            if not ping_t is None:
                ping_t.cancel()
            if not check_t is None:
                check_t.cancel()
            break
    conn.close()

def parseDWG(conn, data):
    if data:
        logger('[PROCESS] <- %s' % data.encode("hex"), True)
        header = {'len': unpack('!L', data[0:4])[0],
                  'id': {'mac': unpack('!6s', data[4:10])[0],
                         'time': unpack('!L', data[12:16])[0],
                         'serial': unpack('!L', data[16:20])[0]},
                  'type': unpack('!H', data[20:22])[0],
                  'flag': unpack('!H', data[22:24])[0]}
        sdata = parseType(header['type'], data[24:])
        if sdata['type']:
            sendDWG(conn, header, sdata)



def parseType(htype, data):
    sdata = {'type': 0,
             'body': ''}
    if htype == 7:   # Status message
        sdata['type'] = 8
        sdata['body'] = pack('!?', False)
    elif htype == 5:   # Recieve message
        body = {'number': unpack('!24s', data[0:24])[0].replace('\x00', ''),
                'type': unpack('!B', data[24])[0],
                'port': unpack('!B', data[25])[0],
                'timestamp': unpack('!15s', data[26:41])[0].replace('\x00', ''),
                'timezone': unpack('!b', data[41])[0],
                'encoding': unpack('!B', data[42])[0],
                'length': unpack('!H', data[43:45])[0]}
        body['content'] = unpack('!%ds' % body['length'], data[45:])[0]
        saveSMS(body)
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
        saveUSSD(body)
        sdata['type'] = 12
        sdata['body'] = pack('!?', False)
    elif htype == 15:   # Auth for API 2.0
        body = {'login': unpack('!16s', data[0:16])[0].replace('\x00', ''),
                'password': unpack('!16s', data[16:])[0].replace('\x00', '')}
        if body['login'] == dwgconfig.login and body['password'] == dwgconfig.password:
            sdata['type'] = 16
            sdata['body'] = pack('!?', False)
            logger('[SYSTEM] Authentication success', False)
        else:
            logger('[SYSTEM] Authentication failed', False)
    return sdata

def pingDWG(conn):
    global ping_t
    sdata = {'type': 0,
             'body': ''}
    sendDWG(conn, create_header(), sdata)
    ping_t = Timer(45.0, pingDWG, [conn])
    ping_t.start()

def sendDWG(conn, header, sdata):
    global ping_t
    pkt = pack('!L', len(sdata['body']))
    pkt += pack('!6s', header['id']['mac']) + "\x00\x00"
    pkt += pack('!L', header['id']['time'])
    pkt += pack('!L', header['id']['serial'])
    pkt += pack('!H', sdata['type'])
    pkt += pack('!H', 0)
    pkt += sdata['body']
    logger('[PROCESS] -> %s' % pkt.encode("hex"), True)
    conn.send(pkt)

def create_header():
    return {'id': {'mac': '\x00\xfa\xb3\xd2\xd3\xaa',
                   'time': int(time()),
                   'serial': randint(1, maxint - 1)}}

def logger(message, debug):
    now = strftime('%d.%m.%Y %H:%M:%S')
    if debug and dwgconfig.debug:
        print '[%s] %s' % (now, message)
    elif not debug:
        print '[%s] %s' % (now, message)

"""
Parsing different messages from Gateway
"""
def saveSMS(body):
    try:
        sms = codecs.open('%s%s.%s' % (dwgconfig.income_path, body['number'], int(time())), 'w', 'utf-8')
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
        logger('[DATA] Received SMS from number %s' % body['number'], False)
    except:
        logger('[DATA] Received unknown SMS', False)

def saveUSSD(body):
    try:
        ussd = codecs.open('%s%s.%s' % (dwgconfig.ussd_income_path, body['port'], int(time())), 'w', 'utf-8')
        ussd.write('Port: %s\n' % body['port'])
        ussd.write('Time: %s\n' % strftime('%d%m%Y%H%M%S'))
        ussd.write('Status: %s\n' % body['status'])
        ussd.write('Encoding: %s\n\n'% body['encoding'])
        if body['encoding'] == 0:
            ussd.write(''.join([unichr(int(body['content'][pos:pos+4], 16)) for pos in range(0, len(body['content']), 4)]))
        elif body['encoding'] == 1:
            ussd.write(body['content'].decode('utf-16-be'))
        ussd.close()
        logger('[DATA] Received USSD from port %s' % body['port'], False)
    except:
        logger('[DATA] Received unknown USSD', False)

"""
Prepare messages for Gateway
"""
def checkSMS(conn):
    global check_t
    files = [f for f in os.listdir(dwgconfig.send_path) if os.path.isfile(os.path.join(dwgconfig.send_path, f))]
    if len(files):
        sms = codecs.open(dwgconfig.send_path + files[0], 'r', 'utf-8').readlines()
        f_send = True
        if len(sms) > 2:
            try:
                number = str(sms[0].strip())
                if not number.isdigit(): f_send = False
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
                sendDWG(conn, create_header(), sdata)
                logger('[DATA] Sending SMS to number %s' % number, False)
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
                    sendDWG(conn, create_header(), sdata)
                    logger('[DATA] Sending USSD to port %s to number %s' % (port, number), False)
            os.remove(dwgconfig.ussd_send_path + files[0])
    check_t = Timer(5.0, checkSMS, [conn])
    check_t.start()


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(('', dwgconfig.port))
sock.listen(1)
logger('[SYSTEM] Server listening...', False)

try:
    while True:
        conn, addr = sock.accept()
        logger('[SYSTEM] Gateway connected %s' % addr[0], False)
        listenDWG(conn)
        logger('[SYSTEM] Gateway disconnected', False)
except KeyboardInterrupt:
            exit()
finally:
    sock.close()