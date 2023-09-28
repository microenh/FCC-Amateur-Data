import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
from random import choice
import sqlite3

BG_COLOR = "#3d6466"
DARK_BG_COLOR ="#28393A"
DB_NAME = "fcc.sqlite"

# CREATE TABLE lookup (
#   callsign            char(10)     not null primary key,
#   radio_service_code  char(2)      null, 
#   grant_date          char(10)     null,
#   expired_date        char(10)     null,
#   cancellation_date   char(10)     null,
#   operator_class      char(1)      null, 
#   previous_callsign   char(10)     null,
#   trustee_callsign    char(10)     null,
#   trustee_name        varchar(50)  null,
#   applicant_type_code char(1)      null, 
#   entity_name         varchar(200) null,
#   first_name          varchar(20)  null,
#   mi                  char(1)      null,
#   last_name           varchar(20)  null,
#   suffix              char(3)      null,
#   street_address      varchar(60)  null,
#   city                varchar(20)  null,
#   state               char(2)      null,
#   zip_code            char(9)      null,
#   po_box              varchar(20)  null,
#   attention_line      varchar(35)  null,
#   frn                 char(10)     null
# );

# CREATE TABLE db_date (date text);

# ('N8ME', 'HV', '03/04/2017', '05/20/2027', '', 'E', 'NQ8P', '', '', 'I', 'ERBAUGH, MARK E', 'MARK', 'E', 'ERBAUGH', '', '3105 BIG PLAIN-CIRCLEVILLE RD.', 'LONDON', 'OH', '43140', ' ', '', '0005334438')
# ('KE8RV', 'HV', '01/28/2020', '02/22/2030', '', '', 'KC8NQQ', 'W8DPK', 'KOVALCHIK, DONALD P', 'B', 'Madison County Amateur Radio Club', '', '', '', '', '4665 Lilly Chapel Opossum Rd', 'London', 'OH', '431408875', '', 'DONALD P KOVALCHIK', '0003799624')
# ('W8BI', 'HA', '02/08/2017', '03/06/2027', '', '', '', 'KB8UEY', 'LUNSFORD, ROBERT D', 'B', 'DAYTON AMATEUR RADIO ASSOCIATION', '', '', '', '', '', 'Dayton', 'OH', '45401', '44', ' ROBERT D LUNSFORD', '0003021573')

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
        self.image = ImageTk.PhotoImage(Image.open("FCC_Seal_1934_125.png"))

        menu_font = font.Font(family='TkMenuFont', size=14)
        heading_font = font.Font(family='TkHeadingFont', size=20)

        style = ttk.Style()
        style.theme_use('default')
        style.configure('item.TLabel', foreground='white', background=BG_COLOR, font=menu_font)
        style.configure('ingredient.TLabel', foreground='white', background=DARK_BG_COLOR, font=menu_font)
        style.configure('heading.TLabel', foreground='yellow', background=BG_COLOR, font=heading_font)
        style.configure('big.TButton', font=heading_font) 

        style.configure('new.TEntry', foreground='black', background='white', insertcolor='black', insertwidth='1')

        style.map('big.TButton', 
            foreground = [('pressed', 'red'), ('active', 'black'), ('!pressed', 'white')],
            background = [('pressed', 'white'),  ('active', '#badee2'), ('!pressed', DARK_BG_COLOR)])

        self.frame1 = tk.Frame(self, width=400, height=500, bg=BG_COLOR)
        self.frame1.grid(row=0, column=0, sticky='nsew')

        self.load_frame1()



    def load_frame1(self):
        def get_db_date():
            connection = sqlite3.connect(DB_NAME)
            cursor = connection.cursor()
            cursor.execute("select date from db_date;")
            db_date = cursor.fetchone()[0]
            connection.close()
            return db_date
        
        self.frame1.pack_propagate(False)
        self.call = tk.StringVar()
        self.displayCall = tk.StringVar()
        self.lookupResult = tk.StringVar()

        # frame1 widgets
        tk.Label(self.frame1, image=self.image, bg=BG_COLOR).pack(pady=20)
        ttk.Label(self.frame1, style='item.TLabel', text=f'Data from {get_db_date()}').pack()
        frame3 = tk.Frame(self.frame1, bg=BG_COLOR)
        frame3.pack()
        ttk.Label(frame3, style='item.TLabel', text='Enter callsign: ').pack(side='left')
        entry = ttk.Entry(frame3, style='new.TEntry', textvariable=self.call)
        entry.bind('<Return>', lambda event: self.lookup())
        entry.pack(side='left', pady=20)
        entry.focus_set()

        # ttk.Button(self.frame1, style='big.TButton', text="LOOKUP",
        #     cursor='hand2', command=self.lookup).pack()
        
        ttk.Label(self.frame1, style='heading.TLabel', textvariable=self.displayCall).pack()
        ttk.Label(self.frame1, style='item.TLabel', textvariable=self.lookupResult).pack(pady=(10,0))

    def lookup(self):
        connection = sqlite3.connect(DB_NAME)
        cursor = connection.cursor()
        call = self.call.get().upper()
        cursor.execute("select * from lookup where callsign='%s'" % call)
        lookup = cursor.fetchone()
        connection.close()
        self.displayCall.set(call)
        self.call.set('')
        # print (lookup)
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