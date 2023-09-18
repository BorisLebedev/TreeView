""" Считывает данные о технологической документации из таблицы Excel"""

from __future__ import annotations
from dataclasses import dataclass
from pandas import isnull
from pandas import read_excel
from STC.config.config import CFG_TD
from STC.gui.splash_screen import SplashScreen, show_dialog


class ExcelRawDataFromTdDb:
    """ Список экземпляров ExcelDocumentData
        из файла с учетом технологической документации """

    def __init__(self) -> None:
        self.documents = []
        self.readExcelData()

    def readExcelData(self) -> None:
        """ Проходит построчно таблицу excel и инстанцирует ExcelDocumentData"""
        SplashScreen().basicMsg('Получение данных из Excel')
        file = CFG_TD.xl_td.folder + CFG_TD.xl_td.file_name
        sheet_name = CFG_TD.xl_td.sheet_name
        try:
            table = read_excel(file, sheet_name=sheet_name, header=None)
            self.readDocumentData(table)
        except FileNotFoundError:
            SplashScreen().close()
            show_dialog(f'{file}\nФайл не найден', 'Critical')

    def readDocumentData(self, table):
        """ Считывает реквизиты зарегистрированных документов """
        start_row = CFG_TD.xl_td.start_row
        row_total = len(table[1])
        for row in range(start_row, row_total):
            document_data = self.initExcelDocumentData(table, row)
            SplashScreen().newMessage(message=f'Считывание документов...\n'
                                              f'{document_data.document.deno}',
                                      upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=row,
                                                stages=row_total)
            if not isnull(document_data.product.name) \
                    and not isnull(document_data.product.deno) \
                    and not isnull(document_data.document.deno):
                self.documents.append(document_data)
        SplashScreen().close()

    @staticmethod
    def initExcelDocumentData(table, row):
        """ Инициализация реквизитов зарегистрированного документа"""
        return ExcelDocumentData(
            document=Document(deno=table[CFG_TD.xl_td.col_deno_td][row],
                              canceled=table[CFG_TD.xl_td.col_canceled][row],
                              canceled_date=table[CFG_TD.xl_td.col_canceled_date][row],
                              archive_num=table[CFG_TD.xl_td.col_archive_num][row],
                              complex=table[CFG_TD.xl_td.col_complex][row],
                              stage=table[CFG_TD.xl_td.col_stage][row]
                              ),
            product=Product(name=table[CFG_TD.xl_td.col_name][row],
                            deno=table[CFG_TD.xl_td.col_deno_kd][row],
                            first_app=table[CFG_TD.xl_td.col_first_app][row]
                            ),
            reg_person=Person(fio=table[CFG_TD.xl_td.col_reg_fio][row],
                              date=table[CFG_TD.xl_td.col_reg_date][row]
                              ),
            dev_person=Person(fio=table[CFG_TD.xl_td.col_dev_fio][row],
                              date=table[CFG_TD.xl_td.col_dev_date][row]
                              ),
            norm_contr=NormContr(norm_date=table[CFG_TD.xl_td.col_norm_date][row],
                                 norm_num=table[CFG_TD.xl_td.col_norm_num][row]
                                 )
        )


@dataclass
class ExcelDocumentData:
    """ Все реквизиты зарегистрированного документа """
    document: Document
    product: Product
    reg_person: Person
    dev_person: Person
    norm_contr: NormContr


@dataclass
class Product:
    """ Изделие, на которое выпущен документ """
    name: str
    deno: str
    first_app: str


@dataclass
class Document:
    """ Реквизиты и жизненный цикл документа """
    deno: str
    canceled: str
    canceled_date: str
    archive_num: str
    complex: str
    stage: str

    def __post_init__(self):
        if not isnull(self.canceled):
            self.stage = self.canceled.capitalize()


@dataclass
class NormContr:
    """ Данные по нормоконтролю """
    norm_date: str
    norm_num: str


@dataclass
class Person:
    """ ФИО и дата для разработчика или регистрирующего """
    fio: str
    date: str
