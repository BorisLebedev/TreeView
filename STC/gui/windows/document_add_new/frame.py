from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.product.product import Product
    from STC.product.product import DocumentType

import logging
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QPoint
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QTableWidgetItem
from STC.config.config import CONFIG
from STC.gui.windows.ancestors.frame import FrameBasic
from STC.gui.windows.ancestors.frame import FrameWithTable
from STC.product.product import return_document_type
from STC.product.product import ProductBuilder
from STC.product.product import DocumentType
from STC.product.product import ProductType
from STC.product.product import DocumentStage
from STC.functions.func import join_deno
from STC.gui.windows.ancestors.context_menu import ContextMenuForSpecProductsTable


# Рамка для основных реквизитов документа
class NewDocumentMainFrame(FrameBasic):
    findDocument = pyqtSignal()
    changeDocument = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(frame_name='Основные данные',
                         frame_type='NewDocumentBasic')
        self._department_codes = {}
        self._organization_codes = {}
        self._method_codes = {}
        self._stage_letters = []
        self._complex_list = []
        self._db_types = DocumentType.documentTypes()
        self.default_stage = 'Доступен для регистрации'
        self._stages = [db_stage.stage for db_stage in DocumentStage.getAllStages()] + [self.default_stage]
        self.d_type = None
        self._sep = ': '
        self._def_kd_type = return_document_type(class_name='КД', subtype_name='Спецификация')
        self._def_td_type = return_document_type(class_name='ТД', subtype_name='Маршрутная карта')
        self.initWidgetLabel()
        self.initWidgetLineEdit()
        self.initWidgetCombobox()
        self.initWidgetButton()
        visibility_settings_td = {'КД': False, 'ТД': True, 'PLM': False}
        self.visibility = {self._l_doc_org: visibility_settings_td,
                           self._l_doc_method: visibility_settings_td,
                           self._l_doc_dep: visibility_settings_td,
                           self._doc_org: visibility_settings_td,
                           self._doc_method: visibility_settings_td,
                           self._doc_dep: visibility_settings_td,
                           self._l_doc_complex: visibility_settings_td,
                           self._doc_complex: visibility_settings_td,
                           self._btn_doc_complex: visibility_settings_td}
        self.initWidgetComboboxDefault()
        self.initWidgetComboboxConnection()

        self.modifyComboboxValues(attr='class')
        self.initWidgetPosition()

    def initWidgetLabel(self) -> None:
        self._l_doc_class = QLabel('Тип документации')
        self._l_doc_subclass = QLabel('Тип документа')
        self._l_doc_type = QLabel('Подтип документа')
        self._l_doc_subtype = QLabel('Вид документа')

        self._l_doc_org = QLabel('Тип ТП по организации')  # ТД
        self._l_doc_method = QLabel('Тип ТП по методу выполнения')  # ТД
        self._l_doc_dep = QLabel('Отдел')  # ТД

        self._l_product_name = QLabel('Наименование изделия')
        self._l_product_deno = QLabel('Обозначение изделия')

        self._l_doc_name = QLabel('Наименование документа')
        self._l_doc_deno = QLabel('Обозначение документа')

        self._l_product_papp = QLabel('Перв. применяемость')  # КД
        self._l_doc_dev = QLabel('ФИО разаработчика')  # КД
        self._l_doc_update = QLabel('Дата изменения')  # КД

        self._l_doc_pages = QLabel('Количество листов')
        self._l_doc_lit = QLabel('Литера')
        self._l_doc_stage = QLabel('Этап разработки')  # ТД
        self._l_doc_complex = QLabel('Изготавливается совместно с')  # ТД

    def initWidgetLineEdit(self) -> None:
        self._product_name = QLineEdit()
        self._product_deno = QLineEdit()
        self._doc_name = QLineEdit()
        self._product_papp = QLineEdit()
        self._doc_dev = QLineEdit()
        self._doc_update = QLineEdit()
        self._doc_complex = QLineEdit()
        self._doc_complex.setText(f'{0} изделий в составе')
        self._doc_complex.setReadOnly(True)

    def initWidgetCombobox(self) -> None:
        self._doc_class = QComboBox()
        self._doc_subclass = QComboBox()
        self._doc_type = QComboBox()
        self._doc_subtype = QComboBox()
        self._doc_org = QComboBox()
        self._doc_method = QComboBox()
        self._doc_dep = QComboBox()
        self._doc_lit = QComboBox()
        self._doc_stage = QComboBox()
        self._doc_pages = QComboBox()
        self._doc_deno = QComboBox()
        self._doc_deno.currentTextChanged.connect(self.changeDocument)

    def initWidgetButton(self) -> None:
        self._btn_doc_complex = QPushButton()
        self._btn_doc_complex.setIcon(CONFIG.style.arrow_right)

    def initWidgetPosition(self) -> None:
        cbs = {self._l_doc_class: self._doc_class,
               self._l_doc_subclass: self._doc_subclass,
               self._l_doc_type: self._doc_type,
               self._l_doc_subtype: self._doc_subtype,
               self._l_doc_org: self._doc_org,
               self._l_doc_method: self._doc_method,
               self._l_doc_dep: self._doc_dep,
               self._l_doc_deno: self._doc_deno,
               self._l_doc_stage: self._doc_stage,
               self._l_product_name: self._product_name,
               self._l_product_deno: self._product_deno,
               self._l_doc_name: self._doc_name,
               self._l_product_papp: self._product_papp,
               self._l_doc_dev: self._doc_dev,
               self._l_doc_update: self._doc_update,
               self._l_doc_complex: (self._doc_complex, self._btn_doc_complex)
               }
        row = 0
        for row, label in enumerate(cbs.keys()):
            self.main_layout.addWidget(label, row, 0)
            if isinstance(cbs[label], tuple):
                for column, widget in enumerate(cbs[label]):
                    self.main_layout.addWidget(widget, row, column + 1)
            else:
                self.main_layout.addWidget(cbs[label], row, 1, 1, -1)
        self.main_layout.setRowStretch(row + 1, 1)
        self.main_layout.setColumnStretch(1, 1)

    def initWidgetComboboxDefault(self) -> None:
        self._doc_org.addItems(self.organization_codes.keys())
        self._doc_method.addItems(self.method_codes.keys())
        self._doc_dep.addItems(self.department_codes.keys())
        self._doc_lit.addItems(self.stage_letters)
        self._doc_stage.addItems(self._stages)
        self._doc_pages.addItems([str(num) for num in range(100)])

    def initWidgetComboboxConnection(self) -> None:
        # self._doc_class.currentIndexChanged.connect(self.generateHierarchy)
        self._doc_class.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='subclass'))
        self._doc_subclass.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='type'))
        self._doc_type.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='subtype'))
        self._doc_subtype.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='document'))
        self._doc_org.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='document'))
        self._doc_method.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='document'))
        self._doc_dep.currentIndexChanged.connect(lambda: self.modifyComboboxValues(attr='document'))

    def widgetVisibility(self) -> None:
        try:
            for widget, settings in self.visibility.items():
                widget.setVisible(settings[self.document_class])
        except KeyError:
            logging.debug('Не найден случай для класса документации')

    def setComboboxValues(self, attr: str) -> list[str]:
        _cb_values = []
        for db_type in self._db_types:
            if attr == 'class':
                _cb_values.append(db_type.class_name)
            elif attr == 'subclass':
                if self._doc_class.currentText() == db_type.class_name:
                    _cb_values.append(db_type.subclass_name)
            elif attr == 'type':
                if self._doc_subclass.currentText() == db_type.subclass_name and \
                        self._doc_class.currentText() == db_type.class_name:
                    _cb_values.append(db_type.type_name)
            elif attr == 'subtype':
                if self._doc_type.currentText() == db_type.type_name and \
                        self._doc_class.currentText() == db_type.class_name:
                    _cb_values.append(self.mergeSignAndSubtype(db_type))
        return sorted(list(set(_cb_values)))

    def defaultDocumentType(self, attr: str) -> None:
        if attr == 'subclass':
            if self._doc_class.currentText() == self._def_kd_type.class_name:
                self._doc_subclass.setCurrentText(self._def_kd_type.subclass_name)
            elif self._doc_class.currentText() == self._def_td_type.class_name:
                self._doc_subclass.setCurrentText(self._def_td_type.subclass_name)
        elif attr == 'type':
            if self._doc_subclass.currentText() == self._def_kd_type.subclass_name:
                self._doc_type.setCurrentText(self._def_kd_type.type_name)
            elif self._doc_subclass.currentText() == self._def_td_type.subclass_name:
                self._doc_type.setCurrentText(self._def_td_type.type_name)
        elif attr == 'subtype':
            if self._doc_type.currentText() == self._def_kd_type.type_name:
                self._doc_subtype.setCurrentText(self.mergeSignAndSubtype(self._def_kd_type))
            elif self._doc_type.currentText() == self._def_td_type.type_name:
                self._doc_subtype.setCurrentText(self.mergeSignAndSubtype(self._def_td_type))

    def modifyComboboxValues(self, attr: str) -> None:
        if attr == 'class':
            items = self.setComboboxValues(attr)
            self._doc_class.blockSignals(True)
            self._doc_class.clear()
            self._doc_class.blockSignals(False)
            self._doc_class.addItems(items)
        elif attr == 'subclass':
            items = self.setComboboxValues(attr)
            self._doc_subclass.blockSignals(True)
            self._doc_subclass.clear()
            self._doc_subclass.blockSignals(False)
            self._doc_subclass.addItems(items)
            self.defaultDocumentType(attr=attr)
        elif attr == 'type':
            items = self.setComboboxValues(attr)
            self._doc_type.blockSignals(True)
            self._doc_type.clear()
            self._doc_type.blockSignals(False)
            self._doc_type.addItems(items)
            self.defaultDocumentType(attr=attr)
        elif attr == 'subtype':
            items = self.setComboboxValues(attr)
            self._doc_subtype.blockSignals(True)
            self._doc_subtype.clear()
            self._doc_subtype.blockSignals(False)
            self._doc_subtype.addItems(items)
            self.defaultDocumentType(attr=attr)
        elif attr == 'document':
            self.documentChanged()

    def documentChanged(self) -> None:
        self.d_type = return_document_type(class_name=self.document_class,
                                           subtype_name=self.document_subtype,
                                           method_code=self.document_method_code,
                                           organization_code=self.document_organization_code)
        self.widgetVisibility()
        self.findDocument.emit()

    def mergeSignAndSubtype(self, db_type: DocumentType) -> str:
        sign = f'{db_type.sign}{self._sep}' if db_type.sign else ''
        return f'{sign}{db_type.subtype_name}'

    @property
    def department_codes(self) -> dict[str, str]:
        if not self._department_codes:
            for department_name, code in CONFIG.data['document_department'].items():
                self._department_codes[department_name] = code
        return self._department_codes

    @property
    def organization_codes(self) -> dict[str, str]:
        if not self._organization_codes:
            for organization_type, code in CONFIG.data['document_organization'].items():
                self._organization_codes[organization_type] = code
        return self._organization_codes

    @property
    def method_codes(self) -> dict[str, str]:
        if not self._method_codes:
            for method_name, code in CONFIG.data['document_method'].items():
                self._method_codes[method_name] = code
        return self._method_codes

    @property
    def stage_letters(self):
        if not self._stage_letters:
            return CONFIG.data['document_settings']['litera'].replace(' ', '').split(',')
        return self._stage_letters

    @property
    def document_class(self) -> str:
        return self._doc_class.currentText()

    @document_class.setter
    def document_class(self, value: str) -> None:
        self._doc_class.setCurrentText(value)
        self.modifyComboboxValues(attr='subclass')

    @property
    def document_subclass(self) -> str:
        return self._doc_subclass.currentText()

    @document_subclass.setter
    def document_subclass(self, value: str) -> None:
        self._doc_subclass.setCurrentText(value)
        self.modifyComboboxValues(attr='type')

    @property
    def document_type(self) -> str:
        return self._doc_type.currentText()

    @property
    def document_subtype(self) -> str:
        text = self._doc_subtype.currentText()
        if text.find(self._sep) != -1:
            index = text.find(self._sep) + len(self._sep)
            text = text[index:]
        logging.debug(f'{text}')
        return text

    @property
    def product_name(self) -> str:
        return self._product_name.text()

    @product_name.setter
    def product_name(self, text: str) -> None:
        self._product_name.setText(text)

    @property
    def product_deno(self) -> str:
        return self._product_deno.text()

    @product_deno.setter
    def product_deno(self, text: str) -> None:
        self._product_deno.setText(text)

    @property
    def document_name(self) -> str:
        return self._doc_name.text()

    @document_name.setter
    def document_name(self, text: str) -> None:
        self._doc_name.setText(text)

    @property
    def document_deno(self) -> str:
        if self._doc_deno.currentText() == '':
            return self.product_deno
        return self._doc_deno.currentText()

    @document_deno.setter
    def document_deno(self, text: str) -> None:
        self._doc_deno.clear()
        self._doc_deno.addItems(text)

    @property
    def product_primary_application(self) -> str:
        return self._product_papp.text()

    @product_primary_application.setter
    def product_primary_application(self, primary_parent: Product) -> None:
        try:
            self._product_papp.setText(primary_parent.deno)
        except AttributeError:
            logging.debug(f'Не найден децимальный номер первичной применяемости')
            self._product_papp.setText('')

    @property
    def document_developer(self) -> str:
        return self._doc_dev.text()

    @document_developer.setter
    def document_developer(self, text: str) -> None:
        self._doc_dev.setText(text)

    @property
    def document_date_update(self) -> str:
        return self._doc_update.text()

    @document_date_update.setter
    def document_date_update(self, text: str) -> None:
        self._doc_update.setText(text)

    @property
    def document_organization(self) -> str | None:
        if self.document_class == 'ТД':
            return self._doc_org.currentText()

    @property
    def document_organization_code(self) -> str | None:
        if self.document_class == 'ТД':
            return self.organization_codes.get(self.document_organization, '')

    @property
    def document_method(self) -> str | None:
        if self.document_class == 'ТД':
            return self._doc_method.currentText()

    @property
    def document_method_code(self) -> str | None:
        if self.document_class == 'ТД':
            return self.method_codes.get(self.document_method, '')

    @property
    def document_department(self) -> str | None:
        if self.document_class == 'ТД':
            return self._doc_dep.currentText()

    @property
    def document_department_code(self) -> str | None:
        if self.document_class == 'ТД':
            return self.department_codes.get(self.document_department, '')

    @property
    def document_lit(self) -> str:
        return self._doc_lit.currentText()

    @property
    def document_stage(self) -> str:
        text = self._doc_stage.currentText()
        if text == 'Доступен для регистрации':
            text = 'Зарегистрирован'
        return text

    @document_stage.setter
    def document_stage(self, text: str) -> None:
        self._doc_stage.setCurrentText(text)

    @property
    def document_pages(self) -> str:
        return self._doc_pages.currentText()

    @property
    def document_complex(self) -> list:
        return self._complex_list

    @document_complex.setter
    def document_complex(self, _complex_list: list) -> None:
        self._complex_list = _complex_list
        text = f'{len(_complex_list)} изготавливается совместно в {self.document_deno}'
        self._doc_complex.setText(text)


# Рамка для изделий входящих в спецификацию
class NewDocumentSpecProducts(FrameWithTable):

    def __init__(self, frame_name) -> None:
        super().__init__(frame_name=frame_name,
                         frame_type='NewDocumentBasic')
        self.addNewRow()

    def initTableSettings(self) -> None:
        # Определен в наследниках
        pass

    def showContextMenu(self, point: QPoint) -> None:
        self.context_menu = ContextMenuForSpecProductsTable(self)
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    def comboboxType(self) -> QComboBox:
        cb = QComboBox()
        cb.addItems([product_type.type_name for product_type in ProductType.getAllTypes()])
        cb.setCurrentText(CONFIG.data['product_settings']['default_type'])
        return cb

    def comboboxUnit(self) -> QComboBox:
        cb = QComboBox()
        cb.addItems(CONFIG.data['product_settings']['units'].replace(' ', '').split(','))
        return cb

    def comboboxCode(self) -> QComboBox:
        cb = QComboBox()
        cb.addItems(CONFIG.data['product_settings']['organization_codes'].replace(' ', '').split(','))
        cb.setCurrentText('АЦИЕ')
        cb.setEditable(True)
        return cb

    def addNewRow(self, row: int = 0) -> None:
        row = self.addRow(row)
        self.table.setCellWidget(row, 0, self.comboboxCode())
        self.table.setCellWidget(row, 6, self.comboboxUnit())
        self.table.setCellWidget(row, 7, self.comboboxType())
        self.table.setItem(row, 1, QTableWidgetItem())
        self.table.setItem(row, 2, QTableWidgetItem())
        self.table.setItem(row, 3, QTableWidgetItem())
        self.table.setItem(row, 4, QTableWidgetItem())
        self.table.setItem(row, 5, QTableWidgetItem())

    def addRow(self, row):
        if row == 0:
            self.table.setRowCount(self.table.rowCount() + 1)
            row = self.table.rowCount() - 1
        else:
            self.table.insertRow(row)
        return row

    def copyRow(self):
        row = self.table.currentRow()+1
        self.addNewRow(row)
        for col in range(self.table.columnCount()):
            try:
                self.table.item(row, col).setText(self.table.item(row-1, col).text())
            except AttributeError:
                self.table.cellWidget(row, col).setCurrentText(self.table.cellWidget(row-1, col).currentText())

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        # Определен в наследниках
        pass

    def getData(self) -> list[dict[str, str | int]]:
        # Определяется в наследниках
        pass


# Рамка для изделий входящих в спецификацию
class NewDocumentSpecProductsWithDeno(NewDocumentSpecProducts):

    def __init__(self) -> None:
        super().__init__(frame_name='Изделия с ДН')

    def initTableSettings(self) -> None:
        self.header_settings = ({'col': 0, 'width': 90, 'name': 'Код'},
                                {'col': 1, 'width': 60, 'name': 'Класс'},
                                {'col': 2, 'width': 60, 'name': 'Номер'},
                                {'col': 3, 'width': 30, 'name': 'Исп.'},
                                {'col': 4, 'width': 180, 'name': 'Наименование'},
                                {'col': 5, 'width': 60, 'name': 'Кол-во'},
                                {'col': 6, 'width': 60, 'name': 'Ед.\nизм.'},
                                {'col': 7, 'width': 90, 'name': 'Тип'})
        self.start_rows = 0
        self.start_cols = 8

    def addNewRow(self, row: int = 0) -> None:
        row = self.addRow(row)
        self.table.setCellWidget(row, 0, self.comboboxCode())
        self.table.setCellWidget(row, 6, self.comboboxUnit())
        self.table.setCellWidget(row, 7, self.comboboxType())
        self.table.setItem(row, 1, QTableWidgetItem())
        self.table.setItem(row, 2, QTableWidgetItem())
        self.table.setItem(row, 3, QTableWidgetItem())
        self.table.setItem(row, 4, QTableWidgetItem())
        self.table.setItem(row, 5, QTableWidgetItem())

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        for row_data in default_values:
            row = self.table.rowCount() - 1
            if row_data['Код'] is not None:
                for setting in self.header_settings:
                    text = str(row_data[setting['name']])
                    if setting['name'] in ('Тип', 'Код', 'Ед.\nизм.'):
                        self.table.cellWidget(row, setting['col']).setCurrentText(text)
                    else:
                        self.table.item(row, setting['col']).setText(text)
                self.addNewRow()

    def getData(self) -> list[dict[str, str | int]]:
        children_data = []
        for row in range(self.table.rowCount()):
            child_data = {}
            for col in range(self.table.columnCount()):
                column_name = self.table.horizontalHeaderItem(col).text()
                try:
                    child_data[column_name] = self.table.item(row, col).text()
                except AttributeError:
                    child_data[column_name] = self.table.cellWidget(row, col).currentText()
            deno = join_deno(code_org=child_data['Код'],
                             code_class=child_data['Класс'],
                             num=child_data['Номер'],
                             ver=child_data['Исп.'])
            child_data['Обозначение'] = deno
            if deno:
                children_data.append(child_data)
        return children_data


# Рамка для изделий без децимального номера, входящих в спецификацию
class NewDocumentSpecProductsNoDeno(NewDocumentSpecProducts):

    def __init__(self) -> None:
        super().__init__(frame_name='Изделия без ДН')

    def initTableSettings(self) -> None:
        self.header_settings = ({'col': 0, 'width': 450, 'name': 'Наименование'},
                                {'col': 1, 'width': 60, 'name': 'Кол-во'},
                                {'col': 2, 'width': 60, 'name': 'Ед.\nизм.'},
                                {'col': 3, 'width': 90, 'name': 'Тип'})
        self.start_rows = 0
        self.start_cols = 4

    def addNewRow(self, row: int = 0) -> None:
        row = self.addRow(row)
        self.table.setCellWidget(row, 2, self.comboboxUnit())
        self.table.setCellWidget(row, 3, self.comboboxType())
        self.table.setItem(row, 0, QTableWidgetItem())
        self.table.setItem(row, 1, QTableWidgetItem())

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        for row_data in default_values:
            row = self.table.rowCount() - 1
            if row_data['Код'] is None:
                for setting in self.header_settings:
                    text = str(row_data[setting['name']])
                    if setting['name'] in ('Тип', 'Код', 'Ед.\nизм.'):
                        self.table.cellWidget(row, setting['col']).setCurrentText(text)
                    else:
                        self.table.item(row, setting['col']).setText(text)
                self.addNewRow()

    def getData(self) -> list[dict[str, str | int]]:
        children_data = []
        for row in range(self.table.rowCount()):
            child_data = {}
            for col in range(self.table.columnCount()):
                column_name = self.table.horizontalHeaderItem(col).text()
                try:
                    child_data[column_name] = self.table.item(row, col).text()
                except AttributeError:
                    child_data[column_name] = self.table.cellWidget(row, col).currentText()
            child_data['Обозначение'] = child_data['Наименование']
            if child_data['Наименование']:
                children_data.append(child_data)
        return children_data


# Рамка для документов входящих в спецификацию
class NewDocumentDocumentTypes(FrameWithTable):

    def __init__(self) -> None:
        super().__init__(frame_name='Документы',
                         frame_type='NewDocumentBasic')
        self.addNewRow()

    def initTableSettings(self) -> None:
        self.header_settings = ({'col': 0, 'width': 100, 'name': 'Код'},
                                {'col': 1, 'width': 200, 'name': 'Вид'})
        self.start_rows = 0
        self.start_cols = 2
        self.db_types = DocumentType.getAllTypes()
        self.cb_items = sorted(list(set([db_type.sign for db_type in self.db_types])))

    def combobox(self) -> QComboBox:
        cb = QComboBox()
        cb.addItems(self.cb_items)
        cb.setCurrentText('')
        cb.setEditable(True)
        cb.currentTextChanged.connect(self.documentChangedEvent)
        return cb

    def documentChangedEvent(self) -> None:
        row = self.table.currentRow()
        sign = self.sender().currentText()
        self.addDocumentSubTypeName(sign, row)
        self.cellChanged()

    def addDocumentSubTypeName(self, sign: str, row: int) -> None:
        for db_type in self.db_types:
            if db_type.sign == sign:
                subtype_name = db_type.subtype_name
                self.table.item(row, 1).setText(subtype_name)

    def addNewRow(self) -> None:
        self.table.setRowCount(self.table.rowCount() + 1)
        self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem())
        self.table.setCellWidget(self.table.rowCount() - 1, 0, self.combobox())

    def getData(self) -> list[str]:
        subtype_names = []
        for row in range(self.table.rowCount()):
            subtype_name = self.table.item(row, 1).text()
            if subtype_name:
                subtype_names.append(subtype_name)
        return subtype_names


# Рамка для отображения изделий в составе
class FrameComplexDocument(FrameWithTable):

    def __init__(self) -> None:
        super().__init__(frame_name='Изготавливается\nсовместно',
                         frame_type='NewDocumentBasic')
        self.table.itemChanged.connect(self.checkProduct)
        self.icon_ok = CONFIG.style.done_mini
        self.icon_cross = CONFIG.style.close
        self.addNewRow()

    def initTableSettings(self) -> None:
        self.header_settings = ({'col': 0, 'width': 30, 'name': ' '},
                                {'col': 1, 'width': 200, 'name': 'Обозначение'},
                                {'col': 2, 'width': 300, 'name': 'Наименование'})
        self.start_rows = 0
        self.start_cols = 3

    def addNewRow(self) -> None:
        self.table.blockSignals(True)
        self.table.setRowCount(self.table.rowCount() + 1)
        self.table.setItem(self.table.rowCount() - 1, 0, QTableWidgetItem())
        self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem())
        self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem())
        self.table.blockSignals(False)

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        for row_data in default_values:
            row = self.table.rowCount() - 1
            self.table.item(row, 0).setIcon(self.icon_ok)
            self.table.item(row, 1).setText(row_data['Обозначение'])
            self.table.item(row, 2).setText(row_data['Наименование'])
            self.addNewRow()

    def cleanValues(self):
        for row in range(self.table.rowCount() - 1, -1, -1):
            self.table.removeRow(row)
        self.addNewRow()

    def checkProduct(self):
        if self.table.currentRow() != -1 and self.table.currentColumn() not in [0, 2]:
            deno = self.table.currentItem().text()
            builder = ProductBuilder()
            builder.getDbProductByDenotation(deno=deno)
            product = builder.product
            if product.db_product is not None:
                self.table.item(self.table.currentRow(), 0).setIcon(self.icon_ok)
                self.table.item(self.table.currentRow(), 2).setText(product.name)
            else:
                self.table.item(self.table.currentRow(), 0).setIcon(self.icon_cross)

    def getData(self) -> list[dict[str, str | int]]:
        children_data = []
        for row in range(self.table.rowCount()):
            child_data = {}
            for col in range(self.table.columnCount()):
                column_name = self.table.horizontalHeaderItem(col).text()
                try:
                    child_data[column_name] = self.table.item(row, col).text()
                except AttributeError:
                    child_data[column_name] = self.table.cellWidget(row, col).currentText()
            if child_data['Обозначение']:
                children_data.append(child_data)
        return children_data
