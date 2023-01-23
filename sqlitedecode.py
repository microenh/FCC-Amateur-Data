import bisect

from sqlite_header import HDR
from sqlite_page import PAGE

def find(call, file=None):
    if file is None:
        file = db_file
    with open(file, "rb") as f:
        h = HDR(f)
        p = PAGE(f, 1, h)
        table_no = None
        for payload in p.payloads:
            if payload[0] == 'table' and payload[1] == 'lookup':
                table_no = payload[3]
        if table_no is None:
            return 'lookup table not found'
        p = PAGE(f, table_no, h)
        while (True):
            b = bisect.bisect_left(p.payloads, call, key = lambda i: i[0])
            if (b < len(p.payloads)) and (p.payloads[b][0] == call):
                return p.payloads[b]
            elif p.type != 0x02:
                return "%s Not found" % call
            else:
                p = PAGE(f, p.children[b], h)
                 
    
if __name__ == "__main__":
    import sys
    global db_file
    if sys.version.find("Micro") >= 0:
        import os
        import sdcard
        import machine
        cs = machine.Pin(22, machine.Pin.OUT)
        spi = machine.SPI(1, baudrate= 1000000, polarity=0, phase=0, bits=8,
                          firstbit=machine.SPI.MSB, sck=machine.Pin(10),
                          mosi=machine.Pin(11), miso=machine.Pin(12))
        sd = sdcard.SDCard(spi,cs)
        os.mount(sd, '/sd')
        # print (os.listdir('/sd'))
        db_file = "/sd/fcc.sqlite"
        print ("Pico")
    else:
        db_file = "fcc.sqlite"
        print ("desktop")
    
    
    
    