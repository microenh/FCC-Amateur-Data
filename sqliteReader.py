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
    
    def __init__(self, filename):
        self.filename = filename
        self.recbuffer = bytearray(100)
        with open(filename, "rb") as f:
            f.readinto(self.recbuffer)
            (header_string,
             self.page_size,
             file_format_write,
             file_format_read,
             self.reserved_space,
             max_embedded_payload,
             min_embedded_payload,
             leaf_payload_fraction,
             file_change_counter,
             database_file_size,
             first_freelist,
             freelist_count,
             schema_cookie,
             schema_format,
             default_cache,
             largest_btree,
             text_encoding,
             user_version,
             incremental_vacuum,
             application_id,
             reserved,
             version_valid_for,
             sqlite_version) = struct.unpack(">16sH6B12I20sII", self.recbuffer)
            if self.page_size == 1:
                self.page_size = 65536
            self.U = self.page_size - self.reserved_space # - hdr_ofs
            self.M = ((self.U - 12) * 32 // 255) - 23
            b1 = bytearray(self.page_size - 100)
            f.readinto(b1)
            self.recbuffer += b1
            b1 = None
        self._parse_page(100)
        self.roots = tuple([i[:4] for i in self.payloads])
        
    def _read_page(self, f, i):
        f.seek((i - 1) * self.page_size)
        f.readinto(self.recbuffer)
        self._parse_page()
            
    def _parse_page(self, offset=0):
        (self.type,
         first_freeblock,
         number_cells,
         cell_content,
         fragment) = struct.unpack_from(">B3HB", self.recbuffer, offset)
        if cell_content == 0:
            cell_content = 65536
        offset += 8
        if self.type in (2, 5):
            right_child = struct.unpack_from(">I", self.recbuffer, offset)[0]
            offset += 4
        if self.type != 5:
            X = self.U - 35 if self.type == 0x0d else int(((self.U - 12) * 64 // 255) - 23)            
        row_ids = []
        payloads = []
        left_child = []
        cell_ofs = struct.unpack_from(">%dH" % number_cells, self.recbuffer, offset)

        for i in cell_ofs:
            if self.type in (2,5):
                left_child.append(struct.unpack_from(">I", self.recbuffer, i)[0])
                i += 4
            if self.type != 0x05:
                P, s = varint(self.recbuffer, i)
                i += s
                if P <= X:
                    base_payload_size = P
                else:
                    K = self.M + ((P - self.M) % (self.U - 4))
                    if K <= X:
                        base_payload_size = K
                    else:
                        base_payload_size = M
            if self.type in (0x0d, 0x05):
                ri, s = varint(self.recbuffer, i)
                i += s
                row_ids.append(ri)
            if self.type != 0x05:
                if base_payload_size == P:
                    overflow = 0
                else:
                    overflow = struct.unpack_from(">I", self.recbuffer, i + base_payload_size)
                payloads.append(self._parse_record(i))
        
        if self.type in (2,5):
            left_child.append(right_child)
            self.children = tuple(left_child)
        else:
            self.children = ()
        self.row_ids = tuple(row_ids)
        self.payloads = tuple(payloads)
            
    def _parse_record(self, ofs):
        offset = ofs
        header_size,s = varint(self.recbuffer, offset)
        offset += s
        data_offset = header_size + ofs
        values = []
        while (offset < header_size + ofs):
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
                b = bisect.bisect_left(self.payloads, call, key = lambda i: i[0])
                if (b < len(self.payloads)) and (self.payloads[b][0] == call):
                    return self.payloads[b]
                elif self.type != 0x02:
                    return "<%s> Not found" % call
                else:
                    self._read_page(f, self.children[b])
                    
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