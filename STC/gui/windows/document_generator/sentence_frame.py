from __future__ import annotations
from typing import TYPE_CHECKING

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


# Виджет рамки с двумя столбцами комбобоксов
class SentenceFrame(QFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
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
        pass

    def initSettings(self) -> None:
        # self.setLayout(QGridLayout())
        self.combobox_height = 30
        self.row = 0
        self.main_layout.setRowStretch(20, 1)
        self.main_layout.setColumnStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)
        self.main_layout.setSpacing(0)

    def initWidget(self, item: None) -> None:
        self.item_type = ComboBox(frame=self.frame, cb_frame=self)
        self.item_type.currentTextChanged.connect(self.typeChanged)
        self.item_name = ComboBox(frame=self.frame, cb_frame=self)
        self.widgets[self.item_type] = self.item_name

    def addWidget(self, item: Document | IOT | Mat | Rig | Equipment | None = None) -> None:
        self.initWidget(item)
        self.initWidgetPosition()

    def typeChanged(self) -> None:
        self.widgets[self.sender()].updItems()
        self.upd()

    def initWidgetPosition(self) -> None:
        self.main_layout.addWidget(self.item_type, self.row, 0)
        self.main_layout.addWidget(self.item_name, self.row, 1)
        self.main_layout.setRowMinimumHeight(self.row, self.combobox_height)
        self.row += 1

    def newWidget(self, item=None) -> None:
        self.addWidget(item=item)
        self.upd()
        self.frame.sentenceResized(self.frame.table.currentRow())

    def showContextMenu(self, point: QPoint) -> None:
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    def nameChanged(self) -> None:
        self.upd()
        self.sentence.convertToCustom()

    def delWidget(self, combobox: QComboBox) -> None:
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        pass

    def itemVisibility(self, state: str) -> None:
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
        self.sentence.convertToCustom()


# Виджет для отображения ИОТ в таблице с переходами
class SentenceIot(SentenceFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceIot(self)

    def initDefaultWidgets(self) -> None:
        for iot in self.sentence.iot.values():
            self.addWidget(item=iot)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: IOT) -> None:
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
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        new_iot = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                db_iot = item_name_item.widget().item
                iot = self.sentence.createIot(db_iot=db_iot)
                new_iot[iot.deno] = iot
        self.sentence.iot = new_iot
        self.frame.updIot.emit()


# Виджет для отображения оснастки в таблице с переходами
class SentenceRig(SentenceFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceRig(self)

    def initDefaultWidgets(self) -> None:
        for rig in self.sentence.rig.values():
            self.addWidget(item=rig)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Rig) -> None:
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
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
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


# Виджет для отображения материалов в таблице с переходами
class SentenceMat(SentenceFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceMat(self)

    def initDefaultWidgets(self) -> None:
        for mat in self.sentence.mat.values():
            self.addWidget(item=mat)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Mat) -> None:
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
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
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


# Виджет для отображения оснастки в таблице с переходами
class SentenceEquipment(SentenceFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceEquipment(self)

    def initDefaultWidgets(self) -> None:
        for equipment in self.sentence.equipment.values():
            self.addWidget(item=equipment)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Equipment) -> None:
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
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
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


# Виджет для отображения документов в таблице с переходами
class SentenceDoc(SentenceFrame):

    def __init__(self, frame: FrameOperationText, sentence: Sentence) -> None:
        super().__init__(frame=frame, sentence=sentence)
        self.context_menu = ContextMenuForSentenceDoc(self)

    def initDefaultWidgets(self) -> None:
        for doc in self.sentence.doc.values():
            self.addWidget(item=doc)
        self.frame.sentenceResized(self.frame.table.currentRow())

    def initWidget(self, item: Document) -> None:
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
        for row in range(self.main_layout.rowCount()):
            item_type_item = self.main_layout.itemAtPosition(row, 0)
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_type_item is not None and item_name_item is not None:
                item_type = item_type_item.widget()
                item_name = item_name_item.widget()
                if combobox == item_type or combobox == item_name:
                    self.main_layout.removeWidget(item_type)
                    self.main_layout.removeWidget(item_name)
                    self.main_layout.setRowMinimumHeight(row, 0)
                    item_type.deleteLater()
                    item_name.deleteLater()
                    self.upd()
                    break
        self.frame.sentenceResized(self.frame.table.currentRow())

    def upd(self) -> None:
        new_doc = {}
        for row in range(self.main_layout.rowCount()):
            item_name_item = self.main_layout.itemAtPosition(row, 1)
            if item_name_item is not None:
                document = item_name_item.widget().item
                new_doc[document.deno] = document
        self.sentence.doc = new_doc
        self.convertSentenceToCustom()
        self.frame.updDoc.emit()
