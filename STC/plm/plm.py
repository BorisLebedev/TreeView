""" Считывает данные из выгрузок PLM """
from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from os import listdir
from os import path
from dataclasses import dataclass

from pandas import DataFrame
from pandas import Series
from pandas import Timestamp
from pandas import isnull
from pandas import to_datetime

from STC.config.config import CFG_PLM
from STC.functions.func import null_cleaner


class DataFromPLM:
    """ Считывает данные из выгрузок PLM """

    def __init__(self) -> None:
        document_types = {'КД': CFG_PLM.main.folder_kd,
                          'ТД': CFG_PLM.main.folder_td}
        self.regex = DenoRegEx()
        self.products = {}
        for document_type, directory in document_types.items():
            self.directory = directory
            for file in self.getExcelFiles():
                self.plm_data = []
                self.dataframe = None
                logging.debug(file)
                _, ext = path.splitext(file)
                if ext == '.xml':
                    self.readXlm(self.getXlmTable(file))
                    dataframe = self.analyze(document_type=document_type)
                    self.doc_stages = list(dataframe['Состояние ЖЦ'].cat.categories)
                    self.products = self.getProducts(dataframe=dataframe,
                                                     document_type=document_type)

    def analyze(self, document_type: str = 'КД') -> DataFrame:
        """ Очищает и подготавливает данные для анализа """

        if self.dataframe is None:
            self.dataframe = DataFrame(self.plm_data)
        else:
            self.dataframe.append(self.plm_data)
        self.dataframe = self.setColumnTypeDatetime(self.dataframe)
        self.dataframe = self.setColumnTypeCategory(self.dataframe)
        self.dataframe = self.addColumnDeno(self.dataframe, document_type)
        self.dataframe = self.dataframe.drop(self.dataframe[isnull(self.dataframe['deno'])].index)
        self.dataframe = self.addColumnDenoDoc(self.dataframe, document_type)
        self.dataframe = self.dataframe.sort_values(by=['deno',
                                                        'Номер версии',
                                                        'Дата изменения'],
                                                    ascending=False)
        self.dataframe = self.dataframe.drop_duplicates(subset=['deno', 'Вид документа'])
        # self.dataframe.to_excel('output1.xlsx', engine='xlsxwriter')
        return self.dataframe

    def getExcelFiles(self) -> list[str]:
        """ Возвращает сортированный список файлов в директории
            (Названия PLM выгрузок состоят из дат выгрузок)"""
        files = listdir(self.directory)
        list_of_files = sorted(files)
        return list_of_files

    def getXlmTable(self, file: str) -> ET.Element:
        """ Считывание данных из xlm """

        tree = ET.parse(path.join(self.directory, file))
        root = tree.getroot()
        table = root[2][0]
        return table

    def readXlm(self, table: ET.Element) -> None:
        """ Считывание данных из xlm """

        for row in table:
            product_data = {}
            for cell_num, cell in enumerate(row):
                try:
                    value = str(cell[0].text)
                except IndexError:
                    value = None
                prop = str(table[0][cell_num][0].text)
                product_data.update({prop: value})
            if product_data[prop] != prop:
                self.plm_data.append(product_data)

    def getProducts(self, dataframe: DataFrame, document_type: str) -> dict[str, PLMProduct]:
        """ Возвращает словарь экземпляров промежуточного класса PLMProduct
            для хранения данных об уникальных изделиях и документах
            с ними связанных """

        row_with_name = 'Имя'
        if document_type == 'ТД':
            row_with_name = 'Наименование'
        for _, row in dataframe.iterrows():
            try:
                plm_product = self.products[row['deno']]
            except KeyError:
                plm_product = PLMProduct(row['deno'])
                self.products.update({row['deno']: plm_product})
            plm_product.name = row[row_with_name]
            plm_document = self.getDocument(row=row,
                                            row_with_name=row_with_name)
            plm_product.setDocument(plm_document)
        return self.products

    def getDocument(self, row, row_with_name: str) -> PLMDocument:
        """ Возвращает документ, составленный из реквизитов документа
            указанных в строке """

        deno_doc = self.denoCleaner(row=row)
        doc_lifecycle = \
            PLMDocumentLifeCycle(
                stage=null_cleaner(row['Состояние ЖЦ']),
                name_created=row['Создал'],
                name_changed=row['Изменил'],
                date_created=to_datetime(row['Дата создания'],
                                         unit='s',
                                         origin='unix'),
                date_changed=to_datetime(row['Дата изменения'],
                                         unit='s',
                                         origin='unix'))

        document = PLMDocument(d_type=row['Вид документа'],
                               deno=deno_doc,
                               name=row[row_with_name],
                               file_name=row['Файл'],
                               lifecycle=doc_lifecycle)
        return document

    def addColumnDeno(self, dataframe: DataFrame, document_type: str) -> DataFrame:
        """ Добавляет столбец с децимальным номером изделия """

        if document_type == 'КД':
            dataframe['deno'] = dataframe['Имя'].str.extract(self.regex.regex_kd)
        elif document_type == 'ТД':
            dataframe['deno'] = dataframe['Имя']
            for row in dataframe.itertuples():
                index = row.Index
                deno = re.findall(self.regex.regex_td,
                                  dataframe.loc[index, 'Имя'])
                if not deno:
                    deno = re.findall(self.regex.regex_td,
                                      dataframe.loc[index, 'Файл'])
                dataframe.loc[index, 'deno'] = deno[0] if deno else None
        return dataframe

    def addColumnDenoDoc(self, dataframe: DataFrame, document_type: str) -> DataFrame:
        """ Добавляет столбец с децимальным номером документа """
        if document_type == 'КД':
            return self.addColumnDenoDocKD(dataframe)
        return self.addColumnDenoDocTD(dataframe)

    def addColumnDenoDocKD(self, dataframe: DataFrame) -> DataFrame:
        """ Добавляет столбец с децимальным номером
            документа конструкторской документации """

        dataframe['deno_doc'] = dataframe['Имя'].str.extract(self.regex.regex_kd)
        dataframe['Имя'].replace(self.regex.regex_name_cleaner,
                                 '', regex=True, inplace=True)
        dataframe['Имя'].replace(self.regex.space_start,
                                 '', regex=True, inplace=True)
        return dataframe

    def addColumnDenoDocTD(self, dataframe: DataFrame) -> DataFrame:
        """ Добавляет столбец с децимальным номером
            документа технологической документации """

        dataframe['deno_doc'] = dataframe['Имя']
        for row in dataframe.itertuples():
            index = row.Index
            deno = re.findall(self.regex.regex_td_doc,
                              dataframe.loc[index, 'Имя'])
            if not deno:
                deno = re.findall(self.regex.regex_td_doc,
                                  dataframe.loc[index, 'Файл'])
            dataframe.loc[index, 'deno_doc'] = deno[0] if deno else None
        return dataframe

    @staticmethod
    def denoCleaner(row: Series) -> str:
        """ Очистка децимальных номеров неправильных форматов """

        text = str(row['deno_doc'])
        if text[-2:] == 'СП':
            return text[:-2]
        return row['deno_doc']

    @staticmethod
    def setColumnTypeCategory(dataframe: DataFrame) -> DataFrame:
        """ Определяет тип для данных,
            разбитых на категории """

        for col_name in ['Вид документа', 'Номер версии', 'Создал', 'Состояние ЖЦ',
                         'Литера', 'Формат', 'Шаблон', 'Логические проблемы',
                         'Изменил', 'Заблокировал', 'Локальная копия']:
            dataframe[col_name] = dataframe[col_name].astype('category')
        return dataframe

    @staticmethod
    def setColumnTypeDatetime(dataframe: DataFrame) -> DataFrame:
        """ Определяет тип для дат """

        for col_name in ['Дата изменения',
                         'Дата блокировки',
                         'Дата создания',
                         'Дата актуализации']:
            dataframe[col_name] = dataframe[col_name].astype('datetime64')
        return dataframe


class PLMProduct:
    """ Отображает свойства изделия, полученные
        при анализе реквизитов документов в PLM """

    def __init__(self, deno: str) -> None:
        self.deno = deno
        self._name = None
        self.documents = {}

    @property
    def name(self) -> str:
        """ Наименование изделия """
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        """ Наименование изделия """
        self._name = str(value).replace('"', '')

    def setDocument(self, plm_document: PLMDocument):
        """ Привязывает документы к данному изделию.
            В качестве ключа используется децимальный номер и
            тип документа """
        # TODO может быть более 1 документа одного вида на 1 продукт
        id_document = str(self.deno) + str(plm_document.d_type)
        self.documents[id_document] = plm_document


@dataclass
class PLMDocument:
    """ Отображает свойства документа, полученные
        при анализе реквизитов документов в PLM """

    d_type: str
    deno: str
    name: str
    file_name: str
    lifecycle: PLMDocumentLifeCycle


@dataclass
class PLMDocumentLifeCycle:
    """ Жизненный цикл документа  """

    stage: str
    name_created: str
    name_changed: str
    date_created: Timestamp
    date_changed: Timestamp


class DenoRegEx:
    """ Составные части для регулярных выражений """

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        self.deno_dev = r'[А-Я]{4}'
        self.deno_code = r'\.[0-9]{6}\.[0-9]{3}'
        self.deno_code_spo = r'\.[0-9]{5}-[0-9]{2}'
        self.deno_code_td = r'\.[0-9]{5}\.[0-9]{5}'
        self.deno_var = r'-[0-9]{2,3}'
        self.deno_text = r'[А-Я-0-9]*'
        self.bracket_open = r'(\[+))'
        self.bracket_close = r'(\]:[0-9]*)'
        self.space_mult = r'([ ]{2,10})'
        self.space_start = r'(^[ ]+)'

    @property
    def deno_r(self):
        """ АБВГ.123456.789-123 """
        return f'{self.deno_dev}{self.deno_code}{self.deno_var}'

    @property
    def deno_r_td(self):
        """ АБВГ.12345.12345 """
        return f'{self.deno_dev}{self.deno_code_td}'

    @property
    def deno_r_text(self):
        """ АБВГ.123456.789-123Текст """
        return f'{self.deno_r}{self.deno_text}'

    @property
    def deno_r_00(self):
        """ АБВГ.12345-12-123 """
        return f'{self.deno_dev}{self.deno_code_spo}{self.deno_var}'

    @property
    def deno_r_00_text(self):
        """ АБВГ.12345-12-123Текст """
        return f'{self.deno_r_00}{self.deno_text}'

    @property
    def deno_r_soft(self):
        """ АБВГ.123456.123 """
        return f'{self.deno_dev}{self.deno_code}'

    @property
    def deno_r_soft_text(self):
        """ АБВГ.123456.123Текст """
        return f'{self.deno_r_soft}{self.deno_text}'

    @property
    def regex_kd(self):
        """ Децимальный номер изделия из документа КД """
        return fr'.*({self.deno_r_00}|{self.deno_r}|{self.deno_r_soft}).*'

    @property
    def regex_td(self):
        """ Децимальный номер изделия из документа ТД """
        return fr'({self.deno_r_00}|{self.deno_r}|{self.deno_r_soft})'

    @property
    def regex_name_cleaner(self):
        """ Убрать из названия все, что не относиться к названию изделия """
        return f'({self.deno_r_00_text}' \
               f'|{self.deno_r_text}' \
               f'|{self.deno_r_soft_text}' \
               f'|{self.bracket_open}' \
               f'|{self.bracket_close}' \
               f'|{self.space_mult}'

    @property
    def regex_td_doc(self):
        """ Децимальный номер документа ТД """
        return fr'{self.deno_r_td}'
