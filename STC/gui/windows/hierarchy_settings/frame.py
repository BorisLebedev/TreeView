from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.product.product import Product
    from STC.gui.windows.hierarchy.model import HierarchicalView

from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from STC.product.product import return_document_type
from STC.gui.windows.ancestors.frame import FrameBasic


class FrameSettings(FrameBasic):

    def __init__(self, frame_name: str, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name=frame_name)
        self.tree_model = tree_model
        self.setFrame()
        self.setTab()
        self.setPositions()

    def setFrame(self) -> None:
        self.frames = []

    def setTab(self) -> None:
        self.tab = QTabWidget()
        for frame in self.frames:
            self.tab.addTab(frame, frame.name)

    def setPositions(self) -> None:
        self.layout().addWidget(self.tab)


# Рамка отображения свойств КД иерархической таблицы (боковое меню вкладок)
class FrameKDSettings(FrameSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='КД',tree_model=tree_model)

    def setFrame(self) -> None:
        self.main_settings = FrameMainSettingsKD(tree_model=self.tree_model)
        self.frames = [self.main_settings]


# Рамка отображения свойств ТД иерархической таблицы (боковое меню вкладок)
class FrameTDSettings(FrameSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='ТД',tree_model=tree_model)

    def setFrame(self) -> None:
        self.main_settings = FrameMainSettingsTD(tree_model=self.tree_model)
        self.frames = [self.main_settings]


# Рамка отображения свойств изделия иерархической таблицы (боковое меню вкладок)
class FrameProductSettings(FrameSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='Изделие',tree_model=tree_model)

    def setFrame(self) -> None:
        self.main_settings = FrameMainSettingsProduct(tree_model=self.tree_model)
        self.frames = [self.main_settings]


# Базовая рамка отображения расположения элементов для свойств иерархической таблицы (верхнее меню вкладок)
class FrameCheckboxSettings(FrameBasic):

    def __init__(self, frame_name: str, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name=frame_name)
        self.tree_model = tree_model
        self.setSettings()
        self.widgetCheckbox()
        self.widgetPosition()
        self.readSettings()

    def setSettings(self) -> None:
        self.settings = {}

    def widgetCheckbox(self) -> None:
        self.checkboxes = {}
        for setting_name, setting in self.settings.items():
            checkbox = QCheckBox(setting_name)
            self.checkboxes[setting] = checkbox
            checkbox.stateChanged.connect(self.addNewColumn)

    def widgetPosition(self) -> None:
        row = 0
        for counter, checkbox in enumerate(self.checkboxes.values()):
            if (counter % 2) == 0:
                col = 0
                row += 1
            else:
                col = 1
            self.main_layout.addWidget(checkbox, row, col, Qt.AlignLeft)
        self.main_layout.setRowStretch(row + 1, 1)

    def readSettings(self) -> None:
        for cb in self.checkboxes.values():
            cb.blockSignals(True)
            if self.header(cb) not in self.tree_model.headerHorizontal:
                cb.setChecked(False)
            else:
                column = self.tree_model.headerHorizontal.index(self.header(cb))
                cb.setChecked(not self.tree_model.isColumnHidden(column))
            cb.blockSignals(False)

    def header(self, cb: QCheckBox) -> str:
        return f'{cb.text()}'

    def addNewColumn(self) -> None:
        data = self.generateData()
        self.tree_model.addNewColumn(data)

    def generateData(self) -> dict[str, str | bool | None | dict[Product, str]]:
        setting = self.settings[self.sender().text()]
        data = {'type': 'product',
                'header': self.header(self.sender()),
                'setting': f'{setting}'}
        return data


# Базовая рамка отображения расположения элементов для меню основных свойств
class FrameMainSettings(FrameCheckboxSettings):

    def __init__(self, document_class: str, tree_model: HierarchicalView):
        self.document_class = document_class
        self.tree_model = tree_model
        self.widgetDocument(self.document_class)
        super().__init__(frame_name='Основные',
                         tree_model=tree_model)

    def widgetDocument(self, document_class: str):
        self.doc_name = QLabel('Тип документа')
        self.doc_type = QComboBox()
        self.doc_type.addItems(self.cbValues(document_class))
        self.doc_type.setSizeAdjustPolicy(self.doc_type.AdjustToMinimumContentsLengthWithIcon)
        self.doc_type.setEditable(True)
        self.doc_type.currentTextChanged.connect(self.readSettings)
        self.documentType()

    def documentType(self) -> None:
        self.document_type = return_document_type(class_name=self.document_class,
                                                  subtype_name=self.doc_type.currentText())

    def header(self, cb: QCheckBox) -> str:
        if self.document_type is None:
            return ''
        return f'{self.document_type.class_name}\n{self.document_type.sign}\n{cb.text()}'

    def addNewColumn(self) -> None:
        if self.document_type is not None:
            data = self.generateData()
            self.tree_model.addNewColumn(data)

    def generateData(self) -> dict[str, str]:
        setting = self.settings[self.sender().text()]
        data = {'type': 'document',
                'header': self.header(self.sender()),
                'class_name': self.document_type.class_name,
                'subtype_name': self.document_type.subtype_name,
                'organization_code': self.document_type.organization_code,
                'setting': f'{setting}',
                'sub_products': {},
                'only_relevant': True}
        return data

    def cbValues(self, document_class: str) -> list[str]:
        cb_values = [doc_type.subtype_name for doc_type in self.tree_model.document_types if
                     doc_type.class_name == document_class]
        return sorted(list(set(cb_values)))

    def widgetPosition(self) -> None:
        self.main_layout.addWidget(self.doc_name, 0, 0)
        self.main_layout.addWidget(self.doc_type, 0, 1)
        row = 1
        for counter, checkbox in enumerate(self.checkboxes.values()):
            if (counter % 2) == 0:
                col = 0
                row += 1
            else:
                col = 1
            self.main_layout.addWidget(checkbox, row, col, Qt.AlignLeft)
        self.main_layout.setRowStretch(row + 1, 1)

    def readSettings(self) -> None:
        self.documentType()
        for cb in self.checkboxes.values():
            cb.blockSignals(True)
            if self.header(cb) not in self.tree_model.headerHorizontal:
                cb.setChecked(False)
            else:
                column = self.tree_model.headerHorizontal.index(self.header(cb))
                cb.setChecked(not self.tree_model.isColumnHidden(column))
            cb.blockSignals(False)


# Рамка для отображения свойств КД иерархической таблицы
class FrameMainSettingsKD(FrameMainSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(document_class='КД',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        self.settings = {'Дата создания': 'date_created_str',
                         'Дата изменения': 'date_changed_str',
                         'Создал': 'name_created',
                         'Изменил': 'name_changed',
                         'Этап': 'stage',
                         'Наличие': 'sign'}


# Рамка для отображения свойств ТД  иерархической таблицы
class FrameMainSettingsTD(FrameMainSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(document_class='ТД',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        self.settings = {'Наименование': 'name',
                         'Обозначение': 'deno',
                         'Дата создания': 'date_created_str',
                         'Дата изменения': 'date_changed_str',
                         'Создал': 'name_created',
                         'Изменил': 'name_changed',
                         'Этап': 'stage',
                         'Наличие': 'sign'}


# Рамка для отображения свойств изделия иерархической таблицы
class FrameMainSettingsProduct(FrameCheckboxSettings):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='Изделие',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        self.settings = {'Первичный\nпроект': 'primary_product',
                         'Первичное\nизделие': 'primary_project',
                         'Проекты': 'all_projects',
                         'Документы\nв проектах': 'all_projects_with_doc',
                         'Дата последнего\nизменения': 'upd_date_f',
                         'Актуальность\nиерархии': 'hierarchy_relevance',
                         'Дней с\nпоследнего\nобновления': 'hierarchy_relevance_days',
                         'Вид': 'product_kind_name',
                         'Название\nпроекта': 'project_name'}
