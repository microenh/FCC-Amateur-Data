#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "sqliteReader.h"

struct HEADER {
  char header_string[16];
  uint16_t page_size;
  uint8_t write_version;
  uint8_t read_version;
  uint8_t reserved_space;
  uint8_t max_embedded;
  uint8_t min_embedded;
  uint8_t leaf_payload;
  uint32_t change_counter;
  uint32_t size;
  uint32_t first_freelist;
  uint32_t freelist_pages;
  uint32_t schema_cookie;
  uint32_t schema_format;
  uint32_t default_cache;
  uint32_t largest_root;
  uint32_t text_encoding;
  uint32_t user_version;
  uint32_t inc_vacuum;
  uint32_t application_id;
  char reserved[20];
  uint32_t version_valid;
  uint32_t sqlite_version;
};


#define convert32(value) ((0x000000ff & value) << 24) | ((0x0000ff00 & value) << 8) | \
                       ((0x00ff0000 & value) >> 8) | ((0xff000000 & value) >> 24)

#define convert16(value) ((0x00ff & value) << 8) | ((0xff00 & value) >> 8)

sqliteReader::sqliteReader(const char *name) {
  // printf("sizeof HEADER %lu\r\n", sizeof(HEADER));
  filename = (char *) malloc(strlen(name) + 1);
  strcpy(filename, name);
  cell_offset = NULL;

  FILE *f = fopen(filename, "rb");
  HEADER hdr;
  fread(&hdr, sizeof(HEADER), 1, f);
  
  page_size = convert16(hdr.page_size);

  U = page_size - hdr.reserved_space;
  M = ((U - 12) * 32 / 255) - 23;
  
  page_buffer = (uint8_t *) malloc(page_size);

  fread(page_buffer, page_size - sizeof(HEADER), 1, f);
  fclose(f);
  parse_page();
  // printf("cell_offset %d\r\n", cell_offset[0]);
  store = &sqliteReader::store_header;
  schema = (SCHEMA *)malloc(number_cells * sizeof(SCHEMA));
  for (uint16_t i=0; i<number_cells; i++) {
    data_dest = (void *)(schema + i);
    parse_payload(cell_offset[i] - 100);
    // printf("type: %s\r\nname: %s\r\ntbl_name: %s\r\nrootpage: %d\r\n\r\n",
    //   schema[i].type, schema[i].name, schema[i].tbl_name, schema[i].rootpage);
  }
  store = &sqliteReader::store_data;
  data_dest = (void *)&lookup;

}

void sqliteReader::parse_page() {
  uint16_t offset = 0;
  type = page_buffer[offset];
  max_number_cells = 0;
  number_cells = page_buffer[offset + 3] << 8 | page_buffer[offset + 4]; 
  offset = 8;
  if (type == 2 || type == 5) {
    right_child = page_buffer[offset] << 24
      | page_buffer[offset + 1] << 16
      | page_buffer[offset + 2] << 8
      | page_buffer[offset + 3];  
      offset += 4;
  }
  if (type != 5) {
    X = (type == 5) ? U - 35 : (U - 12) * 64 / 255 - 23;
  }
  if (number_cells > max_number_cells) {
    free(cell_offset);
    cell_offset = (uint16_t *)malloc(number_cells * 2);
    max_number_cells = number_cells;
  }
  memcpy(cell_offset, page_buffer + offset, number_cells * 2);
  for (int i=0; i<number_cells; i++) {
    cell_offset[i] = convert16(cell_offset[i]);
  }
  
}

void sqliteReader::parse_payload(uint16_t ofs, uint16_t max) {
  uint32_t base_payload_size;
  uint32_t P;
  uint16_t offset = ofs;
  if (type == 2 || type == 5) {
    left_child = page_buffer[offset] << 24
      | page_buffer[offset+1] << 16
      | page_buffer[offset+2] << 8
      | page_buffer[offset+3];  
      offset += 4;
  }
  if (type != 5) {
    P = varint(offset);
    if (P <= X) {
      base_payload_size = P;
    } else {
      uint16_t K = M + ((P - M) % (U - 4));
      base_payload_size = K < X ? K : M;
    }
    // printf("payload size = %u\r\n", P);
    // printf("base payload size = %u\r\n", base_payload_size);
  }
  if (type == 0xd || type == 5) {
    row_id = varint(offset);  
  }
  // printf("row_id = %d, offset = %d\r\n", row_id, offset);
  if (type != 5) {
    if (P == base_payload_size ) {
      overflow = 0;
    } else {
      uint16_t of_offset = offset + base_payload_size;
      overflow = page_buffer[of_offset] << 24
        | page_buffer[of_offset+1] << 16
        | page_buffer[of_offset+2] << 8
        | page_buffer[of_offset+3];  
    }
    parse_record(offset);
  }
}

void sqliteReader::parse_record(uint16_t ofs, uint16_t max) {
  uint16_t offset = ofs;
  uint32_t header_size = varint(offset);
  // printf("header_size = %u\r\n", header_size);
  uint32_t data_offset = header_size + ofs;
  uint16_t ctr = 0;
  uint32_t field_type;
  DB value;
  
  while (offset < header_size + ofs) {
    if (ctr == max) {
      break;
    } 
    field_type = varint(offset);
    // printf("field type: %u ", field_type);
    switch (field_type) {
      case 0:
        value.ptr = NULL;
        break;
      case 1:
        value.i = (int64_t)page_buffer[data_offset++];
        break;
      case 2:
        value.i = (int64_t)page_buffer[data_offset] << 8
              | (int64_t)page_buffer[data_offset+1];
        data_offset += 2;
        break;
      case 3:
        value.i = (int64_t)page_buffer[data_offset] << 16
              | (int64_t)page_buffer[data_offset+1] << 8
              | (int64_t)page_buffer[data_offset+2];
        data_offset += 3;
        break;
      case 4:
        value.i = (int64_t)page_buffer[data_offset] << 24
              | (int64_t)page_buffer[data_offset+1] << 16
              | (int64_t)page_buffer[data_offset+2] << 8
              | (int64_t)page_buffer[data_offset+3];
        data_offset += 4;
        break;
      case 5:
        value.i = (int64_t)page_buffer[data_offset] << 40
              | (int64_t)page_buffer[data_offset+1] << 32
              | (int64_t)page_buffer[data_offset+2] << 24
              | (int64_t)page_buffer[data_offset+3] << 16
              | (int64_t)page_buffer[data_offset+4] << 8
              | (int64_t)page_buffer[data_offset+5];
        data_offset += 6;
        break;
      case 6:
        value.i = (int64_t)page_buffer[data_offset] << 56
              | (int64_t)page_buffer[data_offset+1] << 48
              | (int64_t)page_buffer[data_offset+2] << 40
              | (int64_t)page_buffer[data_offset+3] << 32
              | (int64_t)page_buffer[data_offset+4] << 24
              | (int64_t)page_buffer[data_offset+5] << 16
              | (int64_t)page_buffer[data_offset+6] << 8
              | (int64_t)page_buffer[data_offset+7];
        data_offset += 8;
        break;
      case 7:
        memcpy(&value.f, page_buffer+data_offset, 8);
        data_offset += 8;
        break;
      case 8:
        value.i = 0;
        break;
      case 9:
        value.i = 1;
        break;
      case 10:
      case 11:
        break;
      default:
        value.ptr = page_buffer+data_offset;
        data_offset += ((field_type & ~1) - 12) / 2; 
        break;
    }
    // printf("\r\n");
    (*this.*store)(ctr, field_type, value);
    ctr++;
  }

}


void sqliteReader::save_string(uint16_t field_len, uint16_t target_len, char *dest, char *src) {
  uint16_t move_len = field_len < target_len ? field_len : target_len;
  memcpy(dest, src, move_len);
  *(dest + move_len) = 0;
}

#define SAVE_STRING(x) save_string(field_len, sizeof(x) - 1, x, (char *) data.ptr);

void sqliteReader::store_header(uint16_t field_no, uint32_t field_type, DB data){
  SCHEMA *schema = (SCHEMA *)data_dest;
  uint32_t field_len;
  if (field_type >= 12) {
    field_len = ((field_type & ~1) - 12) / 2; 
  }
  uint16_t move_len;
  switch (field_no) {
    case 0:
      SAVE_STRING(schema->type);
      break;
    case 1:
      SAVE_STRING(schema->name);
      break;
    case 2:
      SAVE_STRING(schema->tbl_name);
      break;
    case 3:
      schema->rootpage = data.i;
      break;
  }
}

void sqliteReader::store_data(uint16_t field_no, uint32_t field_type, DB data){
  LOOKUP *lookup = (LOOKUP *)data_dest;
  uint32_t field_len;
  if (field_type >= 12) {
    field_len = ((field_type & ~1) - 12) / 2; 
  }
  uint16_t move_len;
  switch (field_no) {
    case 0:
      SAVE_STRING(lookup->callsign)
      break;
    case 1:
      SAVE_STRING(lookup->radio_service_code);
      break;
    case 2:
      SAVE_STRING(lookup->grant_date);
      break;
    case 3:
      SAVE_STRING(lookup->expired_date);
      break;
    case 4:
      SAVE_STRING(lookup->cancellation_date);
      break;
    case 5:
      SAVE_STRING(lookup->operator_class);
      break;
    case 6:
      SAVE_STRING(lookup->previous_callsign);
      break;
    case 7:
      SAVE_STRING(lookup->trustee_callsign);
      break;
    case 8:
      SAVE_STRING(lookup->trustee_name);
      break;
    case 9:
      SAVE_STRING(lookup->applicant_type_code);
      break;
    case 10:
      SAVE_STRING(lookup->entity_name);
      break;
    case 11:
      SAVE_STRING(lookup->first_name);
      break;
    case 12:
      SAVE_STRING(lookup->mi);
      break;
    case 13:
      SAVE_STRING(lookup->last_name);
      break;
    case 14:
      SAVE_STRING(lookup->suffix);
      break;
    case 15:
      SAVE_STRING(lookup->street_address);
      break;
    case 16:
      SAVE_STRING(lookup->city);
      break;
    case 17:
      SAVE_STRING(lookup->state);
      break;
    case 18:
      SAVE_STRING(lookup->zip_code);
      break;
    case 19:
      SAVE_STRING(lookup->po_box);
      break;
    case 20:
      SAVE_STRING(lookup->attention_line);
      break;
    case 21:
      SAVE_STRING(lookup->frn);
      break;    
  }
}

uint32_t sqliteReader::varint(uint16_t &offset) {
  uint32_t r = 0;
  uint16_t i = 0;
  uint8_t j = page_buffer[offset++];
  while ((j & 0x80) && (i < 9)) {
    r = (r << 7 | j & 0x7f);
    i++;
    j = page_buffer[offset++];
  }
  return r << (i == 8 ? 8 : 7) | j;
}

void sqliteReader::read_page(FILE *f, uint32_t page) {
  fseek(f, (page-1) * page_size, SEEK_SET);
  fread((void *)page_buffer, page_size, 1, f);
  parse_page();
}

bool sqliteReader::lookup_call(const char *call) {
  uint32_t rootpage;
  uint32_t child;
  for (uint16_t i=0; i< number_cells; i++) {
    if (!strcmp(schema[i].type, "table") && !strcmp(schema[i].tbl_name,"lookup")) {
      rootpage = schema[i].rootpage;
      break;
    }
  }
  FILE *f = fopen(filename, "rb");
  read_page(f, rootpage);
  while (1) {
    uint16_t lo = 0;
    uint16_t hi = number_cells;
    uint16_t mid;
    int compare;
    while (lo < hi) {
      mid = (lo + hi) / 2;
      parse_payload(cell_offset[mid], 1);
      compare = strcmp(lookup.callsign, call);
      if (!compare) {
        parse_payload(cell_offset[mid]);
        return true;
      }
      if (compare < 0) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }
    if (type != 2) {
      return false;
    }
  
    if (lo == number_cells) {
      child = right_child;
    } else {
      if (lo != mid) {
        parse_payload(cell_offset[lo], 1);
      }
      child = left_child;
    }
    read_page(f, child);
  }

  fclose(f);

}

sqliteReader::~sqliteReader() {
  free(page_buffer);
  free(filename);
  free(cell_offset);
  free(schema);
}

