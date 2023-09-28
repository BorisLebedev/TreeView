""" Окно внесения и редактирования документов """

from __future__ import annotations

from typing import TYPE_CHECKING

import logging
import re

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QPushButton

from STC.gui.windows.ancestors.window import WindowBasic
from STC.functions.func import deno_to_components
from STC.gui.windows.document_add_new.structure import StructureNewDocument

if TYPE_CHECKING:
    from STC.product.product import Product
    from STC.product.product import Document


class WindowNewDocument(WindowBasic):
    """ Окно изменения реквизитов документа """

    # pylint: disable=too-many-instance-attributes

    addDocument = pyqtSignal()

    def __init__(self, product: Product | None = None) -> None:
        logging.info('Инициализация окна внесения документа')
        super().__init__()
        self.title = "Внести документ"
        self.product = product
        self._documents = []
        self.td_code = None
        self.initUI()
        self.frame_spec_products = self.structure.spec_products
        self.frame_spec_products_no_deno = self.structure.spec_products_no_deno
        self.frame_spec_documents = self.structure.spec_documents
        self.initDefaultDocument()

    def initUI(self) -> None:
        """ Установка параметров окна внесения документа """

        logging.info('Установка параметров окна внесения документа')
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.size = 1000
        self.ratio = 0.75
        self.setGeometry(150, 150, self.size, int(self.size * self.ratio))
        self.structure = StructureNewDocument(self.main_layout)
        self.structure.main_data.findDocument.connect(self.addDataToFrames)
        self.structure.main_data.changeDocument.connect(self.changeDocument)
        self.apply_btn = QPushButton('Добавить')
        self.apply_btn.clicked.connect(self.addDocument)
        self.structure.btns_layout.addWidget(self.apply_btn)

    def initDefaultDocument(self) -> None:
        """ Установка вида документа по умолчанию """

        self.structure.main_data.blockSignals(True)
        self.structure.main_data.document_class = 'КД'
        self.structure.main_data.blockSignals(False)
        self.structure.main_data.document_subclass = 'Спецификация'
        self.addDataToSpecProduct()
        self.addDataToSpecDocument()

    def addDataToFrames(self) -> None:
        """ Заполнение полей рамок окна данными документа """

        logging.info('Заполнение данных')
        self.addDataToMainFrame()

    def addDataToMainFrame(self) -> None:
        """ Заполнение основных реквизитов документа """

        self.clearMainFrame()
        logging.info('Заполнение главных реквизитов')
        if self.product:
            self.addProductDataToMainFrame()
            if self.checkDocumentExistence():
                self.addDocumentDataToMainFrame()
                self.addNewDocumentDataToMainFrame()
            else:
                self.addNewDocumentDataToMainFrame()

    def addProductDataToMainFrame(self) -> None:
        """ Заполнение данных об изделии """

        self.structure.main_data.product_name = self.product.name
        self.structure.main_data.product_deno = self.product.deno
        self.structure.main_data.product_primary_application = self.product.primary_parent

    def checkDocumentExistence(self) -> bool:
        """ Проверяет существование в БД документа определенного типа,
            относящегося к определенному изделию """

        td_code_match = True
        if self.structure.main_data.document_class == 'ТД':
            self.td_code = f'{self.structure.main_data.d_type.type_code}' \
                           f'{self.structure.main_data.d_type.organization_code}' \
                           f'{self.structure.main_data.d_type.method_code}' \
                           f'.{self.structure.main_data.document_department_code}'
        self._documents = self.getDocument()
        if self.td_code and self._documents:
            td_code_match = re.fullmatch(
                r'\w{4}' + f'.{self.td_code}' + r'\d{4}', self._documents[0].deno)
        return self._documents and td_code_match

    def changeDocument(self) -> None:
        """ Обновляет поля рамки основных реквизитов документа """

        self.clearMainFrameMinorFields()
        for document in self._documents:
            if document.deno == self.structure.main_data.document_deno:
                self.addDocumentDataToMainFrame(document)

    def addDocumentDataToMainFrame(self, document: Document | None = None) -> None:
        """ Заполяет реквизиты документа """

        if document is None:
            document = self._documents[0]
            self.structure.main_data.document_deno = [document.deno for document in self._documents]
        self.structure.main_data.document_name = document.name
        self.structure.main_data.document_developer = document.name_created
        self.structure.main_data.document_date_update = document.date_changed_str
        self.structure.main_data.document_stage = document.stage
        if document.class_name == 'ТД':
            self.addDataToComplexDocument(document=document)

    def addDataToComplexDocument(self, document: Document) -> None:
        """ Добавить данные об изделиях в составном технологическом процессе """

        self.structure.main_data.document_complex = document.sub_products_new
        default_values = []
        children = document.sub_products_new
        for child, _ in children:
            row_dict = {'Обозначение': child.deno,
                        'Наименование': child.name}
            default_values.append(row_dict)
        self.structure.td_complex.defaultValues(default_values)

    def addNewDocumentDataToMainFrame(self) -> None:
        """ Возвращает список децимальных номеров для данного
            типа документа и определенного изделия """

        self.structure.main_data.document_deno = self.newDocumentDeno()

    def newDocumentDeno(self) -> list[str]:
        """ Возвращает список децимальных номеров для документа,
            включая децимальный номер нового документа """

        doc_type = self.structure.main_data.d_type
        doc_class = self.structure.main_data.document_class
        doc_denos = [document.deno for document in self._documents]
        if doc_type:
            if doc_class == 'КД':
                sign = doc_type.sign if doc_type.sign else ''
                if not doc_denos:
                    doc_denos.append(f'{self.product.deno}{sign}')
            elif doc_class == 'ТД':
                td_num = self.product.newTdDocumentNum(self.td_code)
                doc_denos.append(f'УИЕС.{self.td_code}{td_num}')
            else:
                doc_denos = []
        return doc_denos

    def getDocument(self) -> list[Document]:
        """ Возвращает документ определенного вида для определенного изделия """

        return self.product.getDocumentByType(
                    class_name=self.structure.main_data.document_class,
                    subtype_name=self.structure.main_data.document_subtype,
                    meth_code=self.structure.main_data.document_method_code,
                    org_code=self.structure.main_data.document_organization_code,
                    only_text=False)

    def clearMainFrame(self) -> None:
        """ Очистка полей рамки реквизитов документа """

        self.structure.main_data.blockSignals(True)
        self._documents = []
        self.structure.main_data.document_deno = []
        self.clearMainFrameMinorFields()
        self.structure.main_data.blockSignals(False)

    def clearMainFrameMinorFields(self) -> None:
        """ Очистка дополнительных полей реквизитов документа """

        self.structure.td_complex.cleanValues()
        self.structure.main_data.document_complex = []
        # self.structure.main_data.product_primary_application = ''
        self.structure.main_data.document_name = ''
        self.structure.main_data.document_developer = ''
        self.structure.main_data.document_date_update = ''
        self.structure.main_data.document_stage = self.structure.main_data.default_stage

    def addDataToSpecProduct(self) -> None:
        """ Заполняет рамку дочерних изделий """

        logging.info('Заполнение дочерних изделий спецификации')
        if self.product:
            default_values = []
            children = self.product.getChildren()
            for child in children:
                code_org, code_class, num, ver = deno_to_components(child.child.deno)
                row_dict = {'Наименование': child.child.name,
                            'Код': code_org,
                            'Класс': code_class,
                            'Номер': num,
                            'Исп.': ver,
                            'Кол-во': child.quantity,
                            'Ед.\nизм.': child.unit,
                            'Тип': child.product_type.type_name}
                default_values.append(row_dict)
            self.frame_spec_products.defaultValues(default_values)
            self.frame_spec_products_no_deno.defaultValues(default_values)

    def addDataToSpecDocument(self) -> None:
        """ Заполнение рамки документов согласно спецификации """

        logging.info('Заполнение документов спецификации')
        if self.product:
            table = self.frame_spec_documents.table
            documents = sorted(self.product.documents, key=lambda x: x.sign)
            for document in documents:
                row = table.rowCount() - 1
                if document.class_name == 'КД' and document.stage != 'Аннулирован':
                    table.setCurrentCell(row, 0)
                    table.cellWidget(row, 0).setCurrentText(document.sign)
