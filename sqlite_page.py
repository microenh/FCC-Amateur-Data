import struct

def varint(s):
    r = 0
    i = 0
    while (s[i] & 128) and (i < 9):
        r = (r << 7) + (s[i] & 127)
        i += 1
    if (i == 8):
        r = (r << 8) + s[i]
    else:
        r = (r << 7) + s[i]
    return r,i+1

def parse_record(r):
    offset = 0
    header_size,s = varint(r)
    offset += s
    serial = []
    while (offset < header_size):
        si,s = varint(r[offset:])
        serial.append(si)
        offset += s
    values = []
    for i in serial:
        if i == 0:  # NULL
            values.append(None)
        elif i == 1:  # 8-bit signed
            values.append(struct.unpack("b", r[offset:offset + 1])[0])
            offset += 1
        elif i == 2:  # 16-bit signed
            values.append(struct.unpack(">h", r[offset:offset + 2])[0])
            offset += 2
        elif i == 3:  # 24-bit signed
            v = struct.unpack(">hB", r[offset: offset + 3])
            values.append((v[0] << 8) + v[1])
            offset += 3
        elif i == 4:  # 32-bit signed
            values.append(struct.unpack(">i", r[offset:offset + 2])[0])
            offset += 4
        elif i == 5:  # 48-bit signed
            v = struct.unpack(">iH", r[offset: offset + 3])
            values.append((v[0] << 32) + v[1])
            offset += 6
        elif i == 6:  # 64-bit signed
            values.append(struct.unpack(">q", r[offset:offset + 2])[0])
            offset += 8
        elif i == 7:  # 64-bit float
            values.append(struct.unpack(">d", r[offset:offset + 2])[0])
            offset += 8
        elif i == 8: # 0
            values.append(0)
        elif i == 9: # 1
            values.append(1)
        elif i in (10,11): # invalid
            pass
        elif i & 1: # text
            ct = (i - 13) // 2
            values.append(struct.unpack("%ds" % ct, r[offset: offset + ct])[0].decode())
            offset += ct
        else: # blob
            ct = (i - 12) // 2
            values.append(struct.unpack("%ds" % ct, r[offset: offset + ct])[0])
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
        if header is None:
            header = HDR(f)
        i -= 1
        f.seek(i * header.page_size)
        p = f.read(header.page_size)
        if i == 0:
            hdr_ofs = 100
        else:
            hdr_ofs = 0
        (self.type,
         self.first_freeblock,
         self.number_cells,
         self.cell_content,
         self.fragment) = struct.unpack(">B3HB", p[hdr_ofs:hdr_ofs + 8])
        if self.cell_content == 0:
            self.cell_content = 65536
        if self.type in (2,5):
            right_child = struct.unpack(">I", p[hdr_ofs + 8: hdr_ofs + 12])[0]
            co_ofs = hdr_ofs + 12
        else:
            co_ofs = hdr_ofs + 8
            
        self.cell_ofs = struct.unpack(">%dH" % self.number_cells, p[co_ofs: co_ofs + self.number_cells * 2])
        i_cell_ofs = 0
        U = header.page_size - header.reserved_space # - hdr_ofs
        M = ((U - 12) * 32 // 255) - 23
        if self.type == 0x0d:
            X = U - 35
        else:
            X = int(((U - 12) * 64 // 255) - 23)
        if self.type in (0x05, 0x02):
            left_child = [struct.unpack(">I", p[i:i+4])[0] for i in self.cell_ofs]
            if left_child is None:
                self.children = (right_child,)
            else:
                left_child.append(right_child)
                self.children = tuple(left_child)
            i_cell_ofs += 4
        else:
            self.children = ()
        row_ids = []
        payload_sizes = []
        base_payload_sizes = []
        payloads = []
        for i in self.cell_ofs:
            s_ofs = 0
            if self.type != 0x05:
                P, s = varint(p[i + i_cell_ofs:])
                s_ofs += s
                payload_sizes.append(P)
                if P <= X:
                    base_payload_size = P
                else:
                    K = M + ((P - M) % (U - 4))
                    if K <= X:
                        base_payload_size = K
                    else:
                        base_payload_size = M
                base_payload_sizes.append(base_payload_size)
            if self.type in (0x0d, 0x05):
                ri, s = varint(p[i + i_cell_ofs + s_ofs:])
                s_ofs += s
                row_ids.append(ri)
            if self.type != 0x05:
                payload = p[i + i_cell_ofs + s_ofs: i + i_cell_ofs + s_ofs + base_payload_size]
                s_ofs += base_payload_size
                if base_payload_size == P:
                    overflow = 0
                else:
                    overflow = struct.unpack(">I", p[i + i_cell_ofs + s_ofs: i + i_cell_ofs + s_ofs + 4])[0]
                while overflow > 0:
                    print ("overflow = %d" % overflow)
                    f.seek(overflow * header.page_size)
                    of = f.read(header.page_size)
                    overflow = struct.unpack(">I", of[:4])
                    payload += of[:4]
                # print (r.type)
                payloads.append(parse_record(payload))
                # payloads.append(payload)
            
        self.row_ids = tuple(row_ids)
        self.payload_sizes = tuple(payload_sizes)
        self.base_payload_sizes = tuple(base_payload_sizes)
        self.payloads = tuple(payloads)

        
    def __repr__(self):
        return """
Type: {0}
cell count: {1}
children: {2}
row_ids: {3}
payload sizes: {4}
""".format(self.type_str(), self.number_cells, self.children, self.row_ids, self.payload_sizes)

