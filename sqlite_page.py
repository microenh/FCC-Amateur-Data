import struct
from sqlite_header import HDR

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

def parse_record(r, ofs):
    offset = ofs
    header_size,s = varint(r, offset)
    offset += s
    data_offset = header_size + ofs
    values = []
    while (offset < header_size + ofs):
        i,s = varint(r, offset)
        offset += s
        if i == 0:  # NULL
            values.append(None)
        elif i == 1:  # 8-bit signed
            values.append(struct.unpack_from("b", r, data_offset)[0])
            data_offset += 1
        elif i == 2:  # 16-bit signed
            values.append(struct.unpack_from(">h", r, data_offset)[0])
            data_offset += 2
        elif i == 3:  # 24-bit signed
            v = struct.unpack_from(">hB", r, data_offset)
            values.append((v[0] << 8) + v[1])
            data_offset += 3
        elif i == 4:  # 32-bit signed
            values.append(struct.unpack_from(">i", r, data_offset)[0])
            data_offset += 4
        elif i == 5:  # 48-bit signed
            v = struct.unpack_from(">iH", r, data_offset)
            values.append((v[0] << 32) + v[1])
            data_offset += 6
        elif i == 6:  # 64-bit signed
            values.append(struct.unpack_from(">q", r, data_offset)[0])
            data_offset += 8
        elif i == 7:  # 64-bit float
            values.append(struct.unpack_from(">d", r, data_offset)[0])
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
            values.append(struct.unpack_from("%ds" % ct, r, data_offset)[0].decode())
            data_offset += ct
        else: # blob
            ct = (i - 12) // 2
            values.append(struct.unpack_from("%ds" % ct, r, data_offset)[0])
            offset += ct
    return tuple(values)

class PAGE:
    TYPES = {
        0x02: "Index Interior",
        0x05: "Table Interior",
        0x0a: "Index Leaf",
        0x0d: "Table Leaf"
    }
    

    def __init__(self, f, i, header=None):
        p = bytearray(header.page_size)
        if header is None:
            header = HDR(f)
        i -= 1
        f.seek(i * header.page_size)
        f.readinto(p)
        hdr_ofs = 100 if i == 0 else 0
        (self.type,
         first_freeblock,
         number_cells,
         cell_content,
         fragment) = struct.unpack_from(">B3HB", p, hdr_ofs)
        if self.type != 5:
            X = header.U - 35 if self.type == 0x0d else int(((header.U - 12) * 64 // 255) - 23)            
        if cell_content == 0:
            cell_content = 65536
        hdr_ofs += 8
        if self.type in (0x05, 0x02):
            right_child = struct.unpack_from(">I", p, hdr_ofs)[0]
            hdr_ofs += 4
            
        cell_ofs = struct.unpack_from(">%dH" % number_cells, p, hdr_ofs)
        i_cell_ofs = 0
        
        if self.type in (0x05, 0x02):
            left_child = [struct.unpack_from(">I", p, i)[0] for i in cell_ofs]
            if left_child is None:
                self.children = (right_child,)
            else:
                left_child.append(right_child)
                self.children = tuple(left_child)
            i_cell_ofs += 4
        else:
            self.children = ()
            
        row_ids = []
        payloads = []
        for i in cell_ofs:
            s_ofs = 0
            if self.type != 0x05:
                P, s = varint(p, i + i_cell_ofs)
                s_ofs += s
                if P <= X:
                    base_payload_size = P
                else:
                    K = M + ((P - M) % (U - 4))
                    if K <= X:
                        base_payload_size = K
                    else:
                        base_payload_size = M
            if self.type in (0x0d, 0x05):
                ri, s = varint(p, i + i_cell_ofs + s_ofs)
                s_ofs += s
                row_ids.append(ri)
            if self.type != 0x05:
                payload_ofs = i + i_cell_ofs + s_ofs
                s_ofs += base_payload_size
                if base_payload_size == P:
                    overflow = 0
                else:
                    overflow = struct.unpack_from(">I", p, i + i_cell_ofs + s_ofs)[0]
                while overflow > 0:
                    print ("overflow = %d" % overflow)
                    f.seek(overflow * header.page_size)
                    of = f.read(header.page_size)
                    overflow = struct.unpack(">I", of[:4])
                    payload += of[4:]
                payloads.append(parse_record(p, payload_ofs))
            
        self.row_ids = tuple(row_ids)
        # self.payload_sizes = tuple(payload_sizes)
        # self.base_payload_sizes = tuple(base_payload_sizes)
        self.payloads = tuple(payloads)

        
    def __repr__(self):
        return """
Type: {0}
cell count: {1}
children: {2}
row_ids: {3}
""".format(PAGE.TYPES[self.type], len(self.payloads), self.children, self.row_ids)

