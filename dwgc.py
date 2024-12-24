import dwgconfig
from threading import Timer, Thread
from struct import pack, unpack
from random import randint
from sys import exit
from time import time, strftime
import codecs
import os
import logging
from subprocess import Popen, DEVNULL, PIPE
from socket import socket


class DWGD:
    ping_t = None
    check_t = None
    conn = None
    ping_timer = 45.0
    check_timer = 5.0
    ping_count = 0

    def __init__(self, conn: socket) -> None:
        self.conn = conn
        Timer(self.ping_timer, self.ping_dwg).start()
        Timer(self.check_timer, self.check_sms).start()
        self.get_dwg()

    def get_dwg(self) -> None:
        """
        Listening DWG Client
        """
        while True:
            try:
                data = self.conn.recv(66560)
                if not data:
                    break
                else:
                    self.parse_dwg(data)
            except KeyboardInterrupt:
                exit()
            except:
                break
        self.stop_ping()
        self.conn.close()

    def parse_dwg(self, data: bytes) -> None:
        """
        Parsing DWG Messages
        """
        if data:
            logging.debug('[PROCESS] <- {data}'.format(data=data.hex()))
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
                sdata = self.parse_type(header['type'], data[24:data_len])
                if sdata['type']:
                    self.send_dwg(header, sdata)
                data = data[data_len:]

    def parse_type(self, htype: int, data: bytes) -> dict:
        """
        Parsing DWG Types
        """
        sdata = {'type': 0,
                 'body': b''}
        if htype == 0:  # received keep alive
            self.ping_count = 0
        elif htype == 7:   # Status message
            sdata['type'] = 8
            sdata['body'] = pack('!?', False)
        elif htype == 5:   # Receive message
            body = {'number': unpack('!24s', data[0:24])[0].replace(b'\x00', b'').decode('ascii'),
                    'type': unpack('!B', data[24:25])[0],
                    'port': unpack('!B', data[25:26])[0],
                    'timestamp': unpack('!15s', data[26:41])[0].replace(b'\x00', b'').decode('ascii'),
                    'timezone': unpack('!b', data[41:42])[0],
                    'encoding': unpack('!B', data[42:43])[0],
                    'length': unpack('!H', data[43:45])[0]}
            body['content'] = unpack('!{len}s'.format(len=body['length']), data[45:])[0]
            self.save_sms(body)
            sdata['type'] = 6
            sdata['body'] = pack('!?', False)
        elif htype == 3:  # SMS Result
            sdata['type'] = 4
            sdata['body'] = pack('!?', False)
        elif htype == 11:  # USSD Result
            body = {'port': unpack('!B', data[0:1])[0],
                    'status': unpack('!B', data[1:2])[0],
                    'length': unpack('!H', data[2:4])[0],
                    'encoding': unpack('!B', data[4:5])[0]}
            body['content'] = unpack('!{len}s'.format(len=body['length']), data[5:])[0]
            self.save_ussd(body)
            sdata['type'] = 12
            sdata['body'] = pack('!?', False)
        elif htype == 15:   # Auth for API 2.0
            body = {'login': unpack('!16s', data[0:16])[0].replace(b'\x00', b''),
                    'password': unpack('!16s', data[16:])[0].replace(b'\x00', b'')}
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

    def ping_dwg(self) -> None:
        """
        Ping DWG
        """
        if self.ping_count > 2:
            self.stop_ping()
            self.conn.close()
        else:
            sdata = {'type': 0,
                     'body': b''}
            self.ping_count += self.ping_count
            self.send_dwg(self.create_header(), sdata)
            self.ping_t = Timer(self.ping_timer, self.ping_dwg)
            self.ping_t.start()

    def send_dwg(self, header: dict, sdata: dict) -> None:
        """
        Sending message to DWG
        """
        pkt = pack('!L', len(sdata['body']))
        pkt += pack('!6s', header['id']['mac']) + b'\x00\x00'
        pkt += pack('!L', header['id']['time'])
        pkt += pack('!L', header['id']['serial'])
        pkt += pack('!H', sdata['type'])
        pkt += pack('!H', 0)
        pkt += sdata['body']
        logging.debug('[PROCESS] -> {data}'.format(data=pkt.hex()))
        self.conn.send(pkt)

    def create_header(self) -> dict:
        """
        Create headers for DWG
        """
        return {'id': {'mac': b'\x00\xfa\xb3\xd2\xd3\xaa',
                       'time': int(time()),
                       'serial': randint(1, 1000000)}}

    def save_sms(self, body: dict) -> None:
        """
        Saving SMS to file
        """
        try:
            filename = '{number}.{time}'.format(number=body['number'],
                                                time=int(time()))
            sms_partfilename = os.path.join(dwgconfig.income_path, filename)
            sms_filename = self.format_filename(sms_partfilename)
            while os.path.isfile(sms_filename):
                sms_filename = self.format_filename(sms_partfilename)
            sms = codecs.open(sms_filename, 'w', 'utf-8')
            sms.write('Number: {number}\n'.format(number=body['number']))
            sms.write('Port: {port}\n'.format(port=body['port']))
            sms.write('Time: {time}\n'.format(time=body['timestamp']))
            sms.write('Timezone: {timezone}\n'.format(timezone=body['timezone']))
            sms.write('Encoding: {encoding}\n\n'.format(encoding=body['encoding']))
            if body['encoding'] == 0:
                sms.write(body['content'].decode('ascii'))
            elif body['encoding'] == 1:
                sms.write(body['content'].decode('utf-16-be'))
            sms.close()
            if dwgconfig.run_program is not None:
                thread = Thread(target=self.run_program, daemon=True)
                thread.start()
                thread.join()
            logging.info('[DATA] Received SMS from number {number}'.format(number=body['number']))
        except:
            logging.info('[DATA] Received unknown SMS')

    def save_ussd(self, body: dict) -> None:
        """
        Saving USSD to file
        """
        try:
            filename = '{port}.{time}'.format(port=body['port'],
                                              time=int(time()))
            ussd_partfilename = os.path.join(dwgconfig.ussd_income_path, filename)
            ussd_filename = self.format_filename(ussd_partfilename)
            while os.path.isfile(ussd_filename):
                ussd_filename = self.format_filename(ussd_partfilename)
            ussd = codecs.open(ussd_filename, 'w', 'utf-8')
            ussd.write('Port: {port}\n'.format(port=body['port']))
            ussd.write('Time: {time}\n'.format(time=strftime('%d%m%Y%H%M%S')))
            ussd.write('Status: {status}\n'.format(status=body['status']))
            ussd.write('Encoding: {encoding}\n\n'.format(encoding=body['encoding']))
            if body['encoding'] == 0:
                ussd.write(''.join([
                    chr(int(body['content'][pos:pos+4], 16)) for pos in range(0, len(body['content']), 4)
                ]))
            elif body['encoding'] == 1:
                ussd.write(body['content'].decode('utf-16-be'))
            ussd.close()
            logging.info('[DATA] Received USSD from port {port}'.format(port=body['port']))
        except:
            logging.info('[DATA] Received unknown USSD')

    def check_sms(self) -> None:
        """
        Check SMS/USSD in folders
        """
        files = [f for f in os.listdir(dwgconfig.send_path) if os.path.isfile(os.path.join(dwgconfig.send_path, f))]
        port = None
        number = None
        if len(files):
            sms_file = os.path.join(dwgconfig.send_path, files[0])
            sms = codecs.open(sms_file, 'r', 'utf-8').readlines()
            f_send = True
            if len(sms) > 2:
                try:
                    number = str(sms[0].strip())
                    # if not number.isdigit(): f_send = False
                except ValueError:
                    f_send = False
                try:
                    port = int(sms[1].strip())
                except ValueError:
                    f_send = False
                if f_send:
                    content = ''
                    for line in sms[2:]:
                        content += line.strip() + '\n'
                    content = content.strip().encode('utf-16-be')
                    content_len = len(content)
                    sdata = {'type': 1,
                             'body': pack('!BBBB24sH{len}s'.format(len=content_len),
                                          port, 1, 0, 1, number.encode(), content_len, content)}
                    self.send_dwg(self.create_header(), sdata)
                    logging.info('[DATA] Sending SMS to number {number}'.format(number=number))
            os.remove(sms_file)
        else:
            files = [f for f in os.listdir(dwgconfig.ussd_send_path)
                     if os.path.isfile(os.path.join(dwgconfig.ussd_send_path, f))]
            if len(files):
                ussd_file = os.path.join(dwgconfig.ussd_send_path, files[0])
                ussd = codecs.open(ussd_file, 'r', 'utf-8').readlines()
                f_send = True
                if len(ussd) > 1:
                    try:
                        port = int(ussd[0].strip())
                    except ValueError:
                        f_send = False
                    try:
                        number = str(ussd[1].strip())
                    except ValueError:
                        f_send = False
                    if f_send:
                        number_len = len(number)
                        sdata = {'type': 9,
                                 'body': pack('!BBH{len}s'.format(len=number_len),
                                              port, 1, number_len, number.encode())}
                        self.send_dwg(self.create_header(), sdata)
                        logging.info('[DATA] Sending USSD to port {port} to number {number}'
                                     .format(port=port, number=number))
                os.remove(ussd_file)
        self.check_t = Timer(self.check_timer, self.check_sms)
        self.check_t.start()

    def run_program(self):
        sp = Popen(dwgconfig.run_program, shell=True, stdout=DEVNULL, stderr=PIPE)
        sp_output = sp.communicate()[1]
        if sp.returncode != 0:
            logging.error('[SYSTEM] Cannot run program {program}: {error}'.format(program=dwgconfig.run_program,
                                                                                  error=sp_output.decode().strip()))

    def format_filename(self, path: str) -> str:
        return '{path}.{rand}'.format(path=path,
                                      rand=randint(1, 999999))

    def stop_ping(self) -> None:
        if self.ping_t is not None:
            self.ping_t.cancel()
        if self.check_t is not None:
            self.check_t.cancel()
