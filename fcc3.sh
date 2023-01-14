#!/bin/sh

#  fcc3.sh
#  FCC Database
#
#  Created by Mark Erbaugh on 11/5/21.
#  
#! /bin/bash

# Mark Erbaugh 11/5/2021
# this script converts the FCC amateur database download (l_amat.zip)
# to a sqlite3 database, fcc2.sqlite
# to run: place l_amat.zip in the same directory
# compared to fcc.sh, this version creates lookup as a table rather than a view
#  and deletes all the other tables
# comared to fcc2.sh, the lookup table only includes active records

rm fcc3.sqlite
rm -r l_amat
rm temp.sql

unzip l_amat -d l_amat
sed -i '' 's/"//g' l_amat/AM.dat l_amat/EN.dat l_amat/HD.dat

cat << EOF > temp.sql
create table AM
(
      record_type                char(2)              not null,
      unique_system_identifier   numeric(9,0)         not null primary key,
      uls_file_num               char(14)             null,
      ebf_number                 varchar(30)          null,
      callsign                   char(10)             null,
      operator_class             char(1)              null,
      group_code                 char(1)              null,
      region_code                tinyint              null,
      trustee_callsign           char(10)             null,
      trustee_indicator          char(1)              null,
      physician_certification    char(1)              null,
      ve_signature               char(1)              null,
      systematic_callsign_change char(1)              null,
      vanity_callsign_change     char(1)              null,
      vanity_relationship        char(12)             null,
      previous_callsign          char(10)             null,
      previous_operator_class    char(1)              null,
      trustee_name               varchar(50)          null
)
go

create table EN
(
      record_type               char(2)              not null,
      unique_system_identifier  numeric(9,0)         not null primary key,
      uls_file_number           char(14)             null,
      ebf_number                varchar(30)          null,
      callsign                  char(10)             null,
      entity_type               char(2)              null,
      licensee_id               char(9)              null,
      entity_name               varchar(200)         null,
      first_name                varchar(20)          null,
      mi                        char(1)              null,
      last_name                 varchar(20)          null,
      suffix                    char(3)              null,
      phone                     char(10)             null,
      fax                       char(10)             null,
      email                     varchar(50)          null,
      street_address            varchar(60)          null,
      city                      varchar(20)          null,
      state                     char(2)              null,
      zip_code                  char(9)              null,
      po_box                    varchar(20)          null,
      attention_line            varchar(35)          null,
      sgin                      char(3)              null,
      frn                       char(10)             null,
      applicant_type_code       char(1)              null,
      applicant_type_other      char(40)             null,
      status_code               char(1)              null,
      status_date               datetime             null,
      lic_category_code         char(1)              null,
      linked_license_id         numeric(9,0)         null,
      linked_callsign           char(10)             null
)
go

create table HD
(
      record_type                  char(2)              not null,
      unique_system_identifier     numeric(9,0)         not null primary key,
      uls_file_number              char(14)             null,
      ebf_number                   varchar(30)          null,
      callsign                     char(10)             null,
      license_status               char(1)              null,
      radio_service_code           char(2)              null,
      grant_date                   char(10)             null,
      expired_date                 char(10)             null,
      cancellation_date            char(10)             null,
      eligibility_rule_num         char(10)             null,
      applicant_type_code_reserved char(1)              null,
      alien                        char(1)              null,
      alien_government             char(1)              null,
      alien_corporation            char(1)              null,
      alien_officer                char(1)              null,
      alien_control                char(1)              null,
      revoked                      char(1)              null,
      convicted                    char(1)              null,
      adjudged                     char(1)              null,
      involved_reserved            char(1)              null,
      common_carrier               char(1)              null,
      non_common_carrier           char(1)              null,
      private_comm                 char(1)              null,
      fixed                        char(1)              null,
      mobile                       char(1)              null,
      radiolocation                char(1)              null,
      satellite                    char(1)              null,
      developmental_or_sta         char(1)              null,
      interconnected_service       char(1)              null,
      certifier_first_name         varchar(20)          null,
      certifier_mi                 char(1)              null,
      certifier_last_name          varchar(20)          null,
      certifier_suffix             char(3)              null,
      certifier_title              char(40)             null,
      gender                       char(1)              null,
      african_american             char(1)              null,
      native_american              char(1)              null,
      hawaiian                     char(1)              null,
      asian                        char(1)              null,
      white                        char(1)              null,
      ethnicity                    char(1)              null,
      effective_date               char(10)             null,
      last_action_date             char(10)             null,
      auction_id                   int                  null,
      reg_stat_broad_serv          char(1)              null,
      band_manager                 char(1)              null,
      type_serv_broad_serv         char(1)              null,
      alien_ruling                 char(1)              null,
      licensee_name_change         char(1)              null,
      whitespace_ind               char(1)              null,
      additional_cert_choice       char(1)              null,
      additional_cert_answer       char(1)              null,
      discontinuation_ind          char(1)              null,
      regulatory_compliance_ind    char(1)              null,
      eligibility_cert_900         char(1)              null,
      transition_plan_cert_900     char(1)              null,
      return_spectrum_cert_900     char(1)              null,
      payment_cert_900             char(1)              null
)
go

create table lookup (
  radio_service_code  char(2)      null, -- HA - amateur, HV - vanity
  grant_date          char(10)     null,
  expired_date        char(10)     null,
  cancellation_date   char(10)     null,
  callsign            char(10)     null,
  operator_class      char(1)      null, -- A - Advanced, E - Amateur Extra, G - General, N - Novice, P - Technician Plus, T - Technician
  previous_callsign   char(10)     null,
  trustee_callsign    char(10)     null,
  trustee_name        varchar(50)  null,
  applicant_type_code char(1)      null, -- B - Amateur Club, G - Governement Enttiy, I - Individual, M - Military Recreaction. R - Races
                                         -- C - Corporation, D - General Partnership, E - Limited Partnership, F - Limited Liability Partnership,
                                         -- H - Other, J - Joint Venture, L - Limited Liability Company, O - Consortium, P - Partnership,
                                         -- T - Trust, U - Unincorporated Association
  entity_name         varchar(200) null,
  first_name          varchar(20)  null,
  mi                  char(1)      null,
  last_name           varchar(20)  null,
  suffix              char(3)      null,
  street_address      varchar(60)  null,
  city                varchar(20)  null,
  state               char(2)      null,
  zip_code            char(9)      null,
  po_box              varchar(20)  null,
  attention_line      varchar(35)  null,
  frn                 char(10)     null
)
go

.import l_amat/HD.dat HD
.import l_amat/AM.dat AM
.import l_amat/EN.dat EN

insert into lookup
select
  HD.radio_service_code,
  HD.grant_date,
  HD.expired_date,
  HD.cancellation_date,
  AM.callsign,
  AM.operator_class,
  AM.previous_callsign,
  AM.trustee_callsign,
  AM.trustee_name,
  EN.applicant_type_code,
  EN.entity_name,
  EN.first_name,
  EN.mi,
  EN.last_name,
  EN.suffix,
  EN.street_address,
  EN.city,
  EN.state,
  EN.zip_code,
  EN.po_box,
  EN.attention_line,
  EN.frn
from HD
  inner join EN on HD.unique_system_identifier = EN.unique_system_identifier
  inner join AM on HD.unique_system_identifier = AM.unique_system_identifier
where HD.license_status = "A"
go

create index callsign on lookup(callsign);
go

drop table EN;
drop table AM;
drop table HD;

create table counts (line text)
go

.import l_amat/counts counts

create table db_date (date text)
go

insert into db_date select substr(line, 21, 99) from counts limit 1;

drop table counts;

VACUUM;

EOF

sqlite3 -init temp.sql fcc3.sqlite ".quit"
rm -r l_amat
rm temp.sql
