cmake_minimum_required(VERSION 3.12)

add_executable(readFCC
    readFCC.c
    sqlite3.c
)

add_executable(sqliteReader
    sqliteReader.cpp
)