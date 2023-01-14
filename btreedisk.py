import bisect
import struct

# Create a node
class BTreeNode:
    def __init__(self, index, leaf=False):
        self.index = index
        self.leaf = leaf
        self.keys = []
        self.records = []
        self.child = []


# Tree
class BTree:
    def __init__(self, dbName, fmt, t, keySize):
        self.db_fmt = fmt
        self.db_len = struct.calcsize(fmt)
        self.dbName = dbName
        self.nextNodeIndex = 0
        self.nodes = []
        self.root = self.newNode(True)
        self.t = t
        self.keySize = keySize
        self.ndx_fmt = (2 * t - 1) * ('%ds' % keySize) + (2 * t - 1) * 'I' + (2 * t) * 'H' + '?' + 'H'
        self.ndx_len = struct.calcsize(self.ndx_fmt)
        self.hdrFmt = "HHI"
        self.hdr_size = struct.calcsize(self.hdrFmt)
        
    def newNode(self, leaf=False):
        node = BTreeNode(self.nextNodeIndex, leaf)
        self.nextNodeIndex += 1
        self.nodes.append(node)
        return node.index    
    
    def nodeStruct(self, node):
        active = len(node.keys)
        k = (node.keys + (2 * self.t - 1) * [''])[:(2 * self.t - 1)]
        keys = (bytes(i, 'utf8') for i in k)
        records = (node.records + (2 * self.t - 1) * [0])[:(2 * self.t - 1)]
        children = (node.child + (2 * self.t) * [0])[:(2 * self.t)]
        # print ('active: %d, k: %d, records: %d, children: %d' % (active, len(k), len(records), len(children)))
        return struct.pack(self.ndx_fmt, *keys, *records, *children, node.leaf, active)
               
    def save(self):
        with open(self.dbName + ".ndx", "wb") as f:
            f.write(struct.pack(self.hdrFmt, self.keySize, self.t, self.root))
            for node in self.nodes:
                f.write(self.nodeStruct(node))
        
    # Insert node
    def insert(self, k, r = None):
        root = self.root
        if len(self.nodes[root].keys) == (2 * self.t) - 1:
            temp = self.newNode()
            self.root = temp
            self.nodes[temp].child.insert(0, root)
            self.split_child(temp, 0)
            self.insert_non_full(temp, k, r)
        else:
            self.insert_non_full(root, k, r)

    # Insert nonfull
    def insert_non_full(self, x, k, r):
        if self.nodes[x].leaf:
            i = bisect.bisect_left(self.nodes[x].keys, k)
            self.nodes[x].keys.insert(i, k)
            self.nodes[x].records.insert(i, r)
        else:
            i = bisect.bisect_left(self.nodes[x].keys, k)
            if len(self.nodes[self.nodes[x].child[i]].keys) == (2 * self.t) - 1:
                self.split_child(x, i)
                if k > self.nodes[x].keys[i]:
                    i += 1
            self.insert_non_full(self.nodes[x].child[i], k, r)

    # Split the child
    def split_child(self, x, i):
        t = self.t
        y = self.nodes[x].child[i]
        z = self.newNode(self.nodes[y].leaf)
        self.nodes[x].child.insert(i + 1, z)
        
        self.nodes[x].keys.insert(i, self.nodes[y].keys[t - 1])
        self.nodes[z].keys = self.nodes[y].keys[t: (2 * t) - 1]
        self.nodes[y].keys = self.nodes[y].keys[0: t - 1]
        
        self.nodes[x].records.insert(i, self.nodes[y].records[t - 1])
        self.nodes[z].records = self.nodes[y].records[t: (2 * t)]
        self.nodes[y].records = self.nodes[y].records[0: t]
        
        if not self.nodes[y].leaf:
            self.nodes[z].child = self.nodes[y].child[t: 2 * t]
            self.nodes[y].child = self.nodes[y].child[0: t]

    # Print the tree
    def print_tree(self, x, l=0):
        print("Level ", l, " ", len(self.nodes[x].keys), end=":")
        for i in self.nodes[x].keys:
            print(i, end=" ")
        print()
        l += 1
        if len(self.nodes[x].child) > 0:
            for i in self.nodes[x].child:
                self.print_tree(i, l)

    def find(self, key):
        rec = self.search_key(key)
        if rec is None:
            return None
        else:
            with open(self.dbName + ".db", "rb") as f:
                f.seek(rec * self.db_len)
                r = f.read(self.db_len)
            if len(r) == self.db_len:
                tmp = struct.unpack(self.db_fmt, r)
                d = tuple([i.decode('utf-8').partition('\0')[0] for i in tmp])
                return d
            else:
                return None
            
    # Search key in the tree
    def search_key(self, k, x=None):
        if x is not None:
            i = bisect.bisect_left(self.nodes[x].keys, k)
            if i < len(self.nodes[x].keys) and k == self.nodes[x].keys[i]:
                return self.nodes[x].records[i]
            elif self.nodes[x].leaf:
                return None
            else:
                return self.search_key(k, self.nodes[x].child[i])

        else:
            return self.search_key(k, self.root)


class BTreeReader:
    
    def __init__(self, dbName, rec_fmt):
        self.dbName = dbName
        self.rec_fmt = rec_fmt
        self.rec_len = struct.calcsize(rec_fmt)
        self.hdrFmt = "HHI"
        self.hdr_size = struct.calcsize(self.hdrFmt)
        with open(self.dbName + ".ndx", "rb") as f:
            r = f.read(self.hdr_size)
        # print ("len(r): %d" % len(r))
        self.keySize, self.t, self.root = struct.unpack(self.hdrFmt, r)
        self.fmt = (2 * self.t - 1) * ('%ds' % self.keySize) + (2 * self.t - 1) * 'I' + (2 * self.t) * 'H' + '?' + 'H'
        self.rec_size = struct.calcsize(self.fmt)
        
    def readNode(self, f, index):
        f.seek(self.hdr_size + self.rec_size * index)
        r = f.read(self.rec_size)
        data = struct.unpack(self.fmt, r)
        node = BTreeNode(index)
        node.keys = tuple([i.decode('utf-8').partition('\0')[0] for i in data[:( 2 * self.t - 1)]])
        node.records = data[(2 * self.t -1):(2 * (2 * self.t - 1))]
        node.child = data[(2 * (2 * self.t -1)):(2 * (2 * self.t - 1) + (2 * self.t))]
        node.leaf = data[-2]
        node.active = data[-1]
        return node
 
    def find(self, key):
        rec = self.search_key(key)
        if rec is None:
            return None
        else:
            with open(self.dbName + ".db", "rb") as f:
                f.seek(rec * self.rec_len)
                r = f.read(self.rec_len)
            if len(r) == self.rec_len:
                tmp = struct.unpack(self.rec_fmt, r)
                d = tuple([i.decode('utf-8').partition('\0')[0] for i in tmp])
                return d
            else:
                return None
 

    # Search key in the tree
    def search_key(self, k, x=None):
        with open(self.dbName + ".ndx", "rb") as f:
            if x is not None:
                node = self.readNode(f, x)
                i = bisect.bisect_left(node.keys[:node.active], k)
                if i < len(node.keys) and k == node.keys[i]:
                    return node.records[i]
                elif node.leaf:
                    return None
                else:
                    return self.search_key(k, node.child[i])
            else:
                return self.search_key(k, self.root)
            
                
        
        

def main():
    B = BTree(3, 4)

    for i in range(10):
        B.insert(i, 2 * i)

    B.print_tree(B.root)

    if B.search_key(8) is not None:
        print("\nFound")
    else:
        print("\nNot Found")


if __name__ == '__main__':
    main()
