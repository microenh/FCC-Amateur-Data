import struct

class HDR:
    def __init__(self, f):
        f.seek(0)
        (self.header_string,
         self.page_size,
         self.file_format_write,
         self.file_format_read,
         self.reserved_space,
         self.max_embedded_payload,
         self.min_embedded_payload,
         self.leaf_payload_fraction,
         self.file_change_counter,
         self.database_file_size,
         self.first_freelist,
         self.freelist_count,
         self.schema_cookie,
         self.schema_format,
         self.default_cache,
         self.largest_btree,
         self.text_encoding,
         self.user_version,
         self.incremental_vacuum,
         self.application_id,
         self.reserved,
         self.version_valid_for,
         self.sqlite_version) = struct.unpack(">16sH6B12I20sII", f.read(100))
        if self.page_size == 1:
            self.page_size = 65536