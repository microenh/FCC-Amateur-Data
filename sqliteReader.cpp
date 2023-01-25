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
  printf("cell_offset %d\r\n", cell_offset[0]);
  parse_payload(cell_offset[0] - 100);

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
  printf("row_id = %d, offset = %d\r\n", row_id, offset);
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
  printf("header_size = %u\r\n", header_size);
  uint32_t data_offset = header_size + ofs;
  uint32_t ctr = 0;
  uint32_t field_type;
  int32_t value;
  
  while (offset < header_size + ofs) {
    if (ctr == max) {
      break;
    } 
    field_type = varint(offset);
    printf("field type: %u ", field_type);
    switch (field_type) {
      case 0:
        // printf("NULL\r\n");
        break;
      case 1:
        value = (int8_t)page_buffer[data_offset++];
        // printf("byte %d\r\n", value);
        break;
      case 2:
        value = (int8_t)page_buffer[data_offset] << 8
                      | (int8_t)page_buffer[data_offset + 1];
        data_offset += 2;
        printf ("short %d\r\n", value);
        break;
      default:
        //printf("\r\n");
        break;
    }
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

sqliteReader::~sqliteReader() {
  free(page_buffer);
  free(filename);
  free(cell_offset);
}

int main(void) {
  sqliteReader reader = sqliteReader("fcc.sqlite");
}