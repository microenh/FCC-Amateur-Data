"""
Read a sqlite3 table.
No error checking.
overflow of payload data not handled

to use:
init the instance with the file name
find_call(<call>)
"""
import struct
import bisect

def varint(s, ofs):
    r = 0
    i = 0
    j = s[ofs]
    while (j & 128) and (i < 9):
        r = (r << 7) + (j & 127)
        i += 1
        j = s[ofs + i]
    if (i == 8):
        r = (r << 8) + j
    else:
        r = (r << 7) + j
    return r, i + 1


class SqliteReader:
    
    #full header decode format ">16sH6B12I20sII"
    #full page header decode format ">B3HB"
    
    def __init__(self, filename):
        self.filename = filename
        self.recbuffer = bytearray(100)
        with open(filename, "rb") as f:
            f.readinto(self.recbuffer)
            (self.page_size,
             dummy,
             reserved_space) = struct.unpack_from(">2HB", self.recbuffer, 16)
            if self.page_size == 1:
                self.page_size = 65536
            self.U = self.page_size - reserved_space # - hdr_ofs
            self.M = ((self.U - 12) * 32 // 255) - 23
            b1 = bytearray(self.page_size - 100)
            f.readinto(b1)
            self.recbuffer += b1
            b1 = None
        self._parse_page(100)
        self.roots = tuple([self._parse_payload(i,4) for i in self.cell_ofs])            
        
    def _read_page(self, f, i):
        f.seek((i - 1) * self.page_size)
        f.readinto(self.recbuffer)
        self._parse_page()
            
    def _parse_page(self, offset=0):
        (self.type,
         dummy,
         self.number_cells) = struct.unpack_from(">B2H", self.recbuffer, offset)
        offset += 8
        if self.type in (2, 5):
            self.right_child = struct.unpack_from(">I", self.recbuffer, offset)[0]
            offset += 4
        if self.type != 5:
            self.X = self.U - 35 if self.type == 0x0d else int(((self.U - 12) * 64 // 255) - 23)            
        # row_ids = []
        # payloads = []
        self.cell_ofs = struct.unpack_from(">%dH" % self.number_cells, self.recbuffer, offset)

    def _parse_payload(self, i, max=None):
        if self.type in (2,5):
            self.left_child = (struct.unpack_from(">I", self.recbuffer, i)[0])
            i += 4
        if self.type != 0x05:
            P, s = varint(self.recbuffer, i)
            i += s
            if P <= self.X:
                base_payload_size = P
            else:
                K = self.M + ((P - self.M) % (self.U - 4))
                if K <= self.X:
                    base_payload_size = K
                else:
                    base_payload_size = self.M
        if self.type in (0x0d, 0x05):
            self.row_id, s = varint(self.recbuffer, i)
            i += s
        if self.type != 0x05:
            if base_payload_size == P:
                overflow = 0
            else:
                overflow = struct.unpack_from(">I", self.recbuffer, i + base_payload_size)
            self.payload = self._parse_record(i, max)
            return self.payload
        
            
    def _parse_record(self, ofs, max):
        offset = ofs
        header_size,s = varint(self.recbuffer, offset)
        offset += s
        data_offset = header_size + ofs
        values = []
        ctr = 0
        while (offset < header_size + ofs):
            if max is not None and ctr == max:
                break
            ctr += 1
            i,s = varint(self.recbuffer, offset)
            offset += s
            if i == 0:  # NULL
                values.append(None)
            elif i == 1:  # 8-bit signed
                values.append(struct.unpack_from("b", self.recbuffer, data_offset)[0])
                data_offset += 1
            elif i == 2:  # 16-bit signed
                values.append(struct.unpack_from(">h", self.recbuffer, data_offset)[0])
                data_offset += 2
            elif i == 3:  # 24-bit signed
                v = struct.unpack_from(">hB", self.recbuffer, data_offset)
                values.append((v[0] << 8) + v[1])
                data_offset += 3
            elif i == 4:  # 32-bit signed
                values.append(struct.unpack_from(">i", self.recbuffer, data_offset)[0])
                data_offset += 4
            elif i == 5:  # 48-bit signed
                v = struct.unpack_from(">iH", self.recbuffer, data_offset)
                values.append((v[0] << 32) + v[1])
                data_offset += 6
            elif i == 6:  # 64-bit signed
                values.append(struct.unpack_from(">q", self.recbuffer, data_offset)[0])
                data_offset += 8
            elif i == 7:  # 64-bit float
                values.append(struct.unpack_from(">d", self.recbuffer, data_offset)[0])
                data_offset += 8
            elif i == 8: # 0
                values.append(0)
            elif i == 9: # 1
                values.append(1)
            elif i in (10,11): # invalid
                pass
            elif i & 1: # text
                ct = (i - 13) // 2
                # values.append(struct.unpack("%ds" % ct, r[data_offset:data_offset + ct])[0].decode())
                values.append(struct.unpack_from("%ds" % ct, self.recbuffer, data_offset)[0].decode())
                data_offset += ct
            else: # blob
                ct = (i - 12) // 2
                values.append(struct.unpack_from("%ds" % ct, self.recbuffer, data_offset)[0])
                offset += ct
        return tuple(values)
    
    def find_call(self, call):
        for root in self.roots:
            if root[0] == 'table' and root[1] == 'lookup':
                table_no = root[3]
                break
        with open(self.filename, "rb") as f:
            self._read_page(f, table_no)
            while (True):
                lo = 0
                hi = self.number_cells
                while lo < hi:
                    mid = (lo + hi) // 2
                    t = self._parse_payload(self.cell_ofs[mid],1)[0]
                    if t < call:
                        lo = mid + 1
                    else:
                        hi = mid
                if (lo != mid and lo != self.number_cells):
                    self._parse_payload(self.cell_ofs[lo],1)
                b = lo
                if b == self.number_cells:
                    if self.type == 0x02:
                        self._read_page(f, self.right_child)
                    else:
                        return "<%s> (max) Not found" % call
                elif (self.payload[0] == call):
                    return self._parse_payload(self.cell_ofs[b])
                elif self.type != 0x02:
                    return "<%s> Not found" % call
                else:
                    self._read_page(f, self.left_child)
                    
if __name__ == "__main__":
    import sys
    if sys.version.find("Micro") >= 0:
        import os
        import sdcard
        import machine
        cs = machine.Pin(22, machine.Pin.OUT)
        spi = machine.SPI(1, baudrate= 10000000, polarity=0, phase=0, bits=8,
                          firstbit=machine.SPI.MSB, sck=machine.Pin(10),
                          mosi=machine.Pin(11), miso=machine.Pin(12))
        sd = sdcard.SDCard(spi,cs)
        os.mount(sd, '/sd')
        # print (os.listdir('/sd'))
        db_file = "/sd/fcc.sqlite"
    else:
        db_file = "fcc.sqlite"
    r = SqliteReader(db_file)