import sqlite3
import struct
import time
import bisect
from btreedisk import BTree, BTreeReader

sqlite_db_name = "fcc.sqlite"
flat_db_name = "FCC_Calls"

node_size = 171
key_size = 10
fmt = "10s2s10s10s10s1s10s10s50s1s200s20s1s20s3s60s20s2s9s20s35s10s"
rec_len = struct.calcsize(fmt)
B = BTree(flat_db_name, fmt, node_size, key_size)

def make(make_flat_db = False):
    query = """
        select
            callsign,
            radio_service_code,
            grant_date,
            expired_date,
            cancellation_date,
            operator_class,
            previous_callsign,
            trustee_callsign,
            trustee_name,
            applicant_type_code,
            entity_name,
            first_name,
            mi,
            last_name,
            suffix,
            street_address,
            city,
            state,
            zip_code,
            po_box,
            attention_line,
            frn
        from lookup
    """
    con = sqlite3.connect(sqlite_db_name)
    cur = con.cursor()
    res = cur.execute(query)
    x = res.fetchone()
    rec = 0
    
    if make_flat_db:
        print ("Building BTree and flat file")
        with open(flat_db_name + ".db", "wb") as f:
            while x is not None:
                B.insert(x[0], rec)
                rec += 1
                if (rec % 100000 == 0):
                    print (rec, end=" ")
                y = (bytes(i, 'utf-8') for i in x)
                r = struct.pack(fmt, *y)
                f.write(r)
                x = res.fetchone()
    else:
        print ("Building just BTree")
        while x is not None:
            B.insert(x[0], rec)
            rec += 1
            if (rec % 100000 == 0):
                print (rec, end=" ")
            x = res.fetchone()
    B.save()
    print("")
    print("Found %d records" % rec)
    cur.close()
    con.close()
    
def lookup(call):
    r1 = B.find(call)
    print (call, "Not found" if r1 is None else r1[10])
    

def test_good():
    test_lookup_good = (
            "AA0A",
            "AA0AA",
            "AA0AB",
            "N8ME",
            "W8NX",
            "WA8KKN",
            "W8CR",
            "N8CWU",
            "WZ9Y",
            "WZ9Z",
            "WZ9ZZZ",
    )
    print ("")
    print ("Testing known good")
    for call in test_lookup_good:
        lookup(call)


def test_bad():
    test_lookup_bad = (
            "-",
            "N8ME-",
            "Z"
    )
    print ("")
    print ("Testing known bad")
    for call in test_lookup_bad:
        lookup(call)

def test_all():
    query_call = "select callsign from lookup"
    query_count = "select count(*) from lookup"
    print ("")
    con = sqlite3.connect(sqlite_db_name)
    cur = con.cursor()
    res = cur.execute(query_count)
    x = res.fetchone()
    print ("Testing all %d calls" % x[0])
    res = cur.execute(query_call)
    x = res.fetchone()
    rec = 0
    found = 0
    while x is not None:
        rec += 1
        if rec % 100000 == 0:
            print (rec, end=" ")
        if B.find(x[0]) is None:
            print ("")
            print ("%s not found!" % x[0])
        else:
            found += 1
        x = res.fetchone()
    cur.close()
    con.close()
    print ("")
    print ("Tested %d calls, found %d" % (rec, found))
    print ("")
    
def node_sizes():
    max_keys = 0
    max_children = 0
    for i in B.nodes:
        k = len(i.keys)
        if k > max_keys:
            max_keys = k
        c = len(i.child)
        if c > max_children:
            max_children = c
    print ("max keys: %d, max children: %d" % (max_keys, max_children))
    

if __name__ == "__main__":
    s = time.time()
    make(True)
    print ("Elapsed %.2f seconds " % (time.time() - s))
    print ("nodes = %d" % len(B.nodes))
    node_sizes()
    
    print ("")
    print ("Using Memory")
    test_good()
    test_bad()
#     test_all()
    
    B = BTreeReader(flat_db_name, fmt)
    
    print("")
    print ("Using Disk")
    test_good()
    test_bad()
#     # test_all()
    
    print ("")
    print ("Done")
            
