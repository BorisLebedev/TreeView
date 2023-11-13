""" Импорт из Excel иерархических составов """

from __future__ import annotations

import re
from datetime import datetime
from os import listdir
from os import path

from pandas import DataFrame
from pandas import isnull
from pandas import read_excel

from STC.config.config import CFG_HR
from STC.database.database import DbProduct
from STC.database.database import DbProductKind
from STC.database.database import DbProductType
from STC.functions.func import null_cleaner
from STC.gui.splash_screen import SplashScreen


class ExcelData:

    """Содержит данные о всех изделиях
       из файлов excel по которым ведется
       обновление. Так как данные часто повторяются
       предварительная агрегация данных перед внесением
       в БД желательна.

       Проходит по файлам Excel в заданной директории
       и формирует экземпляр ExcelProduct для каждого
       изделия, собирая данные по проектам и ТД

       Например:

       products = {'АБВГ.123456.789': ExcelProduct1,
                   'АБВГ.123456.987': ExcelProduct2}

       documents_td = {'Обозначение ТД': {'Проект 1', 'Проект 2', 'Проект 3'}}"""

    def __init__(self) -> None:
        self.products = {}
        self.project = None
        self.documents_td = {}
        self.deno_col = CFG_HR.xl_h_doc.deno_col
        files = self.getExcelFiles(CFG_HR.xl_h_doc.folder)
        stages = len(self.getExcelFiles(CFG_HR.xl_h_doc.folder))
        for stage, file in enumerate(files):
            name, ext = path.splitext(file)
            if ext == CFG_HR.xl_h_doc.file_name_extension:
                SplashScreen().changeSubProgressBar(stage=stage, stages=stages)
                self.projectName(name)
                self.readExcelData(path.join(CFG_HR.xl_h_doc.folder, file))
        SplashScreen().changeSubProgressBar(stage=0, stages=0)

    def projectName(self, name: str) -> None:
        """ Вырезает имя проекта из названия файла"""
        project = name[len(f'{CFG_HR.xl_h_doc.file_name_prefix}') + 1:]
        self.project = project.lstrip().rstrip()

    def readExcelData(self, file: str) -> None:
        """ Проходит по строкам таблицы состава изделия,
            создает для каждой строки ExcelProduct.
            Добавляет ExcelProduct в словарь с ключом по обозначению изделия
            Например: {'АБВГ.123456.789': ExcelProduct1,
                       'АБВГ.123456.987': ExcelProduct2}"""
        SplashScreen().newMessage(message=f'Импорт данных Excel...\n{self.project}',
                                  stage=SplashScreen().stage)
        table = read_excel(file, sheet_name=CFG_HR.xl_h_doc.sheet_name, header=None)
        start_row = CFG_HR.xl_h_doc.doc_type_row + 1
        stages = len(table[1]) - start_row - 1
        for row in range(start_row, len(table[1])):
            SplashScreen().changeSubProgressBar(stage=row, stages=stages)
            deno = table[self.deno_col][row]
            try:
                product = self.products[deno]
                product.resetAttr(table, row, self.project)
            except KeyError:
                product = ExcelProduct(table, row, self.project)
            if row == start_row:
                product.main_project = self.project
            self.products.update({product.deno: product})

    @staticmethod
    def getExcelFiles(directory: str) -> list[str]:
        """ Сортирует файлы от старых к новым"""
        files = listdir(directory)
        list_of_files = sorted(files, key=lambda x: path.getmtime(path.join(directory, x)))
        return list_of_files


class ExcelProduct:
    """ Собирает данные по изделию из определенной строки
        из файла excel "Список КД и ТД"
        Включает в себя: name = "АЦРП"
                         deno = "АБВГ.123456.789"
                         index = "1.1"
                         projects = {'Проект 1','Проект 2','Проект 3'}
                         documents_td = {'АБВГ.552000.00001': {'Проект 1', 'Проект 2', 'Проект 3'},
                                         'АБВГ.552000.00002': {'Проект 1', 'Проект 3'},
                                         'АБВГ.552000.00003': {'Проект 2', 'Проект 3'}}
                         document_signs = ['СП','СБ','Э4']
                         subproducts = [ExcelSubProduct1, ExcelSubProduct2, ExcelSubProduct3]"""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, table: DataFrame, row: int, project: str) -> None:
        self.projects = set()
        self._name = None
        self._deno = None
        self._index = None
        self._is_new = None
        self._id_kind = None
        self.main_project = None
        self.upd_date = None
        self._primary_application = None
        self.purchased = ''
        self.document_signs = []
        self.subproducts = []
        self.documents_td = {}
        self.index_col = CFG_HR.xl_h_doc.index_col
        self.deno_col = CFG_HR.xl_h_doc.deno_col
        self.name_col = CFG_HR.xl_h_doc.name_col
        self.purchased_col = CFG_HR.xl_h_doc.purchased_col
        self.doc_first_col = CFG_HR.xl_h_doc.doc_first_col
        self.doc_last_col = CFG_HR.xl_h_doc.doc_last_col
        self.upd_date_col = CFG_HR.xl_h_doc.upd_date_col
        self.primary_application_col = CFG_HR.xl_h_doc.primary_application_col
        self.resetAttr(table, row, project)

    def resetAttr(self, table: DataFrame, row: int, project: str) -> None:
        """ Переопределяет аттрибуты (для соответствия более актуальным данным) """
        date = table[self.upd_date_col][row]
        if isnull(date) or not isinstance(date, datetime):
            upd_date = datetime.min
        else:
            upd_date = date
        if not self.upd_date:
            self.upd_date = upd_date
        if upd_date >= self.upd_date:
            self.upd_date = upd_date
            self.name = table[self.name_col][row]
            self.deno = table[self.deno_col][row]
            self.index = table[self.index_col][row]
            self.id_kind = table[self.purchased_col][row]
            self.primary_application = null_cleaner(table[self.primary_application_col][row])
            self.readExcelDocumentTypes(table, row)
            self.readExcelSubproduct(table, row)
            self.addProject(project)
            document_td = ExcelTdDocument(table=table, row=row)
            if document_td.td_deno != ExcelTdDocument.none_deno:
                self.documents_td[document_td.td_deno] = document_td

    def addProject(self, project: str) -> None:
        """ Добавляет название нового проекта в котором встретилось данное изделие
                из названия файла
                Например: {'Проект 1','Проект 2','Проект 3'}"""
        self.projects.add(project)

    def readExcelDocumentTypes(self, table: DataFrame, row: int) -> None:
        """ Считывает типы КД указанные в excel в виде обозначений
                Например: ['СП','СБ','Э4']"""
        for column in range(self.doc_first_col, self.doc_last_col):
            sign = table[column][row]
            if not isnull(sign):
                sign = sign.upper()
                self.document_signs.append(sign)

    def readExcelSubproduct(self, table: DataFrame, row: int) -> None:
        """ Считывает входящие изделия на один уровень входимости ниже
                записывает их как список экземпляров ExcelSubProduct
                Например: [ExcelSubProduct1, ExcelSubProduct2, ExcelSubProduct3]"""
        new_subproducts = []
        if row + 1 != len(table[self.index_col]):
            level = str(self.index).count('.')
            j = row + 1
            level_next = str(table[1][j]).count('.')
            while (level < level_next) and (j < len(table[self.index_col])):
                if level + 1 == level_next:
                    subproduct = ExcelSubProduct(table, j)
                    new_subproducts.append(subproduct)
                j += 1
                if j < len(table[self.index_col]):
                    level_next = str(table[self.index_col][j]).count('.')
        if new_subproducts:
            self.subproducts = new_subproducts

    @property
    def name(self) -> str:
        """ Наименование изделия """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = str(value)

    @property
    def deno(self) -> str:
        """ Децимальный номер """
        return self._deno

    @deno.setter
    def deno(self, value: str) -> None:
        if self._name == value:
            self._deno = self._name
        else:
            self._deno = str(value).replace(' ', '')

    @property
    def index(self) -> str:
        """ Индекс входимости (1.2.3) """
        return self._index

    @index.setter
    def index(self, value: str) -> None:
        self._index = str(value).replace(' ', '')

    @property
    def primary_application(self) -> str:
        """ Децимальный номер первичной применяемости """
        return self._primary_application

    @primary_application.setter
    def primary_application(self, value: str) -> None:
        if not isnull(value):
            self._primary_application = str(value).replace(' ', '')

    @property
    def is_new(self):
        """ Являются ли данные об изделии более новыми
            чем те что уже имеются """
        if self._is_new is None:
            try:
                db_product = DbProduct.data[self.deno]
                upd_date = db_product.date_check
                if isnull(upd_date) or not isinstance(upd_date, datetime):
                    upd_date = datetime.min
                if upd_date > self.upd_date:
                    self._is_new = False
                else:
                    self._is_new = True
            except KeyError:
                self._is_new = True
        return self._is_new

    @property
    def id_kind(self):
        """ Вид изделия """
        return self._id_kind

    @id_kind.setter
    def id_kind(self, name_short):
        product_kind = DbProductKind.data.get(name_short, None)
        if product_kind is not None:
            self._id_kind = int(product_kind.id_kind)
        else:
            self._id_kind = None


class ExcelTdDocument:
    """ Данные технологического документа из Excel """

    none_deno = 'Неизвестно'

    def __init__(self, table: DataFrame, row: int):
        self.mk_code = None
        self.operations = None
        self.td_type = None
        self.mk_place = None
        self.td_deno = self.initTdDeno(table=table,
                                       row=row)
        self.readMkOperations(table=table,
                              row=row)

    def initTdDeno(self, table: DataFrame, row: int) -> str:
        """ Определение децимального номера технологического документа """
        deno = null_cleaner(
            table[CFG_HR.xl_h_doc.doc_td_deno][row])
        if deno is not None:
            if re.fullmatch(r'\w{4}.\d{5}.\d{5}', deno):
                return table[CFG_HR.xl_h_doc.doc_td_deno][row]
        return self.__class__.none_deno

    def readMkOperations(self, table: DataFrame, row: int) -> None:
        """ Чтение данных МК """
        doc_td_org_type = null_cleaner(
            table[CFG_HR.xl_h_doc.doc_td_org_type][row])
        mk_code = null_cleaner(
            table[CFG_HR.xl_h_doc.mk_code_col][row])
        if mk_code is not None and \
                self.td_deno != self.__class__.none_deno and \
                doc_td_org_type != 'Т':
            self.mk_code = mk_code
            self.operations = {}
            self.td_type = null_cleaner(
                table[CFG_HR.xl_h_doc.mk_type_col][row])
            self.mk_place = null_cleaner(
                table[CFG_HR.xl_h_doc.mk_place_col][row])
            self.readMkOperationsSentences(table=table, row=row)

    def readMkOperationsSentences(self, table: DataFrame, row: int) -> None:
        """ Чтение текста МК """
        i = 1
        num = 1
        code = null_cleaner(
            table[CFG_HR.xl_h_doc.mk_code_col + i][row])
        text = null_cleaner(
            table[CFG_HR.xl_h_doc.mk_code_col + i + 1][row])
        while i < 25 and code is not None:
            self.operations[num] = (code, text)
            i += 2
            num += 1
            code = null_cleaner(
                table[CFG_HR.xl_h_doc.mk_code_col + i][row])
            text = null_cleaner(
                table[CFG_HR.xl_h_doc.mk_code_col + i + 1][row])


class ExcelSubProduct:
    """ Изделие из состава другого изделия."""
    # pylint: disable=too-many-instance-attributes

    def __init__(self, table: DataFrame, row: int) -> None:
        self.name = table[CFG_HR.xl_h_doc.name_col][row]
        self.deno = table[CFG_HR.xl_h_doc.deno_col][row]
        self.quantity = table[CFG_HR.xl_h_doc.quantity_col][row]
        self.product_type = table[CFG_HR.xl_h_doc.type_col][row]

    @ property
    def name(self) -> str:
        """ Наименование """
        return self._name

    @ name.setter
    def name(self, value: str) -> None:
        self._name = value
        # self._name = str(value).replace('"', '')

    @ property
    def deno(self) -> str:
        """ Децимальный номер """
        return self._deno

    @ deno.setter
    def deno(self, value: str) -> None:
        if self._name == value:
            self._deno = self._name
        else:
            self._deno = str(value).replace(' ', '')

    @ property
    def quantity(self) -> int:
        """ Количество в составе изделия более высокого уровня """
        return self._quantity

    @ quantity.setter
    def quantity(self, value: int) -> None:
        if isnull(value):
            value = 0
        else:
            value = str(value).replace(' ', '')
            # value = int(value)
        self._quantity = value

    @ property
    def product_type(self) -> str:
        """ Тип изделия по разделу спецификации """
        return self._product_type

    @ product_type.setter
    def product_type(self, value: str) -> None:
        value = str(value).lower()
        product_type = self.readProductType(value)
        self._product_type = product_type

    @staticmethod
    def readProductType(product_type_excel: str) -> DbProductType:
        """ Определяет тип изделия по названию раздела спецификации """
        product_types = DbProductType.data
        if isnull(product_type_excel):
            product_type = product_types['неизвестно']
        else:
            try:
                product_type = product_types[product_type_excel]
            except KeyError:
                product_type = product_types['неизвестно']
        return product_type
