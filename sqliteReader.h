#pragma once

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

    void parse_page(void);
    void parse_payload(uint16_t offset, uint16_t max=0xffff);
    void parse_record(uint16_t offset, uint16_t max=0xffff);

    uint32_t varint(uint16_t &ofs);


  public:
    sqliteReader(const char *);
    ~sqliteReader();
};