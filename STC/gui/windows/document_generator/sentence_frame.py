""" Рамки для таблицы с параметрами переходов,
    которые содержат переменные данные об
    оснастке, материалах, оборудовании и ИОТ """

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout

from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceAdditionalData
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceDoc
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceEquipment
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceIot
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceMat
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceRig
from STC.gui.windows.document_generator.combobox import ComboBox
from STC.gui.windows.document_generator.combobox import ComboBoxDocByName
from STC.gui.windows.document_generator.combobox import ComboBoxDocByType
from STC.gui.windows.document_generator.combobox import ComboBoxEquipmentByName
from STC.gui.windows.document_generator.combobox import ComboBoxEquipmentByType
from STC.gui.windows.document_generator.combobox import ComboBoxIotByName
from STC.gui.windows.document_generator.combobox import ComboBoxIotByType
from STC.gui.windows.document_generator.combobox import ComboBoxMatByName
from STC.gui.windows.document_generator.combobox import ComboBoxMatByType
from STC.gui.windows.document_generator.combobox import ComboBoxRigByName
from STC.gui.windows.document_generator.combobox import ComboBoxRigByType

if TYPE_CHECKING:
    from PyQt5.QtCore import QPoint
    from PyQt5.QtWidgets import QComboBox
    from STC.product.product import IOT
    from STC.product.product import Rig
    from STC.product.product import Mat
    from STC.product.product import Equipment
    from STC.product.product import Document
    from STC.product.product import Sentence
    from STC.gui.windows.document_generator.frame import FrameOperationText


class SentenceFrame(QFrame):
    """ Родительский класс для рамки с двумя столбцами комбобоксов """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        self.item_type = None
        self.item_name = None
        super().__init__()
        self.frame = frame
        self.sentence = sentence
        self.main_layout = QGridLayout()
        self.setLayout(self.main_layout)
        self.initSettings()
        self.widgets = {}
        self.context_menu = ContextMenuForSentenceAdditionalData(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.initDefaultWidgets()

    def initDefaultWidgets(self) -> None:
        """ Начальные виджеты рамки """

    def initSettings(self) -> None:
        """ Геометрические параметры рамки """

        # self.setLayout(QGridLayout())
        self.combobox_height = 30
        self.row = 0
        self.main_layout.setRowStretch(20, 1)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setSpacing(0)

    def initWidget(self, item: None) -> None:
        """ Инициализация виджетов рамки """

        logging.debug(item)
        self.item_type = ComboBox(frame=self.frame, cb_frame=self)
        self.item_type.currentTextChanged.connect(self.typeChanged)
        self.item_name = ComboBox(frame=self.frame, cb_frame=self)
        self.widgets[self.item_type] = self.item_name

    def addWidget(self, item: Document | IOT | Mat | Rig | Equipment | None = None) -> None:
        """ Инициализация и добавление виджетов на рамку """

        self.initWidget(item)
        self.initWidgetPosition()

    def typeChanged(self) -> None:
        """ Обновление списка элементов комбобоксов """

        self.widgets[self.sender()].updItems()
        self.upd()

    def initWidgetPosition(self) -> None:
        """ Добавление виджетов из self.addWidget в рамку """

        self.main_layout.addWidget(self.item_type, self.row, 0)
        self.main_layout.addWidget(self.item_name, self.row, 1)
        self.main_layout.setRowMinimumHeight(self.row, self.combobox_height)
        self.row += 1

    def newWidget(self, item=None) -> None:
        """ Добавление нового виджета в рамку
            с изменением параметров рамки и
            различными методами обновлений """
        item = None if isinstance(item, bool) else item
        self.addWidget(item=item)
        self.upd()
        self.frame.sentenceResized(self.frame.table.currentRow())

    def showContextMenu(self, point: QPoint) -> None:
        """ Контекстное меню """

        qpoint = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qpoint)

    def nameChanged(self) -> None:
        """ Вызывает методы при изменении
            данных комбобоксов """

        self.upd()
        self.sentence.convertToCustom()

    def delWidget(self, combobox: QComboBox) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Вызов сторонних методов при изменении значений комбобоксов """

    def itemVisibility(self, state: str) -> None:
        """ Изменение отображения виджетов в рамке """

        if state == 'full':
            for widget1, widget2 in self.widgets.items():
                widget1.setVisible(True)
                widget2.setVisible(True)
                self.main_layout.setColumnStretch(1, 1)
        elif state == 'half':
            for widget1, widget2 in self.widgets.items():
                widget1.setVisible(False)
                widget2.setVisible(True)
                self.main_layout.setColumnStretch(1, 3000)
        elif state == 'hide':
            for widget1, widget2 in self.widgets.items():
                widget1.setVisible(False)
                widget2.setVisible(False)
                self.main_layout.setColumnStretch(1, 1)

    def convertSentenceToCustom(self) -> None:
        """ Изменение перехода:
            "переход с типовым текстом" ->
            "переход с нетиповым текстом"
            """

        self.sentence.convertToCustom()


class SentenceIot(SentenceFrame):
    """ Виджет для отображения ИОТ в таблице с переходами """

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceIot(self)

    def initDefaultWidgets(self) -> None:
        """ Виджеты рамки при ее инициализации
            По списку ИОТ, привязанных к переходу """

        for iot in self.sentence.iot.values():
            self.addWidget(item=iot)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: IOT) -> None:
        """ Создание комбобоксов """

        self.item_type = ComboBoxIotByType(frame=self.frame,
                                           cb_frame=self,
                                           item=item)
        self.item_type.currentTextChanged.connect(self.typeChanged)

        self.item_name = ComboBoxIotByName(frame=self.frame,
                                           cb_frame=self,
                                           cb_type=self.item_type,
                                           item=item)
        self.item_name.currentTextChanged.connect(self.nameChanged)
        self.widgets[self.item_type] = self.item_name

    def delWidget(self, combobox: ComboBoxIotByType) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Обновление перехода и рамок, связанных с изменением значений комбобокса """

        new_iot = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                db_iot = item_name_item.widget().item
                iot = self.sentence.createIot(db_iot=db_iot)
                new_iot[iot.deno] = iot
        self.sentence.iot = new_iot
        self.frame.updIot.emit()


class SentenceRig(SentenceFrame):
    """ Виджет для отображения оснастки в таблице с переходами """

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceRig(self)

    def initDefaultWidgets(self) -> None:
        """ Виджеты рамки при ее инициализации
            По списку оснастки, привязанной к переходу """

        for rig in self.sentence.rig.values():
            self.addWidget(item=rig)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Rig) -> None:
        """ Создание комбобоксов """

        self.item_type = ComboBoxRigByType(frame=self.frame,
                                           cb_frame=self,
                                           item=item)
        self.item_type.currentTextChanged.connect(self.typeChanged)
        self.item_name = ComboBoxRigByName(frame=self.frame,
                                           cb_frame=self,
                                           cb_type=self.item_type,
                                           item=item)
        self.item_name.currentTextChanged.connect(self.nameChanged)
        self.widgets[self.item_type] = self.item_name

    def delWidget(self, combobox: ComboBoxRigByType) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Обновление перехода и рамок, связанных с изменением значений комбобокса """

        new_rig = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                db_rig = item_name_item.widget().item
                rig = self.sentence.createRig(db_rig=db_rig)
                new_rig[rig.name] = rig
        self.sentence.rig = new_rig
        self.convertSentenceToCustom()
        self.frame.updRig.emit()


class SentenceMat(SentenceFrame):
    """ Виджет для отображения материалов в таблице с переходами """

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceMat(self)

    def initDefaultWidgets(self) -> None:
        """ Виджеты рамки при ее инициализации
            По списку материалов, привязанных к переходу """

        for mat in self.sentence.mat.values():
            self.addWidget(item=mat)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Mat) -> None:
        """ Создание комбобоксов """

        self.item_type = ComboBoxMatByType(frame=self.frame,
                                           cb_frame=self,
                                           item=item)
        self.item_type.currentTextChanged.connect(self.typeChanged)

        self.item_name = ComboBoxMatByName(frame=self.frame,
                                           cb_frame=self,
                                           cb_type=self.item_type,
                                           item=item)
        self.item_name.currentTextChanged.connect(self.nameChanged)
        self.widgets[self.item_type] = self.item_name

    def delWidget(self, combobox: ComboBoxMatByType) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Обновление перехода и рамок, связанных с изменением значений комбобокса """

        new_mat = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                db_mat = item_name_item.widget().item
                mat = self.sentence.createMat(db_mat=db_mat)
                new_mat[mat.name] = mat
        self.sentence.mat = new_mat
        self.convertSentenceToCustom()
        self.frame.updMat.emit()


class SentenceEquipment(SentenceFrame):
    """ Виджет для отображения оснастки в таблице с переходами """

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceEquipment(self)

    def initDefaultWidgets(self) -> None:
        """ Виджеты рамки при ее инициализации
            По списку оборудования, привязанному к переходу """

        for equipment in self.sentence.equipment.values():
            self.addWidget(item=equipment)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Equipment) -> None:
        """ Создание комбобоксов """

        self.item_type = ComboBoxEquipmentByType(frame=self.frame,
                                                 cb_frame=self,
                                                 item=item)
        self.item_type.currentTextChanged.connect(self.typeChanged)
        self.item_name = ComboBoxEquipmentByName(frame=self.frame,
                                                 cb_frame=self,
                                                 cb_type=self.item_type,
                                                 item=item)
        self.item_name.currentTextChanged.connect(self.nameChanged)
        self.widgets[self.item_type] = self.item_name

    def delWidget(self, combobox: ComboBoxEquipmentByType) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Обновление перехода и рамок, связанных с изменением значений комбобокса """

        new_equipment = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                db_equipment = item_name_item.widget().item
                equipment = self.sentence.createEquipment(db_equipment=db_equipment)
                new_equipment[equipment.name] = equipment
        self.sentence.equipment = new_equipment
        self.convertSentenceToCustom()
        self.frame.updEquipment.emit()


class SentenceDoc(SentenceFrame):
    """ Виджет для отображения документов в таблице с переходами """

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceDoc(self)

    def initDefaultWidgets(self) -> None:
        """ Виджеты рамки при ее инициализации
            По списку видов документов, привязанных к переходу """

        for doc in self.sentence.doc.values():
            self.addWidget(item=doc)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Document) -> None:
        """ Создание комбобоксов """

        documents = self.sentence.product.documents
        self.item_type = ComboBoxDocByType(frame=self.frame,
                                           cb_frame=self,
                                           documents=documents,
                                           item=item)
        self.item_type.currentTextChanged.connect(self.typeChanged)

        self.item_name = ComboBoxDocByName(frame=self.frame,
                                           cb_frame=self,
                                           cb_type=self.item_type,
                                           documents=documents,
                                           item=item)
        self.item_name.currentTextChanged.connect(self.nameChanged)
        self.widgets[self.item_type] = self.item_name

    def delWidget(self, combobox: ComboBoxDocByType) -> None:
        """ Удаление определенных комбобоксов из рамки """

        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox in (item_type, item_name):
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    self.widgets.pop(item_type)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        """ Обновление перехода и рамок, связанных с изменением значений комбобокса """

        new_doc = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                document = item_name_item.widget().item
                new_doc[document.deno] = document
        self.sentence.doc = new_doc
        self.convertSentenceToCustom()
        self.frame.updDoc.emit()
