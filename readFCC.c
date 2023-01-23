#include <stdio.h>
#include <sys/stat.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include "sqlite3.h"

struct fcc_rec {
  char callsign[10];
  char radio_service_code[2];
  char grant_date[10];
  char expired_date[10];
  char cancellation_date[10];
  char operator_class;
  char previous_callsign[10];
  char trustee_callsign[10];
  char trustee_name[50];
  char applicant_type_code;
  char entity_name[200];
  char first_name[20];
  char mi;
  char last_name[20];
  char suffix[3];
  char street_address[60];
  char city[20];
  char state[2];
  char zip_code[9];
  char po_box[20];
  char attention_line[35];
  char frn[10];
};

struct index_hdr {
  uint16_t keySize;
  uint16_t nodeSize;
  uint32_t root;
};

unsigned const node_count = 171;

struct index_rec {
  char key[node_count * 2 - 1][10];
  uint32_t record[node_count * 2 - 1];
  uint16_t child[node_count * 2];
  bool leaf;
  uint16_t active;
};

const unsigned rec_size = sizeof(struct fcc_rec);

struct fcc_rec fcc;

const char *fileName = "FCCser.dat";

long get_file_size(const char *filename) {
    struct stat file_status;
    if (stat(filename, &file_status) < 0) {
        return -1;
    }

    return file_status.st_size;
}

void lookup(const char *target) {
  long records = get_file_size(fileName) / rec_size;
  // printf("records: %lu\r\n", records);
  FILE *f = fopen(fileName, "rb");
  int c;
  long low = 0;
  long high = records;
  long mid;
  fread(&fcc, rec_size, 1, f);
  c = strcmp(target, fcc.callsign);
  if (c > 0) {
    while (high - low > 1) {
      mid = (low + high) / 2;
      // printf("%s %s %ld %ld %ld\r\n", fcc.callsign, target, low, mid, high);
      fseek(f, mid * rec_size, SEEK_SET);
      fread(&fcc, rec_size, 1, f);
      c = strcmp(target, fcc.callsign);
      if (!c) {
        break;
      } else if (c > 0) {
        low = mid;
      } else {
        high = mid;
      }
    }
  }
  fclose(f);
  if (strcmp(fcc.callsign, target)) {
    printf("%s - Not found.\r\n", target);
  } else {
    printf("%s %s %s\r\n", fcc.callsign, fcc.first_name, fcc.last_name);
  }
}

const char *calls[] = {
  "_",
  "AA0A",
  "AA0AA",
  "AA0AB",
  "N8ME",
  "N8ME-",
  "W8NX",
  "WA8KKN",
  "W8CR",
  "N8CWU",
  "WZ9Y",
  "WZ9Z",
  "WZ9ZZZ",
  "Z",
};

int mainFlat(void) {

  for (int i = 0; i<sizeof(calls) / sizeof(calls[0]); i++) {
    lookup(calls[i]);
  }
  return 0;
}

const char *dbName = "fcc.sqlite";
const char *indexName = "FCC_Calls.ndx";
const char *dataName = "FCC_Calls.db";
const char *query = "select callsign, last_name, first_name from lookup where callsign = ?";





int mainSQL(void) {
  sqlite3 *pDb;
  sqlite3_stmt *stmt;

  int rc;
  rc = sqlite3_open_v2(dbName, &pDb, SQLITE_OPEN_READONLY, NULL);
  if (!rc) {
    rc = sqlite3_prepare_v2(pDb, query, -1, &stmt, NULL);
    for (int i = 0; i<sizeof(calls) / sizeof(calls[0]); i++) {
      sqlite3_reset(stmt);
      rc = sqlite3_bind_text(stmt, 1, calls[i], -1, NULL);
      while (sqlite3_step(stmt) != SQLITE_DONE) {
        int i;
        int num_cols = sqlite3_column_count(stmt);
        
        for (i = 0; i < num_cols; i++)
        {
          switch (sqlite3_column_type(stmt, i))
          {
          case (SQLITE3_TEXT):
            printf("%s, ", sqlite3_column_text(stmt, i));
            break;
          case (SQLITE_INTEGER):
            printf("%d, ", sqlite3_column_int(stmt, i));
            break;
          case (SQLITE_FLOAT):
            printf("%g, ", sqlite3_column_double(stmt, i));
            break;
          default:
            break;
          }
        }
        printf("\n");
      }
    }
  }


  sqlite3_close_v2(pDb);
  return 0;
}

int binSearch(FILE *f, int nodeIdx, const char* targetCall) {
  struct index_rec rec;

  fseek(f, sizeof(struct index_hdr) + sizeof(struct index_rec) * nodeIdx, SEEK_SET);
  fread(&rec, sizeof(struct index_rec), 1, f);

  uint16_t high = rec.active;
  uint16_t low = 0;
  uint16_t mid = (high + low) / 2;
  // printf("\r\n");
  while (low < high) {
    // printf("%d ", mid);
    int c = strcmp(targetCall, rec.key[mid]);
    if (!c) {
      break;
    } else if (c > 0) {
      low = mid + 1;
    } else {
      high = mid;
    }
    mid = (high + low) / 2;
  }
  if (mid == rec.active) {
    if (rec.leaf) {
      return (-1);
    } else {
      return (binSearch (f, rec.child[rec.active], targetCall));
    }
  } else if (strcmp(targetCall, rec.key[mid])) {
    if (rec.leaf) {
      return (-1);
    } else {
      return (binSearch (f, rec.child[mid], targetCall));
    } 
  }
  return rec.record[mid];
}


void lookupBTree(const char *targetCall) {
  struct index_hdr hdr;
  struct fcc_rec fcc;

  FILE *f = fopen(indexName, "rb");
  fread(&hdr, sizeof(struct index_hdr), 1, f);
  int r = binSearch(f, hdr.root, targetCall);
  fclose(f);
  if (r > -1) {
    f = fopen(dataName, "rb");
    fseek(f, r * sizeof(struct fcc_rec), SEEK_SET);
    fread(&fcc, sizeof(fcc), 1, f);
    printf("%s %s\r\n", fcc.callsign, fcc.entity_name);
  } else {
    printf("Not found.\r\n");
  }
}

void mainBTree(void) {
  struct index_hdr hdr;
  struct index_rec rec;
  FILE *f = fopen(indexName, "rb");
  fread(&hdr, sizeof(hdr), 1, f);
  fseek(f, sizeof(struct index_rec) * hdr.root, SEEK_CUR);
  fread(&rec, sizeof(rec), 1, f);
  fclose(f);

  for(int i=0; i < rec.active; i++) {
    char test[10];
    strcpy(test, rec.key[i]);
    // test[strlen(test) - 1];
    lookupBTree(test);
  }

}

void mainBTreeAll() {
  sqlite3 *pDb;
  sqlite3_stmt *stmt;

  struct index_hdr hdr;
  struct fcc_rec fcc;

  FILE *f = fopen(indexName, "rb");
  fread(&hdr, sizeof(struct index_hdr), 1, f);

  int found = 0;
  int not_found = 0;
  int records = 0;
  int rc = sqlite3_open_v2(dbName, &pDb, SQLITE_OPEN_READONLY, NULL);
  if (!rc) {
    rc = sqlite3_prepare_v2(pDb, "select callsign from lookup", -1, &stmt, NULL);
    while (sqlite3_step(stmt) != SQLITE_DONE) {
      records++;
      if (records % 100000 == 0) {
        printf("%s (%d)\r\n", (const char *) sqlite3_column_text(stmt, 0), records);
      }
      int r = binSearch(f, hdr.root, (const char *) sqlite3_column_text(stmt, 0));
      if (r == -1) {
        not_found++;
      } else {
        found++;
      }
    }
  }
  sqlite3_close_v2(pDb);
  fclose(f);

  printf("\r\nFound: %d, Not Found: %d\r\n", found, not_found);
}



int main(void) {
  // return mainFlat();
  // return mainSQL();
  // mainBTree();
  mainBTreeAll();
}