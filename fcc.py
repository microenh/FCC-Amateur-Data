import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
from random import choice
import sqlite3
import os
import requests, zipfile
from io import BytesIO

from db_setup_strings import *

BG_COLOR = "#3d6466"
DARK_BG_COLOR ="#28393A"
DB = os.path.join(os.path.dirname(__file__), "./fcc.sqlite")
LOGO = os.path.join(os.path.dirname(__file__), "./FCC_Seal_1934_125.png")

VACUUM = f"vacuum into '{DB}';"

op_class = {'A': 'Advanced',
            'E': 'Amateur Extra',
            'G': 'General',
            'N': 'Novice',
            'T': 'Technician'}

class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("FCC Amateur Radio Callgign Lookup")
        self.after_idle(lambda: self.eval("tk::PlaceWindow . center center"))
        self.image = ImageTk.PhotoImage(Image.open(LOGO))
        self.preferences = None
        self.help = None
        self.call = tk.StringVar()
        self.displayCall = tk.StringVar()
        self.lookupResult = tk.StringVar()
        self.dbDate = tk.StringVar()
        self.updateStatus = tk.StringVar()

        menu_font = font.Font(family='TkMenuFont', size=14)
        heading_font = font.Font(family='TkHeadingFont', size=20)

        style = ttk.Style()
        style.theme_use('default')
        # print (self.tk.call('tk', 'windowingsystem')) # aqua on macos
        style.configure('item.TLabel', foreground='white', background=BG_COLOR, font=menu_font)
        style.configure('ingredient.TLabel', foreground='white', background=DARK_BG_COLOR, font=menu_font)
        style.configure('heading.TLabel', foreground='yellow', background=BG_COLOR, font=heading_font)
        style.configure('big.TButton', font=heading_font) 

        style.configure('new.TEntry', foreground='black', background='white', insertcolor='black', insertwidth='1')

        style.map('big.TButton', 
            foreground = [('pressed', 'red'), ('active', 'black'), ('!pressed', 'white')],
            background = [('pressed', 'white'),  ('active', '#badee2'), ('!pressed', DARK_BG_COLOR)])

        frame = tk.Frame(self, width=400, height=500, bg=BG_COLOR)
        frame.grid(row=0, column=0, sticky='nsew')
        frame.pack_propagate(False)

        # frame widgets
        tk.Label(frame, image=self.image, bg=BG_COLOR).pack(pady=20)
        self.get_db_date()
        ttk.Label(frame, style='item.TLabel', textvariable=self.dbDate).pack()
        frame2 = tk.Frame(frame, bg=BG_COLOR)
        frame2.pack()
        ttk.Label(frame2, style='item.TLabel', text='Enter callsign: ').pack(side='left')
        entry = ttk.Entry(frame2, style='new.TEntry', textvariable=self.call)
        entry.bind('<Return>', lambda event: self.lookupCall())
        entry.pack(side='left', pady=20)
        entry.focus_set()
        
        ttk.Label(frame, style='heading.TLabel', textvariable=self.displayCall).pack()
        ttk.Label(frame, style='item.TLabel', textvariable=self.lookupResult).pack(pady=(10,0))

        self.createcommand('tk::mac::ShowPreferences', self.showPreferencesDialog)
        self.createcommand('tk::mac::ShowHelp', self.showHelpDialog)

    def updateFromFCC(self):
        """Populate fcc.sqlite database with data downloaded from FCC."""
        def update_status_display(text):
            self.updateStatus.set(text)
            self.update()

        def insert_data(file_name, table_name):
            data = [i.split('|') for i in str(zf.read(file_name), encoding='UTF-8').replace('"', '').split('\r\n')[:-1]]
            stmt = f"insert into {table_name} values ({','.join(['?'] * len(data[0]))});"
            update_status_display(f'Importing {table_name}')
            con.executemany(stmt, data)
            con.commit()

        update_status_display('Downloading')

        zf = zipfile.ZipFile(BytesIO(requests.get(FCC_URL).content))

        update_status_display('Create database schema')
        
        con = sqlite3.connect(":memory:")
        for i in (CREATE_AM, CREATE_EN, CREATE_HD, CREATE_COUNTS, CREATE_LOOKUP, CREATE_DB_DATE):
            con.execute(i)
        con.commit()

        for i in (('AM.dat', 'AM'), ('EN.dat', 'EN'), ('HD.dat', 'HD'), ('counts', 'counts')):
            insert_data(*i)

        update_status_display('Building database')
 
        for i in (INSERT_DB_DATE, INSERT_LOOKUP, INDEX_LOOKUP):
            con.execute(i)
            con.commit()

        update_status_display('Saving databse')

        try:
            os.remove(DB)
        except FileNotFoundError:
            pass
        
        con.execute(VACUUM) # saves :memory: database to file
        con.close()

        self.get_db_date()
        update_status_display('Done')
        self.after(3000, lambda: update_status_display(''))

    def close_dialog(self, window):
        self.__dict__[window] = None

    def showPreferencesDialog(self):
        if self.preferences is None:
            self.preferences = tk.Toplevel()
            frame = tk.Frame(self.preferences, width=300, height=400, bg=BG_COLOR)
            frame.grid(row=0, column=0, sticky='nsew')
            self.preferences.bind('<Destroy>',  lambda event: self.close_dialog('preferences'))
            self.preferences.title("Settings")

            ttk.Button(frame, style='big.TButton', text="UPDATE FROM FCC", command=self.updateFromFCC).pack(padx=10, pady=10)
            ttk.Label(frame, style='item.TLabel', textvariable=self.updateStatus).pack(padx=10, pady=(0,10))

            self.preferences.grab_set()

    def showHelpDialog(self):
        if self.help is None:
            self.help = tk.Toplevel()
            self.help.bind('<Destroy>', lambda event: self.close_dialog('help'))
            self.help.title("Help")
            self.help.grab_set()

    def get_db_data(self, query):
        con = sqlite3.connect(DB)
        cursor = con.cursor()
        try:
            cursor.execute(query)
            result = cursor.fetchone()
        except sqlite3.OperationalError:
            result = None
        con.close()
        return result

    def get_db_date(self):
        result = self.get_db_data("select date from db_date;")
        self.dbDate.set('<< Nothing downloaded >>' if result is None else f'Data from {result[0]}')
        
    def lookupCall(self):
        call = self.call.get().upper()
        self.displayCall.set(call)
        self.call.set('')
        lookup = self.get_db_data(f"select * from lookup where callsign='{call}'")
        if lookup is None:
            self.lookupResult.set('Not found')
        else:
            name = ' '.join([i for i in lookup[11:15] if i > ''])
            op = 'Class: ' + op_class.get(lookup[5], 'Unknown') if lookup[9] == 'I' else ''
            vanity = 'Vanity' if lookup[1] == 'HV' else ''
            expires = 'Expires: ' + lookup[3] if lookup[3] > '' else ''
            if name == '':
                name = lookup[10]
            csz = f'{lookup[16]}, {lookup[17]}  {lookup[18]}'
            po = f'PO BOX {lookup[19]}' if (lookup[19] > ' ') else ''
            self.lookupResult.set('\r'.join([i for i in (name, po, lookup[15], csz, ' ', vanity, op, expires) if i > '']))
        

# create and run
if __name__ == '__main__':
    App().mainloop()