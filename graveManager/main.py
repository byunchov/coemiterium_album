from PyQt5.QtWidgets import QApplication, QMainWindow, QDialog, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtCore import QDate
from PyQt5 import uic
from qt_material import QtStyleTools
import sys
import socket

EXIT_MSG = b'#!:exit:'
ERROR_MSG = b'!#error:'
HOST = ''
PORT = 50555


class SqlQueryError(Exception):
    """Exception raised for errors in the input query.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def get_data_from_db(query):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        records = []
        server.connect((HOST, PORT))
        server.sendall(bytes(query, 'utf-8'))
        while True:
            data = server.recv(1024)
            if EXIT_MSG == data:
                print(data)
                break
            elif ERROR_MSG in data:
                err = data.decode('utf-8').replace(str(ERROR_MSG, 'utf-8'), '')
                raise SqlQueryError(err)
            records.append(data.decode('utf-8'))
    return records


def insert_data_in_db(query):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        response = 0
        server.connect((HOST, PORT))
        server.sendall(bytes(query, 'utf-8'))
        while True:
            data = server.recv(1024)
            if EXIT_MSG == data:
                print(data)
                break
            elif ERROR_MSG in data:
                err = data.decode('utf-8').replace(str(ERROR_MSG, 'utf-8'), '')
                raise SqlQueryError(err)
            response = int(data.decode('utf-8'))
            print("Last written ID:", response)
    return response


########################################################################
class RuntimeStylesheets(QMainWindow, QtStyleTools):
    # ----------------------------------------------------------------------
    def __init__(self):
        """"""
        super().__init__()
        self.main = uic.loadUi('main_window.ui', self)
        # self.main = QUiLoader().load('main_window.ui', self)

        self.main.pushButton.clicked.connect(lambda: self.apply_stylesheet(self.main, 'dark_teal.xml'))
        self.main.pushButton_2.clicked.connect(
            lambda: self.apply_stylesheet(self.main, 'light_red.xml', extra={'font_family': 'mono', }))
        self.main.pushButton_3.clicked.connect(
            lambda: self.apply_stylesheet(self.main, 'light_blue.xml', extra={'font_family': 'Raleway', }))


class GravesiteDialog(QDialog, QtStyleTools):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = uic.loadUi('gs_occupation.ui', self)

        self.dialog.btn_cancel.clicked.connect(self.close)
        self.dialog.btn_save.clicked.connect(self.save_record)
        self.dialog.btn_find.clicked.connect(self.find_by_egn)
        self.load_zones()
        self.load_sectors()

    def load_zones(self):
        try:
            zone_query = 'SELECT zone FROM grave_sites GROUP by zone ORDER by zone ASC;'
            zones = get_data_from_db(zone_query)
            self.cb_zone.addItems(zones)

        except ConnectionRefusedError:
            self.lbl_status.setText("Неуспешна връзка със сървъра!")
        except SqlQueryError as e:
            self.lbl_status.setText(e.message)

    def load_sectors(self):
        try:
            sector_query = 'SELECT sector FROM grave_sites GROUP by sector ORDER by sector ASC;'
            sectors = get_data_from_db(sector_query)
            self.cb_sector.addItems(sectors)

        except ConnectionRefusedError:
            self.lbl_status.setText("Неуспешна връзка със сървъра!")
        except SqlQueryError as e:
            self.lbl_status.setText(e.message)

    def find_by_egn(self):
        egn = str(self.dialog.find_dead_egn.text())

        if egn == '':
            self.lbl_status.setText("Полето за търсене по ЕГН е празно!")
        else:
            try:
                query = f"SELECT id, first_name, last_name, egn, dob, dod FROM deceased_list WHERE egn like '{egn}';"
                data = get_data_from_db(query)
                if not data:
                    self.lbl_status.setText("Няма намерен резултат!")
                else:
                    self.lbl_status.setText(f"Открит е запис за починал с ЕГН '{egn}'.")
                    deceased = data[0].split('|')
                    print(deceased)
                    self.dialog.dead_id.setText(deceased[0])
                    self.dialog.dead_fname.setText(deceased[1])
                    self.dialog.dead_lname.setText(deceased[2])
                    self.dialog.dead_egn.setText(deceased[3])
                    dob = QDate.fromString(deceased[4], 'yyyy-MM-dd')
                    dod = QDate.fromString(deceased[5], 'yyyy-MM-dd')
                    self.dialog.dead_dob.setDate(dob)
                    self.dialog.dead_dod.setDate(dod)

            except ConnectionRefusedError:
                self.lbl_status.setText("Неуспешна връзка със сървъра!")
            except SqlQueryError as e:
                self.lbl_status.setText(e.message)

    def save_record(self):
        zone = self.dialog.cb_zone.currentText()
        sector = self.dialog.cb_sector.currentText()
        row = self.dialog.tb_row.text()
        col = self.dialog.tb_col.text()
        did = self.dialog.dead_id.text()

        errors = ''
        errors += "'Ред' е празно! " if row == '' else ''
        errors += "'Колона' е празно! " if col == '' else ''
        errors += "Не е избран починал! " if did == '' else ''

        if errors:
            self.lbl_status.setText(errors)
        else:
            self.lbl_status.setText("Записът е създаден успешно.")
            print(zone, sector, row, col, did)
        print("Save clicked!")


class AddDeceasedDialog(QDialog, QtStyleTools):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = uic.loadUi('deceased_dialog.ui', self)

        self.dialog.btn_cancel.clicked.connect(self.close)
        self.dialog.btn_save.clicked.connect(self.save_record)

    def save_record(self):
        fname = self.dialog.dead_fname.text()
        lname = self.dialog.dead_lname.text()
        egn = self.dialog.dead_egn.text()
        dob = self.dialog.dead_dob.date().toString('yyyy-MM-dd')
        dod = self.dialog.dead_dod.date().toString('yyyy-MM-dd')
        token = self.dialog.dead_token.text()

        errors = ''
        errors += "'Име' е празно! " if fname == '' else ''
        errors += "'Фамилия' е празно! " if lname == '' else ''
        errors += "'ЕГН' е празно! " if egn == '' else ''
        errors += "'ИД Токен' е празно! " if token == '' else ''

        if errors:
            self.lbl_status.setText(errors)
        else:
            query = f"insert into deceased_list (first_name, last_name, egn, dob, dod, token) values ('{fname}', '{lname}', '{egn}', '{dob}', '{dod}', '{token}');"
            row = insert_data_in_db(query)
            if row > 0:
                self.lbl_status.setText("Записът е създаден успешно.")
            else:
                self.lbl_status.setText("Възникна проблем при създаването на записа.")
        print(fname, lname, egn, dob, dod, token)


class AddOwnerDialog(QDialog, QtStyleTools):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.dialog = uic.loadUi('owner_dialog.ui', self)

        self.dialog.btn_cancel.clicked.connect(self.close)
        self.dialog.btn_save.clicked.connect(self.save_record)

    def save_record(self):
        fname = self.dialog.owner_fname.text()
        lname = self.dialog.owner_lname.text()
        egn = self.dialog.owner_egn.text()
        dob = self.dialog.owner_dob.date().toString('yyyy-MM-dd')
        adr = self.dialog.owner_address.text()
        start = self.dialog.owner_sdate.date().toString('yyyy-MM-dd')
        end = self.dialog.owner_edate.date().toString('yyyy-MM-dd')
        usef = 1 if self.dialog.owner_usef.isChecked() else 0

        errors = ''
        errors += "'Име' е празно! " if fname == '' else ''
        errors += "'Фамилия' е празно! " if lname == '' else ''
        errors += "'ЕГН' е празно! " if egn == '' else ''
        errors += "'Адрес' е празно! " if adr == '' else ''

        if errors:
            self.lbl_status.setText(errors)
        else:
            query = f"insert into owners_list (first_name, last_name, egn, dob, address, start_date, end_date, " \
                    f"use_forever) values ('{fname}', '{lname}', '{egn}', '{dob}', '{adr}', '{start}', '{end}', " \
                    f"'{usef}'); "
            row = insert_data_in_db(query)
            if row > 0:
                self.lbl_status.setText("Записът е създаден успешно.")
            else:
                self.lbl_status.setText("Възникна проблем при създаването на записа.")
        print(f"'{fname}', '{lname}', '{egn}', '{dob}', '{adr}', '{start}', '{end}'", usef)


class CoemeteriumHomeWindow(QMainWindow, QtStyleTools):

    def __init__(self):
        """"""
        super().__init__()
        self.main = uic.loadUi('home_window.ui', self)
        self.apply_stylesheet(self.main, 'dark_blue.xml', extra={'font_family': 'Raleway', })

        header = self.main.results_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        self.main.btn_site_find.clicked.connect(self.filter_by_loc)
        self.main.btn_dead_find.clicked.connect(self.filter_by_deceased)
        self.main.btn_owner_find.clicked.connect(self.filter_by_owner)

        self.main.btn_site_clr.clicked.connect(self.clear_table)

        self.main.actionAdd_grave.triggered.connect(self.open_gravesite_dialog)
        self.main.actionAdd_owner.triggered.connect(self.open_owner_dialog)
        self.main.actionAdd_deceased.triggered.connect(self.open_add_deceased)
        self.load_zones()
        self.load_sectors()

    def load_zones(self):
        try:
            zone_query = 'SELECT zone FROM grave_sites GROUP by zone ORDER by zone ASC;'
            zones = get_data_from_db(zone_query)
            self.main.cb_zone.addItems(zones)

        except ConnectionRefusedError:
            self.lbl_status.setText("Неуспешна връзка със сървъра!")
        except SqlQueryError as e:
            self.lbl_status.setText(e.message)

    def load_sectors(self):
        try:
            sector_query = 'SELECT sector FROM grave_sites GROUP by sector ORDER by sector ASC;'
            sectors = get_data_from_db(sector_query)
            self.main.cb_sector.addItems(sectors)

        except ConnectionRefusedError:
            self.lbl_status.setText("Неуспешна връзка със сървъра!")
        except SqlQueryError as e:
            self.lbl_status.setText(e.message)

    def open_gravesite_dialog(self):
        dialog = GravesiteDialog(self)
        dialog.exec()

    def open_owner_dialog(self):
        dialog = AddOwnerDialog(self)
        dialog.exec()

    def open_add_deceased(self):
        dialog = AddDeceasedDialog(self)
        dialog.exec()

    def filter_by_loc(self):
        zone = self.main.cb_zone.currentText()
        sector = self.main.cb_sector.currentText()
        row = self.main.tb_row.text()
        col = self.main.tb_col.text()

        zone = f"%{zone}%" if zone != '' else ''
        sector = f"%{sector}%" if sector != '' else ''
        row = f"%{row}%" if row != '' else ''
        col = f"%{col}%" if col != '' else ''

        query = f"select zone, sector, row, num from grave_sites WHERE zone = '{zone}' OR sector = '{sector}' OR row = '{row}' OR num = '{col}';"
        data = get_data_from_db(query)
        records = [d.split('|') for d in data]
        rc = len(records)
        self.main.results_table.setRowCount(rc)
        for i, row in enumerate(records):
            for j, cell in enumerate(row):
                self.main.results_table.setItem(i, j, QTableWidgetItem(cell))

        self.main.results_table.move(0, 0)

        self.main.statusbar.showMessage(f"Филтрирани са {rc} записа.", 10000)
        print("Filter clicked")

    def filter_by_deceased(self):
        fname = self.main.dead_fname.text()
        lname = self.main.dead_lname.text()
        egn = self.main.dead_egn.text()

        fname = f"%{fname}%" if fname != '' else ''
        lname = f"%{lname}%" if lname != '' else ''
        egn = f"%{egn}%" if egn != '' else ''

        query = f"select first_name, last_name, egn, dob, dod, token from deceased_list WHERE first_name like '{fname}' or last_name like '{lname}' or egn like '{egn}'; "
        data = get_data_from_db(query)
        records = [d.split('|') for d in data]
        self.clear_table()
        rc = len(records)
        offset = 4
        self.main.results_table.setRowCount(rc)
        for i, row in enumerate(records):
            for j, cell in enumerate(row):
                self.main.results_table.setItem(i, j + offset, QTableWidgetItem(cell))

        self.main.results_table.move(0, 0)

        self.main.statusbar.showMessage(f"Филтрирани са {rc} записа.", 10000)

    def filter_by_owner(self):
        fname = self.main.owner_fname.text()
        lname = self.main.owner_lname.text()
        egn = self.main.owner_egn.text()

        fname = f"%{fname}%" if fname != '' else ''
        lname = f"%{lname}%" if lname != '' else ''
        egn = f"%{egn}%" if egn != '' else ''

        query = f"select first_name, last_name, egn, start_date, end_date from owners_list WHERE first_name like '{fname}' or last_name like '{lname}' or egn like '{egn}'; "
        data = get_data_from_db(query)
        records = [d.split('|') for d in data]
        self.clear_table()
        rc = len(records)
        offset = 10
        self.main.results_table.setRowCount(rc)
        for i, row in enumerate(records):
            for j, cell in enumerate(row):
                self.main.results_table.setItem(i, j + offset, QTableWidgetItem(cell))

        self.main.results_table.move(0, 0)

        self.main.statusbar.showMessage(f"Филтрирани са {rc} записа.", 10000)


    def clear_table(self):
        while self.main.results_table.rowCount() > 0:
            self.main.results_table.removeRow(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Local file
    QFontDatabase.addApplicationFont('Raleway-Regular.ttf')

    # frame = RuntimeStylesheets()
    # frame.main.show()
    home_window = CoemeteriumHomeWindow()
    home_window.main.show()

    app.exec_()
