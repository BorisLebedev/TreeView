""" Комбобоксы для строк переходов
    окна создания маршрутных карт """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceCombobox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceIotCombobox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceDocCombobox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceRigCombobox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceEquipmentCombobox
from STC.gui.windows.document_generator.context_menu import ContextMenuForSentenceMatCombobox
from STC.product.product import IOT
from STC.product.product import Rig
from STC.product.product import Mat
from STC.product.product import Equipment

if TYPE_CHECKING:
    from PyQt5.QtCore import QPoint
    from STC.product.product import Document
    from STC.gui.windows.document_generator.frame import FrameOperationText
    from STC.gui.windows.document_generator.sentence_frame import SentenceFrame
    from STC.gui.windows.document_generator.sentence_frame import SentenceDoc
    from STC.gui.windows.document_generator.sentence_frame import SentenceIot
    from STC.gui.windows.document_generator.sentence_frame import SentenceRig
    from STC.gui.windows.document_generator.sentence_frame import SentenceMat
    from STC.gui.windows.document_generator.sentence_frame import SentenceEquipment


class ComboBox(QComboBox):
    """ ComboBox с контекстным меню """

    def __init__(self, frame: FrameOperationText, cb_frame: SentenceFrame) -> None:
        super().__init__()
        self.wheelEvent = lambda event: None
        self.frame = frame
        self.cb_frame = cb_frame
        self.values_dict = {}
        self.context_menu = ContextMenuForSentenceCombobox(self)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.initSettings()

    def initSettings(self) -> None:
        """ Установка геометрических параметров """

        self.setMaximumWidth(200)
        self.setMinimumWidth(200)
        self.setMinimumHeight(self.cb_frame.combobox_height)
        self.setMaximumHeight(self.cb_frame.combobox_height)

    def showContextMenu(self, point: QPoint) -> None:
        """ Контекстное меню """

        qpoint = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qpoint)


class ComboBoxByType(ComboBox):
    """ ComboBox с контекстным меню """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceDoc |
                           SentenceIot |
                           SentenceRig |
                           SentenceMat |
                           SentenceEquipment) -> None:
        super().__init__(frame, cb_frame)

    def initSettings(self) -> None:
        """ Установка геометрических параметров """

        self.setMaximumWidth(200)
        self.setMinimumWidth(200)
        self.setMinimumHeight(self.cb_frame.combobox_height)
        self.setMaximumHeight(self.cb_frame.combobox_height)


class ComboBoxIotByType(ComboBoxByType):
    """ ComboBox для типов ИОТ с контекстным меню """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceIot,
                 item: IOT | None = None) -> None:
        super().__init__(frame, cb_frame)
        self.context_menu = ContextMenuForSentenceIotCombobox(self)
        self.item = item
        self.initData()

    def initData(self) -> None:
        """ Список допустимых значений """

        iot_types = sorted(IOT.allIotTypes())
        self.addItems(iot_types)
        if self.item is not None:
            self.setCurrentText(self.item.type_short)


class ComboBoxDocByType(ComboBoxByType):
    """ ComboBox для типов документов с контекстным меню """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceDoc,
                 documents: set[Document],
                 item: Document | None = None):
        super().__init__(frame, cb_frame)
        self.documents = documents
        self.context_menu = ContextMenuForSentenceDocCombobox(self)
        self.item = item
        self.initData()

    def initData(self) -> None:
        """ Список допустимых значений """

        doc_types = sorted([document.subtype_name for document in self.documents])
        self.addItems(doc_types)
        if self.item is not None:
            self.setCurrentText(self.item.subtype_name)


class ComboBoxRigByType(ComboBoxByType):
    """ ComboBox для типов оснастки с контекстным меню """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceRig,
                 item: Rig | None = None) -> None:
        super().__init__(frame, cb_frame)
        self.context_menu = ContextMenuForSentenceRigCombobox(self)
        self.item = item
        self.initData()

    def initData(self) -> None:
        """ Список допустимых значений """

        rig_types = sorted(Rig.allRigTypes())
        self.addItems(rig_types)
        if self.item is not None:
            self.setCurrentText(self.item.rig_type)


class ComboBoxMatByType(ComboBoxByType):
    """ ComboBox для типов материалов с контекстным меню """

    def __init__(self, frame: FrameOperationText, cb_frame: SentenceMat, item: Mat | None = None):
        super().__init__(frame, cb_frame)
        self.context_menu = ContextMenuForSentenceMatCombobox(self)
        self.item = item
        self.initData()

    def initData(self) -> None:
        """ Список допустимых значений """

        mat_kinds = sorted(Mat.allMatKinds())
        self.addItems(mat_kinds)
        if self.item is not None:
            self.setCurrentText(self.item.kind)


class ComboBoxEquipmentByType(ComboBoxByType):
    """ ComboBox для типов оснастки с контекстным меню """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceEquipment,
                 item: Equipment | None = None) -> None:
        super().__init__(frame, cb_frame)
        self.context_menu = ContextMenuForSentenceEquipmentCombobox(self)
        self.item = item
        self.initData()

    def initData(self) -> None:
        """ Список допустимых значений """

        equipment_types = sorted(Equipment.allEquipmentShortNames())
        self.addItems(equipment_types)
        if self.item is not None:
            self.setCurrentText(self.item.name_short)


class ComboBoxByName(ComboBox):
    """ ComboBox для имен данных типа ИОТ, оснастка, материал """

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceDoc |
                           SentenceIot |
                           SentenceRig |
                           SentenceMat |
                           SentenceEquipment,
                 cb_type: ComboBoxDocByType |
                          ComboBoxIotByType |
                          ComboBoxRigByType |
                          ComboBoxMatByType |
                          ComboBoxEquipmentByType,
                 item: Document |
                       IOT |
                       Rig |
                       Mat |
                       Equipment |
                       None = None) -> None:
        super().__init__(frame, cb_frame)
        self.setMaximumWidth(2000)
        self.cb_type = cb_type
        self.updItemDict()
        self._item = item
        self.initData()

    def updItemDict(self) -> None:
        """ Обновление перечня значений
            для комбобоксов """

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от
            значения в соседнем комбобоксе """


class ComboBoxIotByName(ComboBoxByName):
    """ ComboBox для ИОТ с контекстным меню """

    item_dict = {}

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceIot,
                 cb_type: ComboBoxIotByType,
                 item: IOT | None = None):
        super().__init__(frame, cb_frame, cb_type, item)
        self.context_menu = ContextMenuForSentenceIotCombobox(self)

    def updItemDict(self) -> None:
        """ Обновление перечня ИОТ """

        if not self.__class__.item_dict:
            for iot in IOT.allIot():
                key = f'{iot.deno} {iot.name_short}'
                self.__class__.item_dict[key] = iot

    @classmethod
    def updItemDictCls(cls) -> None:
        """ Обновление перечня ИОТ """

        for iot in IOT.allIot():
            key = f'{iot.deno} {iot.name_short}'
            cls.item_dict[key] = iot

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

        self.updItems()
        if self._item is not None:
            self.setCurrentText(f'{self._item.deno} {self._item.name_short}')

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от типа
            (значения в соседнем комбобоксе) """

        items_to_add = []
        for key, iot in self.__class__.item_dict.items():
            if iot.type_short == self.cb_type.currentText():
                items_to_add.append(key)
        items_to_add = sorted(set(items_to_add))
        self.blockSignals(True)
        self.clear()
        self.addItems(items_to_add)
        self.blockSignals(False)

    @property
    def item(self) -> str:
        """ Возвращает экземпляр класса
            по значению комбобокса """

        return self.__class__.item_dict[self.currentText()]


class ComboBoxDocByName(ComboBoxByName):
    """ ComboBox для документов с контекстным меню """

    item_dict = {}

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceDoc,
                 cb_type: ComboBoxDocByType,
                 documents: set[Document],
                 item: Document | None = None):
        self.documents = documents
        self.item_dict = {}
        super().__init__(frame, cb_frame, cb_type, item)
        self.context_menu = ContextMenuForSentenceDocCombobox(self)

    def updItemDict(self) -> None:
        """ Обновление перечня видов документов """

        if not self.item_dict:
            for document in self.documents:
                key = f'{document.deno}'
                self.item_dict[key] = document

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

        self.updItems()
        if self._item is not None:
            self.setCurrentText(f'{self._item.deno}')

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от типа
            (значения в соседнем комбобоксе) """

        items_to_add = []
        for doc in self.item_dict.values():
            if doc.subtype_name == self.cb_type.currentText():
                items_to_add.append(doc.deno)
        items_to_add = sorted(set(items_to_add))
        self.blockSignals(True)
        self.clear()
        self.addItems(items_to_add)
        self.blockSignals(False)

    @property
    def item(self) -> str:
        """ Возвращает экземпляр класса
            по значению комбобокса """

        return self.item_dict[self.currentText()]


class ComboBoxRigByName(ComboBoxByName):
    """ ComboBox для оснастки с контекстным меню """

    item_dict = {}

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceRig,
                 cb_type: ComboBoxRigByType,
                 item: Rig | None = None):
        super().__init__(frame, cb_frame, cb_type, item)
        self.context_menu = ContextMenuForSentenceRigCombobox(self)

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

        self.updItems()
        if self._item is not None:
            self.setCurrentText(f'{self._item.name}')

    def updItemDict(self) -> None:
        """ Обновление перечня оснастки """

        if not self.__class__.item_dict:
            for rig in Rig.allRig():
                key = f'{rig.name}'
                self.__class__.item_dict[key] = rig

    @classmethod
    def updItemDictCls(cls) -> None:
        """ Обновление перечня оснастки """

        for rig in Rig.allRig():
            key = f'{rig.name}'
            cls.item_dict[key] = rig

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от типа
            (значения в соседнем комбобоксе) """

        items_to_add = []
        for key, rig in self.__class__.item_dict.items():
            if rig.rig_type == self.cb_type.currentText():
                items_to_add.append(key)
        items_to_add = sorted(set(items_to_add))
        self.blockSignals(True)
        self.clear()
        self.addItems(items_to_add)
        self.blockSignals(False)

    @property
    def item(self) -> str:
        """ Возвращает экземпляр класса
            по значению комбобокса """

        return self.__class__.item_dict[self.currentText()]


class ComboBoxMatByName(ComboBoxByName):
    """ ComboBox для материалов с контекстным меню """

    item_dict = {}

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceMat,
                 cb_type: ComboBoxMatByType,
                 item: Mat | None = None) -> None:
        super().__init__(frame, cb_frame, cb_type, item)
        self.context_menu = ContextMenuForSentenceMatCombobox(self)

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

        self.updItems()
        if self._item is not None:
            self.setCurrentText(f'{self._item.name}')

    def updItemDict(self) -> None:
        """ Обновление перечня материалов """

        if not self.__class__.item_dict:
            for mat in Mat.allMat():
                key = f'{mat.name}'
                self.__class__.item_dict[key] = mat

    @classmethod
    def updItemDictCls(cls) -> None:
        """ Обновление перечня материалов """

        for mat in Mat.allMat():
            key = f'{mat.name}'
            cls.item_dict[key] = mat

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от типа
            (значения в соседнем комбобоксе) """

        items_to_add = []
        for key, mat in self.__class__.item_dict.items():
            if mat.kind == self.cb_type.currentText():
                items_to_add.append(key)
        items_to_add = sorted(set(items_to_add))
        self.blockSignals(True)
        self.clear()
        self.addItems(items_to_add)
        self.blockSignals(False)

    @property
    def item(self) -> str:
        """ Возвращает экземпляр класса
            по значению комбобокса """

        return self.__class__.item_dict[self.currentText()]


class ComboBoxEquipmentByName(ComboBoxByName):
    """ ComboBox для оснастки с контекстным меню """

    item_dict = {}

    def __init__(self, frame: FrameOperationText,
                 cb_frame: SentenceEquipment,
                 cb_type: ComboBoxEquipmentByType,
                 item: Equipment | None = None) -> None:
        super().__init__(frame, cb_frame, cb_type, item)
        self.context_menu = ContextMenuForSentenceEquipmentCombobox(self)

    def initData(self) -> None:
        """ Обновляет список значений комбобокса
            и устанавливает текущее """

        self.updItems()
        if self._item is not None:
            self.setCurrentText(f'{self._item.name}')

    def updItemDict(self) -> None:
        """ Обновление перечня оборудования """

        if not self.__class__.item_dict:
            for equipment in Equipment.allEquipment():
                key = f'{equipment.name}'
                self.__class__.item_dict[key] = equipment

    @classmethod
    def updItemDictCls(cls) -> None:
        """ Обновление перечня оборудования """

        for equipment in Equipment.allEquipment():
            key = f'{equipment.name}'
            cls.item_dict[key] = equipment

    def updItems(self) -> None:
        """ Изменение списка значений
            комбобокса в зависимости от типа
            (значения в соседнем комбобоксе) """

        items_to_add = []
        for key, equipment in self.__class__.item_dict.items():
            if equipment.name_short == self.cb_type.currentText():
                items_to_add.append(key)
        items_to_add = sorted(set(items_to_add))
        self.blockSignals(True)
        self.clear()
        self.addItems(items_to_add)
        self.blockSignals(False)

    @property
    def item(self) -> str:
        """ Возвращает экземпляр класса
            по значению комбобокса """

        return self.__class__.item_dict[self.currentText()]
