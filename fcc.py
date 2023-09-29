import tkinter as tk
from tkinter import ttk, font
from PIL import Image, ImageTk
from random import choice
import sqlite3
import os

import requests, zipfile
from io import BytesIO

BG_COLOR = "#3d6466"
DARK_BG_COLOR ="#28393A"
DB = os.path.join(os.path.dirname(__file__), "./fcc.sqlite")
LOGO = os.path.join(os.path.dirname(__file__), "./FCC_Seal_1934_125.png")

CREATE_AM = """
create temp table AM
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
);
"""

INSERT_AM = """
    insert into AM VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
"""

CREATE_EN = """
create temp table EN
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
);
"""

INSERT_EN = """
    insert into EN values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);
"""

CREATE_HD = """
create temp table HD
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
);
"""

INSERT_HD = """
    insert into HD values (
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,
        ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
    );
"""

CREATE_LOOKUP = """
create table lookup (
    callsign            char(10)     not null primary key,
    radio_service_code  char(2)      null, 
    grant_date          char(10)     null,
    expired_date        char(10)     null,
    cancellation_date   char(10)     null,
    operator_class      char(1)      null, 
    previous_callsign   char(10)     null,
    trustee_callsign    char(10)     null,
    trustee_name        varchar(50)  null,
    applicant_type_code char(1)      null, 
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
);
"""

CREATE_COUNTS = """
    create temp table counts (line text);
"""

INSERT_COUNTS = """
    insert into counts values (?);
"""

CREATE_DB_DATE = """
create table db_date(
    date text
);
"""

INSERT_DB_DATE = """
    insert into db_date select substr(line, 21, 99) from counts limit 1;
"""

INSERT_LOOKUP = """
insert into lookup
select
    AM.callsign,
    HD.radio_service_code,
    HD.grant_date,
    HD.expired_date,
    HD.cancellation_date,
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
where HD.license_status = "A";
"""

INDEX_LOOKUP = 'create index callsign on lookup(callsign);'

VACUUM = f"vacuum into '{DB}';"

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

        self.frame1 = tk.Frame(self, width=400, height=500, bg=BG_COLOR)
        self.frame1.grid(row=0, column=0, sticky='nsew')

        self.load_frame1()

        # menubar = tk.Menu(self)
        # menubar.delete(0)
        # self.config(menu=menubar)
        # file_menu = tk.Menu(menubar)
        # file_menu.add_command(label='Exit', command=self.destroy)
        # menubar.add_cascade(label="File", menu=file_menu)

        # menubar = tk.Menu(self)
        # appmenu = tk.Menu(menubar, name='apple')
        # menubar.add_cascade(menu=appmenu)
        # appmenu.add_command(label='Settings...')
        # appmenu.add_separator()
        # self['menu'] = menubar       

        self.createcommand('tk::mac::ShowPreferences', self.showMyPreferencesDialog)
        self.createcommand('tk::mac::ShowHelp', self.showMyHelpDialog)

    def closePreferences(self, window):
        self.preferences = None

    def updateFromFCC(self):

        def parse(table_name):
            return [i.split('|') for i in str(zf.read(table_name), encoding='UTF-8').replace('"', '').split('\r\n')[:-1]]


        #Defining the zip file URL
        url = 'https://data.fcc.gov/download/pub/uls/complete/l_amat.zip'
        # url = 'https://data.fcc.gov/download/pub/uls/complete/a_um.zip'

        # Downloading the file by sending the request to the URL
        self.updateStatus.set('Downloading')
        self.preferences.update()
        zf = zipfile.ZipFile(BytesIO(requests.get(url).content))

        self.updateStatus.set('Extracting')
        self.preferences.update()
        
        con = sqlite3.connect(":memory:")
        con.execute(CREATE_AM)
        con.execute(CREATE_EN)
        con.execute(CREATE_HD)
        con.execute(CREATE_COUNTS)
        con.execute(CREATE_LOOKUP)
        con.execute(CREATE_DB_DATE)

        con.executemany(INSERT_COUNTS, parse('counts'))
        con.commit()
        con.executemany(INSERT_AM, parse('AM.dat'))
        con.commit()
        con.executemany(INSERT_EN, parse('EN.dat'))
        con.commit()
        con.executemany(INSERT_HD, parse('HD.dat'))
        con.commit()

        self.updateStatus.set('Building database')
        self.preferences.update()

        con.execute(INSERT_DB_DATE)
        con.commit()
        con.execute(INSERT_LOOKUP)
        con.execute(INDEX_LOOKUP)
        con.commit()

        self.updateStatus.set('Saving databse')
        self.preferences.update()

        try:
            os.remove(DB)
        except FileNotFoundError:
            pass
        
        con.execute(VACUUM)
        con.close
        self.updateStatus.set('')
        self.get_db_date()


    def showMyPreferencesDialog(self):
        if self.preferences is None:
            self.preferences = tk.Toplevel()
            self.frame2 = tk.Frame(self.preferences, width=300, height=400, bg=BG_COLOR)
            self.frame2.grid(row=0, column=0, sticky='nsew')
            self.preferences.bind('<Destroy>', self.closePreferences)
            self.preferences.title("Settings")

            ttk.Button(self.frame2, style='big.TButton', text="UPDATE FROM FCC", command=self.updateFromFCC).pack(padx=10, pady=10)
            ttk.Label(self.frame2, style='item.TLabel', textvariable=self.updateStatus).pack(padx=10, pady=10)

            self.preferences.mainloop()


    def closeHelp(self, window):
        self.help = None

    def showMyHelpDialog(self):
        if self.help is None:
            self.help = tk.Toplevel()
            self.help.bind('<Destroy>', self.closeHelp)
            self.help.title("Help")
            self.help.mainloop()


    def get_db_date(self):
        connection = sqlite3.connect(DB)
        cursor = connection.cursor()
        try:
            cursor.execute("select date from db_date;")
            date = f'Data from {cursor.fetchone()[0]}'
        except sqlite3.OperationalError:
            date = '<< Nothing downloaded. >>'
        connection.close()
        self.dbDate.set(date)
        
    def load_frame1(self):
        self.frame1.pack_propagate(False)

        # frame1 widgets
        tk.Label(self.frame1, image=self.image, bg=BG_COLOR).pack(pady=20)
        self.get_db_date()
        ttk.Label(self.frame1, style='item.TLabel', textvariable=self.dbDate).pack()
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
        connection = sqlite3.connect(DB)
        cursor = connection.cursor()
        call = self.call.get().upper()
        try:
            cursor.execute("select * from lookup where callsign='%s'" % call)
            lookup = cursor.fetchone()
        except sqlite3.OperationalError:
            lookup = None
        connection.close()
        self.displayCall.set(call)
        self.call.set('')
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