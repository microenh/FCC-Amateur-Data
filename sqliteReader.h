#pragma once

#include <stdint.h>
#include <stdio.h>

union DB {
  int64_t i;
  double f;
  uint8_t *ptr;
};

struct SCHEMA {
  char type[11];
  char name[21];
  char tbl_name[21];
  uint32_t rootpage;
};

struct LOOKUP {
  char callsign[11];
  char radio_service_code[3];
  char grant_date[11];
  char expired_date[11];
  char cancellation_date[11];
  char operator_class[2];
  char previous_callsign[11];
  char trustee_callsign[11];
  char trustee_name[51];
  char applicant_type_code[2];
  char entity_name[201];
  char first_name[21];
  char mi[2];
  char last_name[21];
  char suffix[4];
  char street_address[61];
  char city[21];
  char state[3];
  char zip_code[10];
  char po_box[21];
  char attention_line[36];
  char frn[11];
};

class sqliteReader {
  private:
    char *filename;
    uint16_t page_size;
    uint8_t *page_buffer;
    uint16_t U;
    uint16_t M;
    uint16_t X;
    uint8_t type;
    uint16_t max_number_cells;
    uint16_t number_cells;
    uint32_t right_child;
    uint32_t left_child;
    uint16_t *cell_offset;
    uint32_t row_id;
    uint32_t overflow;
    SCHEMA *schema;
    void *data_dest;

    void parse_page(void);
    void parse_payload(uint16_t offset, uint16_t max=0xffff);
    void parse_record(uint16_t offset, uint16_t max=0xffff);
    void (sqliteReader::*store)(uint16_t field_no, uint32_t field_type, DB data);
    void store_header(uint16_t field_no, uint32_t field_type, DB data);
    void store_data(uint16_t field_no, uint32_t field_type, DB data);
    void save_string(uint16_t field_len, uint16_t target_len, char *dest, char *src);
    void read_page(FILE *f, uint32_t page);
  
    uint32_t varint(uint16_t &ofs);


  public:
    sqliteReader(const char *);
    ~sqliteReader();
    bool lookup_call(const char *);
    LOOKUP lookup;
};