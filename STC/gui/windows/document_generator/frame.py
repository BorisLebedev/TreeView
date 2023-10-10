"""  """

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt5.QtCore import QPoint
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QAbstractItemView
from PyQt5.QtWidgets import QAbstractScrollArea
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from STC.config.config import CONFIG
from STC.functions.func import text_slicer
from STC.gui.windows.ancestors.frame import FrameBasic
from STC.gui.windows.ancestors.frame import FrameWithTable

from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceTable
from STC.gui.windows.document_generator.plaintext import DocText
from STC.gui.windows.document_generator.plaintext import EquipmentText
from STC.gui.windows.document_generator.plaintext import IotText
from STC.gui.windows.document_generator.plaintext import MatText
from STC.gui.windows.document_generator.plaintext import RigText
from STC.gui.windows.document_generator.plaintext import SentenceTextEdit
from STC.gui.windows.document_generator.sentence_frame import SentenceDoc
from STC.gui.windows.document_generator.sentence_frame import SentenceEquipment
from STC.gui.windows.document_generator.sentence_frame import SentenceIot
from STC.gui.windows.document_generator.sentence_frame import SentenceMat
from STC.gui.windows.document_generator.sentence_frame import SentenceRig
from STC.gui.splash_screen import show_dialog
from STC.product.product import OperationBuilder
from STC.product.product import Operation

if TYPE_CHECKING:
    from STC.product.product import Document
    from STC.product.product import Sentence


def inScroll(widget: QWidget) -> QScrollArea:
    """  """

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(widget)
    return scroll


class FrameMkMain(FrameBasic):
    """ Рамка основных данных генерируемой МК """

    changeLitera = pyqtSignal()
    changeStage = pyqtSignal()
    changeDeveloper = pyqtSignal()
    changeChecker = pyqtSignal()
    changeApprover = pyqtSignal()
    changeNContr = pyqtSignal()
    changeMContr = pyqtSignal()
    changeKind = pyqtSignal()

    def __init__(self) -> None:
        super().__init__(frame_name='Основные данные')
        self.stage_letters = sorted(CONFIG.data['document_settings']['litera'].replace(' ', '').split(','))
        self.stages = CONFIG.data['document_settings']['stages'].replace("", "").split(',')
        self.initWidgetLabel()
        self.initWidgetLineedit()
        self.initWidgetCombobox()
        self.initWidgetComboboxDefault()
        self.initWidgetComboboxActions()
        self.initWidgetPosition()

    def initWidgetLabel(self) -> None:
        """ Инициализация всех QLabel """

        self._l_product_name = QLabel('Наименование изделия')
        self._l_product_deno = QLabel('Обозначение изделия')
        self._l_product_kind = QLabel('Вид изделия')
        self._l_doc_name = QLabel('Наименование документа')
        self._l_doc_deno = QLabel('Обозначение документа')
        self._l_doc_litera = QLabel('Литера')
        self._l_doc_developer = QLabel('Разработал')
        self._l_doc_checker = QLabel('Проверил')
        self._l_doc_approver = QLabel('Утвердил')
        self._l_doc_n_contr = QLabel('Нормоконтроль')
        self._l_doc_m_contr = QLabel('Метролог')
        self._l_doc_stage = QLabel('Этап разработки')

    def initWidgetLineedit(self) -> None:
        """ Инициализация всех QLineEdit """

        self._product_name = QLineEdit()
        self._product_deno = QLineEdit()
        self._doc_name = QLineEdit()
        self._doc_deno = QLineEdit()
        self._doc_developer = QLineEdit()
        self._doc_checker = QLineEdit()
        self._doc_approver = QLineEdit()
        self._doc_n_contr = QLineEdit()
        self._product_kind = QLineEdit()
        self._doc_m_contr = QLineEdit()

    def initWidgetCombobox(self) -> None:
        """ Инициализация всех QComboBox """

        self._doc_litera = QComboBox()
        self._doc_stage = QComboBox()

    def initWidgetComboboxDefault(self) -> None:
        """ Начальные данные комбобоксов """

        self._doc_litera.addItems(self.stage_letters)
        self._doc_stage.addItems(self.stages)

    def initWidgetComboboxActions(self) -> None:
        """ Инициализация действий при изменении
            данных редактируемых виджетов """

        self._doc_litera.currentTextChanged.connect(self.changeLitera)
        self._doc_stage.currentTextChanged.connect(self.changeStage)
        self._doc_developer.editingFinished.connect(self.changeDeveloper)
        self._doc_checker.editingFinished.connect(self.changeChecker)
        self._doc_approver.editingFinished.connect(self.changeApprover)
        self._doc_n_contr.editingFinished.connect(self.changeNContr)
        self._doc_m_contr.editingFinished.connect(self.changeMContr)

    def initWidgetPosition(self) -> None:
        """ Расположение виджетов в рамке """

        self.widgets = {
            self._l_product_name: self._product_name,
            self._l_product_deno: self._product_deno,
            self._l_product_kind: self._product_kind,
            self._l_doc_name: self._doc_name,
            self._l_doc_deno: self._doc_deno,
            self._l_doc_litera: self._doc_litera,
            self._l_doc_developer: self._doc_developer,
            self._l_doc_checker: self._doc_checker,
            self._l_doc_approver: self._doc_approver,
            self._l_doc_n_contr: self._doc_n_contr,
            self._l_doc_stage: self._doc_stage,
        }
        row = 0
        for row, label in enumerate(self.widgets.keys()):
            self.layout().addWidget(label, row, 0)
            self.layout().addWidget(self.widgets[label], row, 1)
        self.layout().setRowStretch(row + 1, 1)

    @property
    def product_name(self) -> str:
        """ Возвращает наименование изделия """

        return self._product_name.text()

    @product_name.setter
    def product_name(self, text: str) -> None:
        """ Устанавливает наименование изделия """

        self._product_name.setText(text)

    @property
    def product_deno(self) -> str:
        """ Возвращает децимальный номер изделия """

        return self._product_deno.text()

    @product_deno.setter
    def product_deno(self, text: str) -> None:
        """ Устанавливает децимальный номер изделия """

        self._product_deno.setText(text)

    @property
    def product_kind(self) -> str:
        """ Возвращает вид изделия """

        return self._product_kind.text()

    @product_kind.setter
    def product_kind(self, kind: str) -> None:
        """ Устанавливает вид изделия """

        self._product_kind.setText(kind)

    @property
    def document_name(self) -> str:
        """ Возвращает наименование документа """

        return self._doc_name.text()

    @document_name.setter
    def document_name(self, text: str) -> None:
        """ Устанавливает наименование документа """

        self._doc_name.setText(text)

    @property
    def document_deno(self) -> str:
        """ Возвращает децимальный номер документа """

        return self._doc_deno.text()

    @document_deno.setter
    def document_deno(self, text: str) -> None:
        """ Устанавливает децимальный номер документа """

        self._doc_deno.setText(text)

    @property
    def document_litera(self) -> str:
        """ Возвращает литеру документа """

        return self._doc_litera.currentText()

    @document_litera.setter
    def document_litera(self, value: str) -> None:
        """ Устанавливает литеру документа """

        self._doc_litera.setCurrentText(value)

    @property
    def document_stage(self) -> str:
        """ Возвращает этап разработки документа """

        return self._doc_stage.currentText()

    @document_stage.setter
    def document_stage(self, value: str) -> None:
        """ Устанавливает этап разработки документа """

        self._doc_stage.blockSignals(True)
        if value in self.stages:
            self._doc_stage.setCurrentText(value)
        else:
            self._doc_stage.addItem(value)
            self._doc_stage.setCurrentText(value)
        self._doc_stage.blockSignals(False)

    @property
    def document_developer(self) -> str:
        """ Возвращает разработчика документа """

        return self._doc_developer.text()

    @document_developer.setter
    def document_developer(self, value: str) -> None:
        """ Устанавливает ФИО разработчика документа в рамке """

        self._doc_developer.setText(value)

    @property
    def document_checker(self) -> str:
        """ Возвращает ФИО проверяющего """

        return self._doc_checker.text()

    @document_checker.setter
    def document_checker(self, value: str) -> None:
        """ Устанавливает ФИО проверяющего в рамке """

        self._doc_checker.setText(value)

    @property
    def document_approver(self) -> str:
        """ Возвращает ФИО утверждающего """

        return self._doc_approver.text()

    @document_approver.setter
    def document_approver(self, value: str) -> None:
        """ Устанавливает ФИО утверждающего в рамке """

        self._doc_approver.setText(value)

    @property
    def document_n_contr(self) -> str:
        """ Возвращает ФИО нормоконтролера """

        return self._doc_n_contr.text()

    @document_n_contr.setter
    def document_n_contr(self, value: str) -> None:
        """ Устанавливает ФИО нормоконтролера в рамке"""

        self._doc_n_contr.setText(value)

    @property
    def document_m_contr(self) -> str:
        """ Возвращает ФИО метролога """

        return self._doc_m_contr.text()

    @document_m_contr.setter
    def document_m_contr(self, value: str) -> None:
        """ Устанавливает ФИО метролога в рамке"""

        self._doc_m_contr.setText(value)


class FrameMkOperations(FrameWithTable):
    """ Рамка для отображения операций """

    createNewOperation = pyqtSignal()
    changeOperation = pyqtSignal()
    updateButtons = pyqtSignal()
    deleleOperation = pyqtSignal()

    def __init__(self) -> None:
        logging.debug('Инициализация рамки для отображения операций')
        self._document_main = None
        self.del_operation = None
        self.new_operation = None
        super().__init__(frame_name='Операции')

    def initTableSettings(self) -> None:
        """ Настройки таблицы """

        self.header_settings = ({'col': 0, 'width': 30, 'name': '+'},
                                {'col': 1, 'width': 30, 'name': '-'},
                                {'col': 2, 'width': 70, 'name': 'Номер'},
                                {'col': 3, 'width': 200, 'name': 'Наименование'},
                                {'col': 4, 'width': 200, 'name': 'Участок'},
                                {'col': 5, 'width': 300, 'name': 'Рабочее\nместо'},
                                {'col': 6, 'width': 100, 'name': 'Профессия'})
        self.start_rows = 0
        self.start_cols = len(self.header_settings)
        self.table.verticalHeader().setSectionsMovable(True)
        self.table.verticalHeader().sectionMoved.connect(self.moveOperation)

    def showContextMenu(self, point: QPoint) -> None:
        """ Вызов контекстного меню (контекстное меню
            для данной таблицы отсутствует) """

    def addNewRow(self, row: int = 0) -> None:
        """ Добавление строки """

        debug_msg = f'Вставка ряд {row} в таблицу операций'
        logging.debug(debug_msg)
        self.blockSignals(True)
        self.table.insertRow(row)
        self.table.setCellWidget(row, 0, self.addOperationButton())
        self.table.setCellWidget(row, 1, self.delOperationButton())
        self.table.setCellWidget(row, 2, QPushButton())
        self.table.setCellWidget(row, 3, self.operation(operation=self.document_main.operations[row]))
        self.table.setCellWidget(row, 4, self.area(operation=self.document_main.operations[row]))
        self.table.setCellWidget(row, 5, self.workplace(operation=self.document_main.operations[row]))
        self.table.setCellWidget(row, 6, self.profession(operation=self.document_main.operations[row]))
        self.blockSignals(False)
        self.operationNumsUpdate()

    def addOperationOrder(self, order: int) -> None:
        """ Изменение порядка следования операций """

        logging.debug('Пересчет номеров операций')
        operations = {}
        for row, operation in sorted(self.document_main.operations.items(), key=lambda x: x[0], reverse=True):
            if row >= order:
                row += 1
            operations[row] = operation
            if operation.order >= order:
                debug_msg = f'Операция {operation.num} {operation.name} ' \
                            f'была {operation.order} стала {operation.order + 1}'
                logging.debug(debug_msg)
                # del operation.order
                operation.order += 1
        self.document_main.operations = operations

    def addOperationButton(self) -> QPushButton:
        """ Кнопка добавления операции """

        btn_add_op = QPushButton('+')
        btn_add_op.clicked.connect(self.createNewOperation)
        return btn_add_op

    def addOperationButtonClicked(self, operation: Operation | None = None) -> None:
        """ Создание новой операции и добавление
            нового ряда в таблицу операций """

        self.new_operation = operation
        if not operation:
            logging.debug('Операция не задана, попытка создать новую операцию')
            row = self.table.indexAt(self.sender().pos()).row()
            v_row = self.table.visualRow(row) + 1
            try:
                name = self.table.cellWidget(row, 3).currentText()
            except AttributeError:
                name = CONFIG.data['excel_document']['default_operation']
            debug_msg = f'Наименование новой операции {name} ' \
                        f'порядок новой операции {v_row}'
            logging.debug(debug_msg)
            self.new_operation = self.createOperation(name=name,
                                                      order=v_row)
        debug_msg = f'Добавляется операция {self.new_operation.name} ' \
                    f'{self.new_operation.num} {self.new_operation.order}'
        logging.debug(debug_msg)
        self.document_main.addOperation(operation=self.new_operation)
        self.addNewRow(row=self.new_operation.order)

    def createOperation(self, name: str, order: int) -> Operation:
        """ Создание нового экземпляра класса операции """

        debug_msg = f'Создание операции с названием {name} и на позиции {order}'
        logging.debug(debug_msg)
        self.addOperationOrder(order)
        builder = OperationBuilder()
        builder.createOperation(document=self.document_main,
                                name=name,
                                order=order,
                                new=True)
        operation = builder.operation
        debug_msg = f'Создана операция с названием {operation.num} {operation.name}'
        logging.debug(debug_msg)
        return operation

    def changeArea(self) -> None:
        """ Изменение участка изготовления """

        row = self.table.indexAt(self.sender().pos()).row()
        operation = self.document_main.operations[row]
        operation.area = self.table.cellWidget(row, 4).currentText()
        self.table.cellWidget(row, 5).blockSignals(True)
        self.table.cellWidget(row, 5).clear()
        self.table.cellWidget(row, 5).addItems(operation.possible_workplaces_names)
        self.table.cellWidget(row, 5).blockSignals(False)
        self.table.cellWidget(row, 5).setCurrentText(operation.default_workplace.name)
        self.changeWorkplace()

    def changeWorkplace(self) -> None:
        """ Изменение рабочего места """

        row = self.table.indexAt(self.sender().pos()).row()
        operation = self.document_main.operations[row]
        operation.workplace = self.table.cellWidget(row, 5).currentText()
        self.table.cellWidget(row, 6).blockSignals(True)
        self.table.cellWidget(row, 6).clear()
        self.table.cellWidget(row, 6).addItems(operation.possible_professions_names)
        self.table.cellWidget(row, 6).blockSignals(False)
        self.table.cellWidget(row, 6).setCurrentText(operation.default_profession.name)

    def changeProfession(self) -> None:
        """ Изменение профессии """

        row = self.table.indexAt(self.sender().pos()).row()
        operation = self.document_main.operations[row]
        operation.profession = self.table.cellWidget(row, 6).currentText()

    def delOperationOrder(self, d_order: int, d_row: int) -> None:
        """ Удаление операции """

        logging.debug('Пересчет номеров операций')
        operations = {}
        for row, operation in sorted(self.document_main.operations.items(),
                                     key=lambda x: x[0],
                                     reverse=False):
            if row != d_row:
                if row > d_row:
                    row -= 1
                operations[row] = operation
        self.document_main.operations = operations
        for row, operation in sorted(self.document_main.operations.items(),
                                     key=lambda x: self.table.visualRow(x[0]),
                                     reverse=False):
            if operation.order > d_order:
                debug_msg = f'Операция {operation.num} {operation.name} ' \
                            f'была {operation.order} стала {operation.order - 1}'
                logging.debug(debug_msg)
                operation.order -= 1

    def delOperationButton(self) -> QPushButton:
        """ Кнопка удаления операции """

        btn_del_op = QPushButton('-')
        btn_del_op.clicked.connect(self.deleleOperation)
        return btn_del_op

    def delOperationButtonClicked(self, order: int | None = None) -> None:
        """  """

        if not order:
            row = self.table.indexAt(self.sender().pos()).row()
            order = self.table.visualRow(self.table.indexAt(self.sender().pos()).row())
            self.del_operation = OperationBuilder.operations[(self.document_main, order)]
            self.delOperationOrder(d_order=order, d_row=row)
            self.table.removeRow(row)
            self.operationNumsUpdate()

    def moveOperation(self) -> None:
        """  """

        logging.debug(f'Изменение положения операций')
        self.operationNumsUpdate()
        self.updateButtons.emit()

    def operation(self, operation: Operation) -> QComboBox:
        """  """

        cb = QComboBox()
        default_operations = Operation.defaultOperationsName(operation.document_main.product)
        if operation.name not in default_operations:
            default_operations.append(operation.name)
        cb.addItems(sorted(default_operations))
        cb.setCurrentText(operation.name)
        cb.currentTextChanged.connect(self.changeOperation)
        return cb

    def operationNumsUpdate(self) -> None:
        """  """

        logging.debug(f'Обновление номеров операций при смене их порядка')
        for row in range(self.table.rowCount()):
            new_order = self.table.visualRow(row)
            operation = self.document_main.operations[row]
            logging.debug(f'Операция {operation.num} {operation.name} {operation.order} -> {new_order}')
            operation.order = new_order
            self.table.cellWidget(row, 2).setText(operation.num)

    def area(self, operation: Operation) -> QComboBox:
        """  """

        cb = QComboBox()
        cb.addItems(operation.possible_areas_names)
        if operation.area.name not in operation.possible_areas_names:
            cb.addItems([operation.area.name])
        cb.setCurrentText(operation.area.name)
        cb.currentTextChanged.connect(self.changeArea)
        return cb

    def workplace(self, operation: Operation) -> QComboBox:
        """  """

        cb = QComboBox()
        cb.addItems(operation.possible_workplaces_names)
        if operation.workplace.name not in operation.possible_workplaces_names:
            cb.addItems([operation.workplace.name])
        cb.setCurrentText(operation.workplace.name)
        cb.currentTextChanged.connect(self.changeWorkplace)
        return cb

    def profession(self, operation: Operation) -> QComboBox:
        """  """

        cb = QComboBox()
        cb.addItems(operation.possible_professions_names)
        if operation.profession.name not in operation.possible_professions_names:
            cb.addItems([operation.profession.name])
        cb.setCurrentText(operation.profession.name)
        cb.currentTextChanged.connect(self.changeProfession)
        return cb

    @property
    def document_main(self) -> Document:
        """  """

        return self._document_main

    @document_main.setter
    def document_main(self, document: Document) -> None:
        """  """

        self._document_main = document


# Рамка для отображения главных свойств операции генерируемой МК
class FrameMkOperationMain(FrameBasic):
    """  """

    def __init__(self, document: Document, operation: Operation) -> None:
        logging.debug(f'Инициализация рамки для отображения главных свойств операции генерируемой МК')
        self._operation_num_font = QFont(CONFIG.style.font,
                                         CONFIG.style.font_size_big, 1)
        self.document = document
        self.operation = operation
        self.operation_name = f'{operation.num} {operation.name}'
        super().__init__(frame_name=self.operation_name)
        self.icon_close = CONFIG.style.arrow_up
        self.icon_open = CONFIG.style.arrow_down
        self.initWidgetLabel()
        self.initFrame()
        self.initFrameData()
        self.initFrameConnection()
        self.initWidgetPosition()
        self.layout().setColumnStretch(1, 1)

    def initWidgetLabel(self) -> None:
        """  """

        self._l_operation_num = QLabel(self.operation.num)
        self._l_operation = QLabel(self.operation.name)
        self._l_operation_num.setFont(self._operation_num_font)
        self._l_operation.setFont(self._operation_num_font)
        self._l_settings = QLabel('Свойства')
        self._l_iot = QLabel('ИОТ')
        self._l_equipments = QLabel('Оборудование')
        self._l_documents = QLabel('Документы')
        self._l_materials = QLabel('Материалы')
        self._l_rigs = QLabel('Оснастка')
        self._l_sentences = QLabel('Переходы')

    def initWidgetButton(self) -> QPushButton:
        """  """

        btn = QPushButton()
        btn.setIcon(self.icon_open)
        btn.clicked.connect(self.changeButtonIcon)
        return btn

    def changeButtonIcon(self) -> None:
        """  """

        btn = self.sender()
        index = self.layout().indexOf(btn)
        is_hidden = self.layout().itemAt(index + 1).widget().isHidden()
        if is_hidden:
            btn.setIcon(self.icon_open)
            self.layout().itemAt(index + 1).widget().setVisible(True)
            self.layout().itemAt(index + 1).widget().updateGeometry()
            if isinstance(self.layout().itemAt(index + 1).widget(), FrameOperationText):
                self.layout().itemAt(index + 1).widget().colResized()
        else:
            btn.setIcon(self.icon_close)
            self.layout().itemAt(index + 1).widget().setVisible(False)

    def initFrame(self) -> None:
        """  """

        self._f_iots = IotText(operation=self.operation)
        self._f_documents = DocText(operation=self.operation)
        self._f_materials = MatText(operation=self.operation)
        self._f_rigs = RigText(operation=self.operation)
        self._f_equipments = EquipmentText(operation=self.operation)
        self._f_sentences = FrameOperationText(operation=self.operation)
        self._f_settings = FrameOperationSettings(self.operation)

    def initFrameData(self) -> None:
        """  """

        self._f_iots.upd()
        self._f_documents.upd()
        self._f_rigs.upd()
        self._f_equipments.upd()
        self._f_materials.upd()

    def initFrameConnection(self) -> None:
        """  """

        self._f_sentences.updRig.connect(self._f_rigs.upd)
        self._f_sentences.updEquipment.connect(self._f_equipments.upd)
        self._f_sentences.updIot.connect(self._f_iots.upd)
        self._f_sentences.updMat.connect(self._f_materials.upd)
        self._f_sentences.updDoc.connect(self._f_documents.upd)
        self._f_settings.updSentenceTable.connect(self._f_sentences.updTable)

    def initWidgetPosition(self) -> None:
        """  """

        self.layout().addWidget(self._l_operation_num, 0, 0)
        self.layout().addWidget(self._l_operation, 0, 1)
        self.widgets = {self._l_settings: inScroll(widget=self._f_settings),
                        self._l_iot: self._f_iots,
                        self._l_documents: self._f_documents,
                        self._l_equipments: self._f_equipments,
                        self._l_materials: self._f_materials,
                        self._l_rigs: self._f_rigs,
                        self._l_sentences: inScroll(widget=self._f_sentences),
                        }
        for num, label in enumerate(self.widgets.keys()):
            row = 2 + num * 2
            btn = self.initWidgetButton()
            self.layout().addWidget(label, row, 1)
            self.layout().addWidget(btn, row, 0)
            self.layout().addWidget(self.widgets[label], row + 1, 0, 1, 2)
            if label != self._l_sentences:
                self.widgets[label].setVisible(False)
                btn.setIcon(self.icon_close)
        self.layout().setRowStretch(self.layout().rowCount() - 1, 1)

    def updFrame(self) -> None:
        """  """

        self.name = f'{self.operation.num} {self.operation.name}'
        self._l_operation_num.setText(self.operation.num)
        self._l_operation.setText(self.operation.name)
        logging.debug(f'Обновляется рамка {self.name}')


# Рамка с кнопками для переключения между операциями генерируемой МК
class FrameOperationButtons(QFrame):
    """  """

    showFrame = pyqtSignal()

    def __init__(self) -> None:
        logging.debug(f'Инициализация рамки кнопок переключения между операциями')
        super().__init__()
        self.setLayout(QGridLayout())
        self.layout().setRowStretch(1000, 1)
        self.setMinimumWidth(35)

    def updButtons(self, frames: list[FrameMkMain, FrameMkOperations, FrameMkOperationMain]) -> None:
        """  """

        self.delButtons()
        self.addButtons(frames)

    def addButtons(self, frames: list[FrameMkMain, FrameMkOperations, FrameMkOperationMain]) -> None:
        """  """

        logging.debug(f'Создание кнопок переключения между операциями')
        operation_frames = [frame for frame in frames[2:]]
        operation_frames = sorted(operation_frames, key=lambda frame: frame.operation.num)
        for frame in operation_frames:
            frame.updFrame()
            btn_text = '\n'.join(text_slicer(text=frame.name[4:], max_len=120))
            btn = QPushButton(f'{frame.name[:3]}\n{btn_text}')
            btn.setObjectName(frame.name)
            logging.debug(f'Создана кнопка {btn.text()}')
            btn.setStyleSheet("Text-align:left")
            self.layout().addWidget(btn, self.layout().count(), 0)
            btn.clicked.connect(lambda: self.currentFrame())

    def currentFrame(self) -> None:
        """  """

        self.current_frame = self.sender().objectName()
        logging.debug(self.current_frame)
        self.showFrame.emit()

    def delButtons(self) -> None:
        """  """

        logging.debug(f'Удаление кнопок переключения между операциями')
        for row in reversed(range(self.layout().count())):
            button = self.layout().itemAtPosition(row, 0).widget()
            logging.debug(f'Удалена кнопка {button.text()}')
            self.layout().removeWidget(button)
            button.deleteLater()
            button = None


# Рамка с особенностями генерируемой МК
class FrameOperationSettings(QFrame):
    """  """

    updSentenceTable = pyqtSignal()

    def __init__(self, operation: Operation) -> None:
        logging.debug(f'Инициализация рамки с особенностями генерируемой МК')
        super().__init__()

        self.operation = operation
        self.settings = {}
        self.initCheckbox()
        self.initCheckboxState()
        self.setLayout(QVBoxLayout())
        self.initCheckboxPosition()

    def initCheckbox(self) -> None:
        """  """

        for setting in sorted(self.operation.settings.values(), key=lambda _setting: _setting.name):
            checkbox = QCheckBox(setting.name)
            checkbox.stateChanged.connect(self.checkboxStateChanged)
            self.settings[checkbox] = setting

    def initCheckboxState(self) -> None:
        """  """

        for checkbox, setting in self.settings.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(setting.activated)
            checkbox.blockSignals(False)

    def initCheckboxPosition(self) -> None:
        """  """

        for cb in self.settings.keys():
            self.layout().addWidget(cb)

    def checkboxStateChanged(self) -> None:
        """  """

        checkbox = self.sender()
        setting = self.settings[checkbox]
        setting.activated = checkbox.isChecked()
        if setting.activated:
            setting.addSentences()
        else:
            setting.delSentences()
        self.updSentenceTable.emit()


# Рамка для документов операции генерируемой МК (НЕ ИСПОЛЬЗУЕТСЯ)
class FrameOperationDocuments(QFrame):
    """  """

    def __init__(self, operation) -> None:
        logging.debug(f'Инициализация рамки видов документов')
        super().__init__()
        self.operation = operation
        self.documents = {}
        self.initCheckbox()
        self.initCheckboxState()
        self.setLayout(QVBoxLayout())
        self.initCheckboxPosition()

    def initCheckbox(self) -> None:
        """  """

        for document_in_operation in self.operation.documents:
            checkbox = QCheckBox(f'{document_in_operation.document.deno} {document_in_operation.document.subtype_name}')
            checkbox.stateChanged.connect(self.checkboxStateChanged)
            self.documents[checkbox] = document_in_operation

    def initCheckboxPosition(self) -> None:
        """  """

        for checkbox in self.documents.keys():
            self.layout().addWidget(checkbox)

    def initCheckboxState(self) -> None:
        """  """

        for checkbox, document in self.documents.items():
            checkbox.setChecked(document.activated)

    def checkboxStateChanged(self) -> None:
        """  """

        checkbox = self.sender()
        document_in_operation = self.documents[checkbox]
        document_in_operation.activated = checkbox.isChecked()


# Рамка для текста переходов генерируемой МК
class FrameOperationText(FrameWithTable):
    """  """

    updIot = pyqtSignal()
    updRig = pyqtSignal()
    updMat = pyqtSignal()
    updDoc = pyqtSignal()
    updEquipment = pyqtSignal()

    def __init__(self, operation) -> None:
        super().__init__()
        self.operation = operation
        self.initSettings()
        self.operation.initSentences()
        self.initSentences()
        self.initHeaderIcons()

    def initSettings(self) -> None:
        """  """

        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setSizeAdjustPolicy(QAbstractScrollArea.AdjustToContents)
        self.table.horizontalHeader().sectionClicked.connect(self.headerClicked)
        self.table.horizontalHeader().sectionResized.connect(self.colResized)
        self.table.verticalHeader().sectionResized.connect(self.rowResized)
        self.table.verticalHeader().setSectionsMovable(True)
        self.table.verticalHeader().sectionMoved.connect(self.moveSentence)

    def initTableSettings(self) -> None:
        """  """

        self.col_txt = 0
        self.col_doc = 1
        self.col_mat = 2
        self.col_rig = 3
        self.col_iot = 4
        self.col_equipment = 5
        self.header_settings = ({'col': self.col_txt, 'width': 600, 'name': 'Текст перехода'},
                                {'col': self.col_doc, 'width': 400, 'name': 'Документы', 'state': 'full'},
                                {'col': self.col_mat, 'width': 400, 'name': 'Материалы', 'state': 'full'},
                                {'col': self.col_rig, 'width': 400, 'name': 'Оснастка', 'state': 'full'},
                                {'col': self.col_iot, 'width': 400, 'name': 'ИОТ', 'state': 'full'},
                                # {'col': self.col_equipment, 'width': 400, 'name': 'Оборудование', 'state': 'full'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

    def initSentences(self) -> None:
        """  """

        for order in range(len(self.operation.sentences.keys())):
            try:
                sentence = self.operation.sentences[order]
                self.addNewRow()
                self.addText(sentence=sentence)
            except KeyError:
                show_dialog(text=f"Ошибка нумерации переходов. Не найден переход {order + 1}")
                break

        self.updRig.emit()
        self.updEquipment.emit()
        self.updIot.emit()
        self.updMat.emit()
        self.updDoc.emit()
        self.colResized()

    def initHeaderIcons(self) -> None:
        """  """

        self.headerState = {}
        for num, setting in enumerate(self.header_settings):
            if 'state' in setting:
                self.headerState[num] = setting['state']
                self.table.horizontalHeader().model().setHeaderData(num,
                                                                    Qt.Horizontal,
                                                                    CONFIG.style.arrow_left,
                                                                    Qt.DecorationRole)

    def cellChanged(self) -> None:
        """  """

        pass

    def showContextMenu(self, point: QPoint) -> None:
        """  """

        self.context_menu = ContextMenuForSentenceTable(self)
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    def addSentence(self, row: int) -> None:
        """  """

        sentence = Sentence(operation=self.operation)
        self.operation.addSentence(order=row + 1, sentence=sentence)
        self.updTable()

    def delSentence(self) -> None:
        """  """

        row = self.table.currentRow()
        self.operation.delSentence(order=row)
        self.operation.restoreSentenceOrder()
        self.updTable()

    def sentenceResized(self, row: int) -> None:
        """  """

        sentence_widget = self.sentenceByRow(row=row)
        if sentence_widget is not None:
            sentence_widget.resizeSentence()
            self.table.resizeRowToContents(row)
            if sentence_widget.current_height < self.table.rowHeight(row):
                sentence_widget.current_height = self.table.rowHeight(row)

    def colResized(self) -> None:
        """  """

        for row in range(self.table.rowCount()):
            self.sentenceResized(row=row)

    def rowResized(self, logicalIndex: int) -> None:
        """  """

        sentence_widget = self.sentenceByRow(row=logicalIndex)
        if sentence_widget is not None:
            sentence_widget.setFixedHeight(self.table.rowHeight(logicalIndex))

    def addText(self, sentence: Sentence) -> None:
        """  """

        row = self.table.rowCount() - 1
        self.widgetSentence(sentence=sentence, row=row)
        self.widgetDoc(sentence=sentence, row=row)
        self.widgetIot(sentence=sentence, row=row)
        self.widgetRig(sentence=sentence, row=row)
        # self.widgetEquipment(sentence=sentence, row=row)
        self.widgetMat(sentence=sentence, row=row)

    def widgetDoc(self, sentence: Sentence, row: int) -> None:
        """  """

        widget = SentenceDoc(sentence=sentence, frame=self)
        self.table.setCellWidget(row, self.col_doc, widget)

    def widgetIot(self, sentence: Sentence, row: int) -> None:
        """  """

        widget = SentenceIot(sentence=sentence, frame=self)
        self.table.setCellWidget(row, self.col_iot, widget)

    def widgetMat(self, sentence: Sentence, row: int) -> None:
        """  """

        widget = SentenceMat(sentence=sentence, frame=self)
        self.table.setCellWidget(row, self.col_mat, widget)

    def widgetRig(self, sentence: Sentence, row: int) -> None:
        """  """

        widget = SentenceRig(sentence=sentence, frame=self)
        self.table.setCellWidget(row, self.col_rig, widget)

    def widgetEquipment(self, sentence: Sentence, row: int) -> None:
        """  """

        widget = SentenceEquipment(sentence=sentence, frame=self)
        self.table.setCellWidget(row, self.col_equipment, widget)

    def widgetSentence(self, sentence: Sentence, row: int) -> None:
        """  """

        widget_sentence = SentenceTextEdit(sentence=sentence, frame=self)
        widget_sentence.sentenceTextChanged.connect(self.sentenceChanged)
        self.table.setCellWidget(row, self.col_txt, widget_sentence)

    def sentenceChanged(self) -> None:
        """  """

        sentence_widget = self.sender()
        text = sentence_widget.toPlainText()
        sentence_widget.sentence.convertToCustom(text=text)
        self.updDoc.emit()
        row = self.table.currentRow()
        self.sentenceResized(row=row)

    def changeOrder(self, sentence: Sentence) -> None:
        """  """

        sentence.order = self.table.rowCount()

    def updTable(self) -> None:
        """  """

        self.deleteAllRows()
        self.initSentences()
        self.applyWidgetVisibility()

    def deleteAllRows(self) -> None:
        """  """

        for row in reversed(range(self.table.rowCount())):
            self.table.removeRow(row)

    def moveSentence(self) -> None:
        """  """

        temp_sentence = {}
        for row in range(self.table.rowCount()):
            sentence_widget = self.table.cellWidget(row, self.col_txt)
            temp_sentence[self.table.visualRow(row)] = sentence_widget.sentence
        self.operation.sentences = temp_sentence
        self.updTable()

    def sentenceByRow(self, row: int) -> SentenceTextEdit | None:
        """  """

        return self.table.cellWidget(row, self.col_txt)

    def headerClicked(self, logicalIndex: int) -> None:
        """  """

        if logicalIndex in self.headerState:
            if self.headerState[logicalIndex] == 'full':
                self.headerState[logicalIndex] = 'half'
                self.table.horizontalHeader().model().setHeaderData(logicalIndex,
                                                                    Qt.Horizontal,
                                                                    CONFIG.style.arrow_left_2,
                                                                    Qt.DecorationRole)
                self.hideWidget(column=logicalIndex, state=self.headerState[logicalIndex])
            elif self.headerState[logicalIndex] == 'half':
                self.headerState[logicalIndex] = 'hide'
                self.table.horizontalHeader().model().setHeaderData(logicalIndex,
                                                                    Qt.Horizontal,
                                                                    CONFIG.style.arrow_right,
                                                                    Qt.DecorationRole)
                self.table.horizontalHeaderItem(logicalIndex).setText('')
                self.table.horizontalHeader().resizeSection(logicalIndex, 10)
                self.hideWidget(column=logicalIndex, state=self.headerState[logicalIndex])
            elif self.headerState[logicalIndex] == 'hide':
                self.headerState[logicalIndex] = 'full'
                self.table.horizontalHeader().model().setHeaderData(logicalIndex,
                                                                    Qt.Horizontal,
                                                                    CONFIG.style.arrow_left,
                                                                    Qt.DecorationRole)
                self.hideWidget(column=logicalIndex, state=self.headerState[logicalIndex])
                self.table.horizontalHeaderItem(logicalIndex).setText(self.header_settings[logicalIndex]['name'])
                self.table.horizontalHeader().resizeSection(logicalIndex,
                                                            self.header_settings[logicalIndex]['width'])

    def hideWidget(self, column: int, state: str) -> None:
        """  """

        for row in range(self.table.rowCount()):
            frame = self.table.cellWidget(row, column)
            frame.itemVisibility(state)

    def applyWidgetVisibility(self) -> None:
        """  """

        for logicalIndex in self.headerState.keys():
            self.hideWidget(logicalIndex, self.headerState[logicalIndex])

