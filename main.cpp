#include "sqliteReader.h"
#include <stdio.h>
#include <string.h>
#include <stdint.h>

const char *fmt = 
  "call:      %s\r\n"
  "call code: %s\r\n"
  "grant:     %s\r\n"
  "expired:   %s\r\n"
  "cancelled: %s\r\n"
  "class:     %s\r\n"
  "previous:  %s\r\n"
  "t call:    %s\r\n"
  "t name:    %s\r\n"
  "app code:  %s\r\n"
  "ent name:  %s\r\n"
  "first:     %s\r\n"
  "mi:        %s\r\n"
  "last:      %s\r\n"
  "suffix:    %s\r\n"
  "street:    %s\r\n"
  "city:      %s\r\n"
  "state:     %s\r\n"
  "ZIP:       %s\r\n"
  "po box     %s\r\n"
  "attn:      %s\r\n"
  "frn:       %s\r\n";


int main(void) {
  sqliteReader reader = sqliteReader("fcc.sqlite");
  char buff[80];
  char *input = buff;
  size_t input_size = sizeof(input);
  while (true) {
    printf("Enter call => ");
     if (getline(&input, &input_size, stdin) == 1) {
       break;
     } else {
      input[strlen(input) - 1] = 0;
      if (reader.lookup_call(input)) {
        printf (fmt, reader.lookup.callsign,
                    reader.lookup.radio_service_code,
                    reader.lookup.grant_date,
                    reader.lookup.expired_date,
                    reader.lookup.cancellation_date,
                    reader.lookup.operator_class,
                    reader.lookup.previous_callsign,
                    reader.lookup.trustee_callsign,
                    reader.lookup.trustee_name,
                    reader.lookup.applicant_type_code,
                    reader.lookup.entity_name,
                    reader.lookup.first_name,
                    reader.lookup.mi,
                    reader.lookup.last_name,
                    reader.lookup.suffix,
                    reader.lookup.street_address,
                    reader.lookup.city,
                    reader.lookup.state,
                    reader.lookup.zip_code,
                    reader.lookup.po_box,
                    reader.lookup.attention_line,
                    reader.lookup.frn);
      } else {
        printf("Not found\r\n");
      }
    }
  }
}