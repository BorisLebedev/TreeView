""" Модуль с рамками, которые использует окно ввода нового документа """

from __future__ import annotations
from typing import TYPE_CHECKING

import logging
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QPoint
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QMessageBox
from PyQt5.Qt import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QTableWidgetItem
from STC.gui.splash_screen import show_dialog
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

if TYPE_CHECKING:
    from STC.product.product import Product


class NewDocumentMainFrame(FrameBasic):
    """ Рамка для основных реквизитов документа """

    # pylint: disable = too-many-instance-attributes
    # pylint: disable = too-many-public-methods

    findDocument = pyqtSignal()
    changeDocument = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(frame_name='Основные данные')
        self._department_codes = {}
        self._organization_codes = {}
        self._method_codes = {}
        self._stage_letters = []
        self._complex_list = []
        self._db_types = DocumentType.documentTypes()
        self.default_stage = 'Доступен для регистрации'
        self._stages = \
            [db_stage.stage for db_stage in DocumentStage.getAllStages()] + [self.default_stage]
        self.d_type = None
        self._sep = ': '
        self._def_kd_type = return_document_type(class_name='КД',
                                                 subtype_name='Спецификация')
        self._def_td_type = return_document_type(class_name='ТД',
                                                 subtype_name='Маршрутная карта')
        self.initWidgetLabel()
        self.initWidgetLineEdit()
        self.initWidgetCombobox()
        visibility_settings_td = {'КД': False,
                                  'ТД': True,
                                  'PLM': False}
        self.visibility = {self._l_doc_org: visibility_settings_td,
                           self._l_doc_method: visibility_settings_td,
                           self._l_doc_dep: visibility_settings_td,
                           self._doc_org: visibility_settings_td,
                           self._doc_method: visibility_settings_td,
                           self._doc_dep: visibility_settings_td,
                           self._l_doc_complex: visibility_settings_td,
                           self._doc_complex: visibility_settings_td}
        self.initWidgetComboboxDefault()
        self.initWidgetComboboxConnection()

        self.modifyComboboxValues(attr='class')
        self.initWidgetPosition()

    def initWidgetLabel(self) -> None:
        """ Инициализация QLabel """

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
        self._l_doc_dev = QLabel('ФИО разработчика')  # КД
        self._l_doc_update = QLabel('Дата изменения')  # КД

        self._l_doc_pages = QLabel('Количество листов')
        self._l_doc_lit = QLabel('Литера')
        self._l_doc_stage = QLabel('Этап разработки')  # ТД
        self._l_doc_complex = QLabel('Изготавливается совместно с')  # ТД

    def initWidgetLineEdit(self) -> None:
        """ Инициализация QLineEdit """

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
        """ Инициализация QComboBox """

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

    def initWidgetPosition(self) -> None:
        """ Расположение виджетов в рамке """

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
               self._l_doc_complex: self._doc_complex,
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
        """ Данные для комбобоксов  """

        self._doc_org.addItems(self.organization_codes.keys())
        self._doc_method.addItems(self.method_codes.keys())
        self._doc_dep.addItems(self.department_codes.keys())
        self._doc_lit.addItems(self.stage_letters)
        self._doc_stage.addItems(self._stages)
        self._doc_pages.addItems([str(num) for num in range(100)])

    def initWidgetComboboxConnection(self) -> None:
        """ Реакции на изменения значения комбобоксов
            выбора типа документа """

        self._doc_class.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='subclass'))
        self._doc_subclass.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='type'))
        self._doc_type.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='subtype'))
        self._doc_subtype.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='document'))
        self._doc_org.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='document'))
        self._doc_method.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='document'))
        self._doc_dep.currentIndexChanged.connect(
            lambda: self.modifyComboboxValues(attr='document'))

    def widgetVisibility(self) -> None:
        """ Определяет видимость виджета в форме ввода
            в зависимости от типа документа """

        try:
            for widget, settings in self.visibility.items():
                widget.setVisible(settings[self.document_class])
        except KeyError:
            logging.debug('Не найден случай для класса документации')

    def setComboboxValues(self, attr: str) -> list[str]:
        """ Изменяет варианты значений в комбобоксах
            в зависимости от типа комбобокса и
            выбранных значений в других комбобоксах"""

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
        """ Устанавливает значения по умолчанию в комбобоксах
            после изменения комбобоксов выбора типа документа """

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
        """ Изменяет комбобоксы в зависимости от
            значения изменяющегося комбобоксы """

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
        """ Поиск типа документа по значениям,
            указанным в комбобоксах выбора типа документа"""

        self.d_type = return_document_type(
            class_name=self.document_class,
            subtype_name=self.document_subtype,
            method_code=self.document_method_code,
            organization_code=self.document_organization_code)
        self.widgetVisibility()
        self.findDocument.emit()

    def mergeSignAndSubtype(self, db_type: DocumentType) -> str:
        """ Возвращает строку из сокращения и подтипа документа,
            для использования в вариантах выбора для комбобоксов
            выбора типа документа """

        sign = f'{db_type.sign}{self._sep}' if db_type.sign else ''
        return f'{sign}{db_type.subtype_name}'

    @property
    def department_codes(self) -> dict[str, str]:
        """ Возвращает словарь кодов отделов и их наименований """

        if not self._department_codes:
            for department_name, code in CONFIG.data['document_department'].items():
                self._department_codes[department_name] = code
        return self._department_codes

    @property
    def organization_codes(self) -> dict[str, str]:
        """ Возвращает словарь типа технологического
            процесса по организации и кода ему соответствующего """

        if not self._organization_codes:
            for organization_type, code in CONFIG.data['document_organization'].items():
                self._organization_codes[organization_type] = code
        return self._organization_codes

    @property
    def method_codes(self) -> dict[str, str]:
        """ Возвращает словарь наименований методов изготовления и
            кода децимального номера, который ему соответствует """

        if not self._method_codes:
            for method_name, code in CONFIG.data['document_method'].items():
                self._method_codes[method_name] = code
        return self._method_codes

    @property
    def stage_letters(self):
        """ Возвращает возможные значения литеры документа """

        if not self._stage_letters:
            return CONFIG.data['document_settings']['litera'].replace(' ', '').split(',')
        return self._stage_letters

    @property
    def document_class(self) -> str:
        """ Возвращает класс типа документа """

        return self._doc_class.currentText()

    @document_class.setter
    def document_class(self, value: str) -> None:
        """ Устанавливает класс типа документа """

        self._doc_class.setCurrentText(value)
        self.modifyComboboxValues(attr='subclass')

    @property
    def document_subclass(self) -> str:
        """ Возвращает подкласс типа документа """

        return self._doc_subclass.currentText()

    @document_subclass.setter
    def document_subclass(self, value: str) -> None:
        """ Устанавливает подкласс типа документа """

        self._doc_subclass.setCurrentText(value)
        self.modifyComboboxValues(attr='type')

    @property
    def document_type(self) -> str:
        """ Возвращает тип типа документа """

        return self._doc_type.currentText()

    @property
    def document_subtype(self) -> str:
        """ Возвращает подтип типа документа """

        text = self._doc_subtype.currentText()
        if text.find(self._sep) != -1:
            index = text.find(self._sep) + len(self._sep)
            text = text[index:]
        return text

    @property
    def product_name(self) -> str:
        """ Наименование изделия """

        return self._product_name.text()

    @product_name.setter
    def product_name(self, text: str) -> None:
        """ Наименование изделия """
        self._product_name.setText(text)

    @property
    def product_deno(self) -> str:
        """ Децимальный номер изделия """

        return self._product_deno.text()

    @product_deno.setter
    def product_deno(self, text: str) -> None:
        """ Децимальный номер изделия """

        self._product_deno.setText(text)

    @property
    def document_name(self) -> str:
        """ Наименование документа """

        return self._doc_name.text()

    @document_name.setter
    def document_name(self, text: str) -> None:
        """ Наименование документа """

        self._doc_name.setText(text)

    @property
    def document_deno(self) -> str:
        """ Децимальный номер документа """

        if self._doc_deno.currentText() == '':
            return self.product_deno
        return self._doc_deno.currentText()

    @document_deno.setter
    def document_deno(self, text: str) -> None:
        """ Децимальный номер документа """

        self._doc_deno.clear()
        self._doc_deno.addItems(text)

    @property
    def product_primary_application(self) -> str:
        """ Первичная применяемость изделия """

        return self._product_papp.text()

    @product_primary_application.setter
    def product_primary_application(self, primary_parent: Product) -> None:
        """ Первичная применяемость изделия """

        try:
            self._product_papp.setText(primary_parent.deno)
        except AttributeError:
            logging.debug('Не найден децимальный номер первичной применяемости')
            self._product_papp.setText('')

    @property
    def document_developer(self) -> str:
        """ Разработчик документа """

        return self._doc_dev.text()

    @document_developer.setter
    def document_developer(self, text: str) -> None:
        """ Разработчик документа """

        self._doc_dev.setText(text)

    @property
    def document_date_update(self) -> str:
        """ Дата изменения документа """

        return self._doc_update.text()

    @document_date_update.setter
    def document_date_update(self, text: str) -> None:
        """ Дата изменения документа """

        self._doc_update.setText(text)

    @property
    def document_organization(self) -> str | None:
        """ Тип документа по организации """

        if self.document_class == 'ТД':
            return self._doc_org.currentText()
        return None

    @property
    def document_organization_code(self) -> str | None:
        """ Код документа по организации """

        if self.document_class == 'ТД':
            return self.organization_codes.get(self.document_organization, '')
        return None

    @property
    def document_method(self) -> str | None:
        """ Наименование метода изготовления """

        if self.document_class == 'ТД':
            return self._doc_method.currentText()
        return None

    @property
    def document_method_code(self) -> str | None:
        """ Код метода изготовления """

        if self.document_class == 'ТД':
            return self.method_codes.get(self.document_method, '')
        return None

    @property
    def document_department(self) -> str | None:
        """ Наименование отдела """

        if self.document_class == 'ТД':
            return self._doc_dep.currentText()
        return None

    @property
    def document_department_code(self) -> str | None:
        """ Код наименования отдела """

        if self.document_class == 'ТД':
            return self.department_codes.get(self.document_department, '')
        return None

    @property
    def document_lit(self) -> str:
        """ Литера документа """

        return self._doc_lit.currentText()

    @property
    def document_stage(self) -> str:
        """ Этап разработки документа """

        text = self._doc_stage.currentText()
        if text == 'Доступен для регистрации':
            text = 'Зарегистрирован'
        return text

    @document_stage.setter
    def document_stage(self, text: str) -> None:
        """ Этап разработки документа """

        self._doc_stage.setCurrentText(text)

    @property
    def document_pages(self) -> str:
        """ Количество страниц документа """

        return self._doc_pages.currentText()

    @property
    def document_complex(self) -> list:
        """ Список изделий входящих в составные документы """

        return self._complex_list

    @document_complex.setter
    def document_complex(self, _complex_list: list) -> None:
        """ Список изделий входящих в составные документы """

        self._complex_list = _complex_list
        text = f'{len(_complex_list)} изготавливается совместно в {self.document_deno}'
        self._doc_complex.setText(text)


class NewDocumentSpecProducts(FrameWithTable):
    """ Родительский класс для изделий входящих в спецификацию """

    def __init__(self, frame_name) -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)
        self.addNewRow()

    def initTableSettings(self) -> None:
        """ Параметры таблицы """

    def showContextMenu(self, point: QPoint) -> None:
        """ Вызов контекстного меню """
        # pylint: disable = attribute-defined-outside-init
        # self.context_menu определено в super().init()

        self.context_menu = ContextMenuForSpecProductsTable(self)
        qpoint = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qpoint)

    @staticmethod
    def comboboxType() -> QComboBox:
        """ Комбобокс с типами изделий по спецификации """

        combobox = QComboBox()
        combobox.addItems([product_type.type_name for product_type in ProductType.getAllTypes()])
        combobox.setCurrentText(CONFIG.data['product_settings']['default_type'])
        return combobox

    @staticmethod
    def comboboxUnit() -> QComboBox:
        """ Комбобокс с видами единиц измерения """

        combobox = QComboBox()
        combobox.addItems(CONFIG.data['product_settings']['units'].replace(' ', '').split(','))
        return combobox

    @staticmethod
    def comboboxCode() -> QComboBox:
        """ Комбобокс с кодами децимальных номеров различных производителей """

        combobox = QComboBox()
        combobox.addItems(
            CONFIG.data['product_settings']['organization_codes'].replace(' ', '').split(','))
        combobox.setCurrentText('АЦИЕ')
        combobox.setEditable(True)
        return combobox

    @staticmethod
    def itemChanged(item):
        if isinstance(item, QTableWidgetItem):
            text = item.text()[0].upper() + item.text()[1:] if item.text() else item.text()
            item.setText(text)

    def addNewRow(self, row: int = 0) -> None:
        """ Добавление новой строки таблицы"""

        self.table.blockSignals(True)
        row = self.addRow(row)
        self.table.setCellWidget(row, 0, self.comboboxCode())
        self.table.setCellWidget(row, 6, self.comboboxUnit())
        self.table.setCellWidget(row, 7, self.comboboxType())
        self.table.setItem(row, 1, QTableWidgetItem())
        self.table.setItem(row, 2, QTableWidgetItem())
        self.table.setItem(row, 3, QTableWidgetItem())
        self.table.setItem(row, 4, QTableWidgetItem())
        self.table.setItem(row, 5, QTableWidgetItem())
        self.table.blockSignals(False)

    def addRow(self, row):
        """ Добавление нового ряда таблицы
            в зависимости от текущего ряда """

        if row == 0:
            self.table.setRowCount(self.table.rowCount() + 1)
            row = self.table.rowCount() - 1
        else:
            self.table.insertRow(row)
        return row

    def copyRow(self):
        """ Копирование строки таблицы """

        row = self.table.currentRow()+1
        self.addNewRow(row)
        for col in range(self.table.columnCount()):
            try:
                self.table.item(row, col).setText(self.table.item(row-1, col).text())
            except AttributeError:
                self.table.cellWidget(row, col).\
                    setCurrentText(self.table.cellWidget(row-1, col).currentText())

    def markRows(self) -> None:
        """ Выделить цветом несколько строк таблицы """

        items = self.table.selectedItems()
        for item in items:
            item.setData(Qt.BackgroundColorRole, QColor(0, 200, 0, 200))

    def markRowsDel(self) -> None:
        """ Выделить цветом несколько строк таблицы """

        items = self.table.selectedItems()
        for item in items:
            item.setData(Qt.BackgroundColorRole, QColor(0, 0, 0, 0))

    def deleteRows(self) -> None:
        msg_box = show_dialog(text=f'Удалить выделенные строки',
                              m_type='continue_project')
        if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.Yes:
            items = self.table.selectedItems()
            for item in items:
                row = item.row()
                self.table.setCurrentCell(row, 1)
                self.deleteRow()
        if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.No:
            pass

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        """ Внесение значений по умолчанию """

    def getData(self) -> list[dict[str, str | int]]:
        """ Получить данные """


class NewDocumentSpecProductsWithDeno(NewDocumentSpecProducts):
    """ Рамка для изделий входящих в спецификацию """

    def __init__(self) -> None:
        super().__init__(frame_name='Изделия с ДН')

    def initTableSettings(self) -> None:
        """ Параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 90, 'name': 'Код'},
                                {'col': 1, 'width': 60, 'name': 'Класс'},
                                {'col': 2, 'width': 60, 'name': 'Номер'},
                                {'col': 3, 'width': 30, 'name': 'Исп.'},
                                {'col': 4, 'width': 180, 'name': 'Наименование'},
                                {'col': 5, 'width': 60, 'name': 'Кол-во'},
                                {'col': 6, 'width': 60, 'name': 'Ед.\nизм.'},
                                {'col': 7, 'width': 90, 'name': 'Тип'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self, row: int = 0) -> None:
        """ Добавление новой строки таблицы """

        self.table.blockSignals(True)
        row = self.addRow(row)
        self.table.setCellWidget(row, 0, self.comboboxCode())
        self.table.setCellWidget(row, 6, self.comboboxUnit())
        self.table.setCellWidget(row, 7, self.comboboxType())
        self.table.setItem(row, 1, TableWidgetItem())
        self.table.setItem(row, 2, TableWidgetItem())
        self.table.setItem(row, 3, TableWidgetItem())
        self.table.setItem(row, 4, TableWidgetItem())
        self.table.setItem(row, 5, TableWidgetItem())
        self.table.blockSignals(False)

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        """ Внесение значений по умолчанию """

        for row_data in default_values:
            row = self.table.rowCount() - 1
            if row_data['Код'] is not None:
                for setting in self.header_settings:
                    text = str(row_data[setting['name']])
                    self.table.blockSignals(True)
                    if setting['name'] in ('Тип', 'Код', 'Ед.\nизм.'):
                        self.table.cellWidget(row, setting['col']).setCurrentText(text)
                    else:
                        self.table.item(row, setting['col']).setText(text)
                    self.table.blockSignals(False)
                self.addNewRow()

    def getData(self) -> list[dict[str, str | int]]:
        """ Получить данные """

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


class NewDocumentSpecProductsNoDeno(NewDocumentSpecProducts):
    """ Рамка для изделий без децимального номера, входящих в спецификацию """

    def __init__(self) -> None:
        super().__init__(frame_name='Изделия без ДН')

    def initTableSettings(self) -> None:
        """ Параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 450, 'name': 'Наименование'},
                                {'col': 1, 'width': 60, 'name': 'Кол-во'},
                                {'col': 2, 'width': 60, 'name': 'Ед.\nизм.'},
                                {'col': 3, 'width': 90, 'name': 'Тип'})
        self.start_rows = 0
        self.start_cols = 4

    def addNewRow(self, row: int = 0) -> None:
        """ Добавление новой строки таблицы """

        row = self.addRow(row)
        self.table.setCellWidget(row, 2, self.comboboxUnit())
        self.table.setCellWidget(row, 3, self.comboboxType())
        self.table.setItem(row, 0, QTableWidgetItem())
        self.table.setItem(row, 1, QTableWidgetItem())

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        """ Внесение значений по умолчанию """

        for row_data in default_values:
            row = self.table.rowCount() - 1
            if row_data['Код'] is None:
                for setting in self.header_settings:
                    text = str(row_data[setting['name']])
                    self.table.blockSignals(True)
                    if setting['name'] in ('Тип', 'Код', 'Ед.\nизм.'):
                        self.table.cellWidget(row, setting['col']).setCurrentText(text)
                    else:
                        self.table.item(row, setting['col']).setText(text)
                    self.table.blockSignals(False)
                self.addNewRow()

    def getData(self) -> list[dict[str, str | int]]:
        """ Получить данные """

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


class NewDocumentDocumentTypes(FrameWithTable):
    """ Рамка для документов входящих в спецификацию """

    def __init__(self) -> None:
        self.db_types = []
        self.cb_items = []
        super().__init__(frame_name='Документы')
        self.addNewRow()

    def initTableSettings(self) -> None:
        """ Параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 100, 'name': 'Код'},
                                {'col': 1, 'width': 200, 'name': 'Вид'})
        self.start_rows = 0
        self.start_cols = 2
        self.db_types = DocumentType.getAllTypes()
        self.cb_items = sorted(list(set(db_type.sign for db_type in self.db_types)))

    def combobox(self) -> QComboBox:
        """ Комбобокс с кодами видов документов """

        combobox = QComboBox()
        combobox.addItems(self.cb_items)
        combobox.setCurrentText('')
        combobox.setEditable(True)
        combobox.currentTextChanged.connect(self.documentChangedEvent)
        return combobox

    def documentChangedEvent(self) -> None:
        """ Реакция на изменение значения комбобокса
            с кодами видов документов """

        row = self.table.currentRow()
        sign = self.sender().currentText()
        self.addDocumentSubTypeName(sign, row)
        self.cellChanged()

    def addDocumentSubTypeName(self, sign: str, row: int) -> None:
        """ Вносит наименование вида документа
            в зависимости от кода вида документа """

        for db_type in self.db_types:
            if db_type.sign == sign:
                subtype_name = db_type.subtype_name
                self.table.item(row, 1).setText(subtype_name)

    def addNewRow(self) -> None:
        """ Добавление новой строки таблицы """

        self.table.setRowCount(self.table.rowCount() + 1)
        self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem())
        self.table.setCellWidget(self.table.rowCount() - 1, 0, self.combobox())

    def getData(self) -> list[str]:
        """ Получить данные """

        subtype_names = []
        for row in range(self.table.rowCount()):
            subtype_name = self.table.item(row, 1).text()
            if subtype_name:
                subtype_names.append(subtype_name)
        return subtype_names


class FrameComplexDocument(FrameWithTable):
    """ Рамка для отображения изделий в составе """

    def __init__(self) -> None:
        super().__init__(frame_name='Изготавливается\nсовместно')
        self.table.itemChanged.connect(self.checkProduct)
        self.icon_ok = CONFIG.style.done_mini
        self.found = 'Найдено'
        self.not_found = 'Не найдено'
        self.icon_cross = CONFIG.style.close
        self.addNewRow()

    def initTableSettings(self) -> None:
        """ Параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 120, 'name': 'Найдено'},
                                {'col': 1, 'width': 200, 'name': 'Обозначение'},
                                {'col': 2, 'width': 300, 'name': 'Наименование'})
        self.start_rows = 0
        self.start_cols = 3

    def addNewRow(self) -> None:
        """ Добавление новой строки таблицы """

        self.table.blockSignals(True)
        self.table.setRowCount(self.table.rowCount() + 1)
        self.table.setItem(self.table.rowCount() - 1, 0, QTableWidgetItem())
        self.table.setItem(self.table.rowCount() - 1, 1, QTableWidgetItem())
        self.table.setItem(self.table.rowCount() - 1, 2, QTableWidgetItem())
        self.table.blockSignals(False)

    def defaultValues(self, default_values: list[dict[str, str | int]]) -> None:
        """ Внесение текущих значений таблицы изделий составного документа"""

        for row_data in default_values:
            row = self.table.rowCount() - 1
            self.table.item(row, 0).setIcon(self.icon_ok)
            self.table.item(row, 0).setText(self.found)
            self.table.item(row, 1).setText(row_data['Обозначение'])
            self.table.item(row, 2).setText(row_data['Наименование'])
            self.addNewRow()

    def cleanValues(self):
        """ Очистка значений таблицы """

        for row in range(self.table.rowCount() - 1, -1, -1):
            self.table.removeRow(row)
        self.addNewRow()

    def checkProduct(self):
        """ Проверка наличия изделия с таким децимальным номером """

        if self.table.currentRow() != -1 and self.table.currentColumn() not in [0, 2]:
            deno = self.table.currentItem().text()
            builder = ProductBuilder()
            builder.getDbProductByDenotation(deno=deno)
            product = builder.product
            if product.db_product is not None:
                self.table.item(self.table.currentRow(), 0).setIcon(self.icon_ok)
                self.table.item(self.table.currentRow(), 0).setText(self.found)
                self.table.item(self.table.currentRow(), 2).setText(product.name)
            else:
                self.table.item(self.table.currentRow(), 0).setText(self.not_found)
                self.table.item(self.table.currentRow(), 0).setIcon(self.icon_cross)

    def getData(self) -> list[dict[str, str | int]]:
        """ Получить данные """

        children_data = []
        for row in range(self.table.rowCount()):
            child_data = {}
            if self.table.item(row, 0).text() == self.found:
                child_data['Обозначение'] = self.table.item(row, 1).text()
                child_data['Наименование'] = self.table.item(row, 2).text()
                children_data.append(child_data)
            # for col in range(self.table.columnCount()):
            #     column_name = self.table.horizontalHeaderItem(col).text()
            #     try:
            #         child_data[column_name] = self.table.item(row, col).text()
            #     except AttributeError:
            #         child_data[column_name] = self.table.cellWidget(row, col).currentText()
            # if child_data['Обозначение']:
            #     children_data.append(child_data)
        return children_data


class TableWidgetItem(QTableWidgetItem):
    """ QTableWidgetItem с текстом с заглавной буквы """

    def setText(self, atext: str):
        if atext:
            atext = atext[0].upper() + atext[1:]
        super().setText(atext)

