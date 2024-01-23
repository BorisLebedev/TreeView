""" Экспорт иерархических составов изделий в Excel для разных отделов """

from __future__ import annotations
import logging
import re

from os import path
from os import remove
from shutil import copy as shutil_copy
from typing import TYPE_CHECKING
from dataclasses import dataclass
from xlwings import App as xwApp
from xlwings import Book as xwBook

from STC.gui.windows.ancestors.model import StandartModel
from STC.config.config import CFG_HR
from STC.database.database import DbMkExcel
from STC.database.database import DbProduct
from STC.gui.splash_screen import SplashScreen
from STC.gui.splash_screen import show_dialog

if TYPE_CHECKING:
    from PyQt5.Qt import QStandardItem
    from STC.gui.windows.hierarchy.model import HierarchicalView
    from STC.product.product import Product
    from STC.config.config import CfgXLHierarchyForDocuments
    from STC.config.config import CfgXLHierarchyNorm
    from STC.config.config import CfgXLHierarchyNTD


def add_to_excel(product: DbProduct, only_deno: bool) -> bool:
    """ Определяет нужно ли экспортировать изделие """

    if not product.has_real_deno and only_deno:
        return False
    return True


def index_ntd(main_index: str, row: int, full: bool = True) -> str:
    index = f'{main_index}.{str(row + 1)}'
    return index if full else index[3:]


def index_mk(main_index: str, row: int, full: bool = True) -> str:
    index = f'{main_index}{str(row + 1)}.'
    return index if full else index[2:]


class ExcelExport:
    """ Родительский класс для выгрузок иерархических составов """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, tree_model: HierarchicalView,
                 config:
                 CfgXLHierarchyForDocuments |
                 CfgXLHierarchyNorm |
                 CfgXLHierarchyNTD) -> None:
        logging.info('Выгрузка данных в Excel')
        SplashScreen().newMessage(message='Определение параметров выгрузки...',
                                  stage=0,
                                  stages=6)
        self.config = config
        self.tree_model = tree_model

        self.initFilePaths()
        self.initCustomConfigData()
        self.initColumns()

        SplashScreen().newMessage(message='Создание документа...')
        shutil_copy(self.wb_main_name, self._wb_temp)

        SplashScreen().newMessage(message='Загрузка данных шаблона...')
        self.initTemplateData()

        SplashScreen().newMessage(message='Считывание данных...')
        self.getData()

        SplashScreen().newMessage(message='Открытие шаблона...')
        self.openWorkbook()

        SplashScreen().newMessage(message='Запись данных...')
        self.addDataToExcel()

        SplashScreen().newMessage(message='Сохранение выгрузки...')
        self.wb_new = self.newWorkbookName()
        self.workbook.save(self.wb_new)
        self.workbook.close()
        self.xl_app.quit()
        remove(self._wb_temp)

        SplashScreen().closeWithWindow()
        show_dialog(text=f'Завершено создание документа {self.wb_new}', m_type='info')

    def initFilePaths(self):
        """ Название и место сохранения выгрузки,
            временного файла, имени листа"""

        self.ws_main_name = self.config.sheet_name
        self.wb_main_name = path.join(self.config.template_folder,
                                      self.config.template_file)
        self._wb_temp = path.join(self.config.temp_folder,
                                  self.config.template_file)
        self.file_path = self.config.export_file_path

    def newWorkbookName(self) -> str:
        """Полное наименование выгрузки """

        file_name_prefix = self.config.file_name_prefix
        file_name_postfix = self.config.file_name_postfix
        file_name_extension = self.config.file_name_extension
        return f'{self.file_path}{file_name_prefix} ' \
               f'{self.wb_name} ' \
               f'{file_name_postfix}{file_name_extension}'

    def initCustomConfigData(self):
        """ Дополнительные данные из конфига"""

    def initColumns(self):
        """ Номера столбцов """

    def initTemplateData(self):
        """ Дополнительные данные шаблона выгрузки """

    def openWorkbook(self):
        """ Открыть книгу Excel """
        self.xl_app = xwApp(visible=False)
        self.workbook = xwBook(self._wb_temp)
        self.worksheet = self.workbook.sheets[self.ws_main_name]

    def getData(self):
        """ Генерация модели из древа со считыванием данных """

        self._standart_model = StandartModel(tree_view=self.tree_model)
        self._standart_model.getIndexes()
        self._standart_model.addData()
        self._current_row = 1
        self._tree_row_count = self._standart_model.rowCount()
        self.treeModelToList(item=self.tree_model.model.invisibleRootItem(),
                             level=0,
                             main_index='')
        SplashScreen().changeSubProgressBar(stage=0,
                                            stages=0)

    def treeModelToList(self, item: QStandardItem, level: int, main_index: str):
        """ Перевод данных модели в списки для выгрузки в Excel  """

    def addDataToExcel(self) -> None:
        """ Добавление данных в Excel """

    @property
    def wb_name(self):
        """ Наименование изделия из имени выгрузки """
        return 'НАИМЕНОВАНИЕ ИЗДЕЛИЯ'


class Excel(ExcelExport):
    """ Выгрузка иерархических составов для
        разработки технологических документов """

    def __init__(self, tree_model: HierarchicalView, full: bool = False) -> None:
        self.full = full
        super().__init__(tree_model=tree_model, config=CFG_HR.xl_h_doc)

    def initCustomConfigData(self):
        """ Дополнительные данные из конфига"""
        self.product_type_exceptions = CFG_HR.xl_h_doc.product_type_exceptions
        self.ilgach_dep = CFG_HR.xl_h_doc.ilgach_dep

    def initColumns(self):
        """ Номера столбцов """
        self.columns = ExcelData(
            list_dnkd=[],
            list_name=[],
            list_lvl=[],
            list_num=[],
            list_type=[],
            list_purchased=[],
            list_index=[],
            list_kttp=[],
            list_mk=[],
            list_kd=[],
            list_kd_code=[],
            list_kd_date=[],
            list_primary_appearance=[],
            list_need_upd=[],
            list_fio_spec=[],
            list_dep=[]
        )

    def initTemplateData(self):
        """ Инициализация строки документов """
        self.openWorkbook()
        doc_type_row = self.config.doc_type_row
        doc_type_col_start = self.config.doc_type_col_start
        doc_type_col_fin = self.config.doc_type_col_fin
        self.doc_types_excel = self.worksheet.range((doc_type_row, doc_type_col_start),
                                                    (doc_type_row, doc_type_col_fin)).value
        self.workbook.close()
        self.xl_app.quit()

    def treeModelToList(self, item: QStandardItem, level: int, main_index: str):
        """ Перевод данных модели в списки для выгрузки в Excel  """
        for row in range(item.rowCount()):
            child = item.child(row)
            sub_index = index_mk(main_index, row)
            index = sub_index[2:]
            product = item.child(row).data()

            SplashScreen().newMessage(message=f'Считывание данных...\n{sub_index}', upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=self._current_row,
                                                stages=self._tree_row_count)
            self._current_row += 1

            if product.has_real_deno or self.full:
                # if product.deno == 'УИЕС.464512.378':
                #     pass
                # creator = product.getDocumentByType(class_name='КД',
                #                                     subtype_name='Спецификация',
                #                                     setting='name_created',
                #                                     first=True)
                # if creator is None:
                #     creator = ''
                # temp_creator = creator.replace(' ', '')
                # creator_dep = 'Илгач' if temp_creator in self.ilgach_dep else ''
                creator = ''
                creator_dep = ''
                kttp = ''
                self.columns.list_lvl.append([level])
                self.columns.list_index.append([index])
                self.columns.list_name.append([item.child(row, 2).text()])

                if product.has_real_deno:
                    self.columns.list_dnkd.append([item.child(row, 3).text()])
                else:
                    self.columns.list_dnkd.append([item.child(row, 2).text()])

                if product.product_kind.name in self.product_type_exceptions:
                    self.columns.list_purchased.append([product.product_kind.name])
                else:
                    self.columns.list_purchased.append([""])

                self.columns.list_type.append([item.child(row, 4).text().capitalize()])
                self.columns.list_num.append([item.child(row, 5).text()])
                kttp = self.chooseKttp(product=product)
                self.columns.list_kttp.append([kttp])
                self.columns.list_kd_date.append([product.upd_date])
                self.columns.list_need_upd.append([str(product.hierarchy_relevance)])
                self.columns.list_primary_appearance.append([product.primary_product])
                self.columns.list_fio_spec.append([creator])
                self.columns.list_dep.append([creator_dep])
                sign_row, signs = self.generateDocumentListByType(product)
                self.columns.list_kd.append(sign_row)
                self.columns.list_mk.append(self.generateMkData(product=product,
                                                                kttp=kttp))
                self.columns.list_kd_code.append(['.'.join(list(signs)) + '.'])
                self.treeModelToList(item=child,
                                     level=level + 1,
                                     main_index=index_mk(main_index, row))

    @staticmethod
    def chooseKttp(product: Product) -> str:
        """ Выбор типового технологического процесса для выгрузки """
        documents = product.getDocumentByType(
            class_name='ТД',
            subtype_name='Карта типового (группового) технологического процесса',
            org_code='2',
            only_text=False)
        denos = sorted([document.deno for document in documents])
        if 'УИЕС.55288.00021' in denos and 'УИЕС.55288.00013' in denos:
            denos.remove('УИЕС.55288.00013')
        elif 'УИЕС.55288.00022' in denos and 'УИЕС.55288.00013' in denos:
            denos.remove('УИЕС.55288.00013')
        return chr(10).join(denos)

    def generateDocumentListByType(self, product: Product) -> tuple[list[str | None], set[str]]:
        """ Генерация строки типов документов для определенного изделия """
        signs = {'СП'}
        doc_types_excel_current = ['СП']
        doc_types_excel_current = doc_types_excel_current + ([None] * len(self.doc_types_excel))
        documents = product.documents
        for pos, sign in enumerate(self.doc_types_excel):
            for document in documents:
                if document.sign == sign and document.stage != 'Аннулирован':
                    if sign:
                        doc_types_excel_current[pos + 1] = sign
                        signs.add(sign)
        return doc_types_excel_current, signs

    @staticmethod
    def generateMkData(product: Product, kttp: str = '') -> list[str | None]:
        """ Генерация строки с данными технологии изготовления """
        data = [None] * 49
        if kttp == '':
            for document in product.documents:
                if document.subtype_name == 'Маршрутная карта' \
                        and document.stage != 'Аннулирован':
                    db_mk_excel = DbMkExcel.getMkExcel(id_document_real=document.id_document_real)
                    if db_mk_excel is not None:
                        data[0] = db_mk_excel.kind
                        data[1] = db_mk_excel.area
                        data[2] = db_mk_excel.code
                        sentences = db_mk_excel.mk_excel_sentences
                        i = 1
                        for sentence in sentences:
                            data[2 + i] = sentence.code
                            data[3 + i] = sentence.text
                            i += 2
        return data

    def addDataToExcel(self) -> None:
        """ Добавление данных в Excel """
        self.worksheet.range('L6').value = self.columns.list_num
        self.worksheet.range('JW6').value = self.columns.list_type
        self.worksheet.range('JX6').value = self.columns.list_purchased
        self.worksheet.range('K6').value = self.columns.list_dnkd
        self.worksheet.range('N6').value = self.columns.list_fio_spec
        self.worksheet.range('Q6').value = self.columns.list_dep
        self.worksheet.range('E6').value = self.columns.list_name
        self.worksheet.range('A6').value = self.columns.list_lvl
        self.worksheet.range('B6').value = self.columns.list_index
        self.worksheet.range('KA6').value = self.columns.list_kttp
        self.worksheet.range('KI6').value = self.columns.list_mk
        self.worksheet.range('AD6').value = self.columns.list_kd
        self.worksheet.range('JT6').value = self.columns.list_primary_appearance
        self.worksheet.range('JP6').value = self.columns.list_kd_date
        self.worksheet.range('JO6').value = self.columns.list_need_upd
        self.worksheet.range('JV6').value = self.columns.list_kd_code

    @property
    def wb_name(self):
        """ Наименование изделия из имени выгрузки """
        wb_main_name_new = self.columns.list_name[0][0].replace('"', '')
        wb_main_name_new = re.sub(r'[\\/:"*?<>|]+', '!', wb_main_name_new, count=0, flags=0)
        return wb_main_name_new


class ExcelNorm(ExcelExport):
    """ Выгрузка иерархических составов для
        оценки трудоемкости изготовления """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(tree_model=tree_model, config=CFG_HR.xl_h_nrm)

    def initColumns(self):
        """ Номера столбцов """
        self.columns = ExcelDataNorm(
            list_dnkd=[],
            list_name=[],
            list_lvl=[],
            list_num=[],
            list_index=[]
        )

    def treeModelToList(self, item: QStandardItem, level: int, main_index: str):
        """ Перевод данных модели в списки для выгрузки в Excel  """
        for row in range(item.rowCount()):
            child = item.child(row)
            index = index_ntd(main_index, row, False)
            product = item.child(row).data()
            self.columns.list_lvl.append([level])
            self.columns.list_index.append([index])
            self.columns.list_name.append([product.name])
            self.columns.list_dnkd.append([product.deno])
            self.columns.list_num.append([item.child(row, 5).text()])
            self.treeModelToList(item=child,
                                 level=level + 1,
                                 main_index=index_ntd(main_index, row))

    def addDataToExcel(self) -> None:
        """ Добавление данных в Excel """
        self.columns.list_index[0][0] = 'Изделие'
        self.worksheet.range('A2').value = self.columns.list_lvl
        self.worksheet.range('B2').value = self.columns.list_index
        self.worksheet.range('C2').value = self.columns.list_name
        self.worksheet.range('D2').value = self.columns.list_dnkd
        self.worksheet.range('F2').value = self.columns.list_num

    @property
    def wb_name(self):
        """ Наименование изделия из имени выгрузки """
        name = self.columns.list_name[0][0].replace('"', '')
        return re.sub(r'[\\/:"*?<>|]+', '!', name, count=0, flags=0)


class ExcelNTD(ExcelExport):
    """ Выгрузка иерархических составов для
        оценки трудоемкости сервисного обслуживания """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(tree_model=tree_model, config=CFG_HR.xl_h_ntd)

    def initColumns(self):
        """ Номера столбцов """
        self.columns = ExcelDataNTD(
            list_lvl=[],
            list_index=[],
            list_name=[],
            list_deno=[],
            list_num=[],
            list_msr=[],
        )

    def treeModelToList(self, item: QStandardItem, level: int, main_index: str):
        """ Перевод данных модели в списки для выгрузки в Excel  """
        for row in range(item.rowCount()):
            child = item.child(row)
            index = index_ntd(main_index, row, False)
            product = item.child(row).data()
            self.columns.list_lvl.append([level])
            self.columns.list_index.append([index])
            self.columns.list_name.append([f'{product.name}'])
            self.columns.list_deno.append([f'{product.deno}'])
            self.columns.list_num.append([item.child(row, 5).text()])
            self.columns.list_msr.append([item.child(row, 6).text()])
            self.treeModelToList(item=child,
                                 level=level + 1,
                                 main_index=index_ntd(main_index, row))

    def addDataToExcel(self) -> None:
        """ Добавление данных в Excel """
        self.worksheet.range('A4').value = self.columns.list_lvl
        self.worksheet.range('B4').value = self.columns.list_index
        self.worksheet.range('C4').value = self.columns.list_name
        self.worksheet.range('D4').value = self.columns.list_deno
        self.worksheet.range('E4').value = self.columns.list_num
        self.worksheet.range('F4').value = self.columns.list_msr

    @property
    def wb_name(self):
        """ Наименование изделия из имени выгрузки """
        name = self.columns.list_name[0][0].replace('"', '')
        return re.sub(r'[\\/:"*?<>|]+', '!', name, count=0, flags=0)


@dataclass
class ExcelData:
    """ Данные для выгрузки """
    # pylint: disable=too-many-instance-attributes
    list_dnkd: list
    list_name: list
    list_lvl: list
    list_num: list
    list_type: list
    list_purchased: list
    list_index: list
    list_kttp: list
    list_mk: list
    list_kd: list
    list_kd_code: list
    list_kd_date: list
    list_primary_appearance: list
    list_need_upd: list
    list_fio_spec: list
    list_dep: list
    max_row: int = 0


@dataclass
class ExcelDataNorm:
    """ Данные для выгрузки оценки трудоемкости
        изготовления изделия"""

    list_dnkd: list
    list_name: list
    list_lvl: list
    list_num: list
    list_index: list
    max_row: int = 0


@dataclass
class ExcelDataNTD:
    """ Данные для выгрузки оценки трудоемкости
        сервисного обслуживания"""

    list_lvl: list
    list_index: list
    list_name: list
    list_deno: list
    list_num: list
    list_msr: list
    max_row: int = 0
