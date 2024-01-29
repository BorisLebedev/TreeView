""" Рамки окна выбора свойств
    (дополнительных столбцов)
    иерархической таблицы """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from STC.product.product import return_document_type
from STC.gui.windows.ancestors.frame import FrameBasic

if TYPE_CHECKING:
    from STC.product.product import Product
    from STC.gui.windows.hierarchy.model import HierarchicalView


class FrameSettings(FrameBasic):
    """ Родительский класс для рамок выбора опций """

    def __init__(self, frame_name: str, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name=frame_name)
        self.tree_model = tree_model
        self.setFrame()
        self.setTab()
        self.setPositions()

    def setFrame(self) -> None:
        """ Инициализация рамок дополнительных опций """

        self.frames = []

    def setTab(self) -> None:
        """ Инициализация меню переключения между рамками """

        self.tab = QTabWidget()
        for frame in self.frames:
            self.tab.addTab(frame, frame.name)

    def setPositions(self) -> None:
        """ Расположение виджетов рамки"""

        self.layout().addWidget(self.tab)


class FrameKDSettings(FrameSettings):
    """ Рамка отображения свойств КД иерархической
        таблицы (боковое меню вкладок) """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='КД',
                         tree_model=tree_model)

    def setFrame(self) -> None:
        """ Инициализация рамок дополнительных опций """

        self.main_settings = FrameMainSettingsKD(tree_model=self.tree_model)
        self.frames = [self.main_settings]


class FrameTDSettings(FrameSettings):
    """ Рамка отображения свойств ТД иерархической
        таблицы (боковое меню вкладок) """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='ТД',
                         tree_model=tree_model)

    def setFrame(self) -> None:
        """ Инициализация рамок дополнительных опций """

        self.main_settings = FrameMainSettingsTD(tree_model=self.tree_model)
        self.frames = [self.main_settings]


class FrameProductSettings(FrameSettings):
    """ Рамка отображения свойств изделия иерархической
        таблицы (боковое меню вкладок) """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='Изделие',
                         tree_model=tree_model)

    def setFrame(self) -> None:
        """ Инициализация рамок дополнительных опций """

        self.main_settings = FrameMainSettingsProduct(tree_model=self.tree_model)
        self.frames = [self.main_settings]


class FrameCheckboxSettings(FrameBasic):
    """ Родительская рамка отображения расположения
        элементов для свойств иерархической
        таблицы (верхнее меню вкладок) """

    def __init__(self, frame_name: str, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name=frame_name)
        self.tree_model = tree_model
        self.setSettings()
        self.widgetCheckbox()
        self.widgetPosition()
        self.readSettings()

    def setSettings(self) -> None:
        """ Создание словаря {наименование свойства: наименование аттрибута}
            по которому создаются элементы рамки и запрашиваются данные """

        self.settings = {}

    def widgetCheckbox(self) -> None:
        """ Создание чекбоксов по наименованиям
            и параметрам из self.settings """

        self.checkboxes = {}
        for setting_name, setting in self.settings.items():
            checkbox = QCheckBox(setting_name)
            self.checkboxes[setting] = checkbox
            checkbox.stateChanged.connect(self.addNewColumn)

    def widgetPosition(self) -> None:
        """ Расположение виджетов в рамке """

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
        """ Приведение в соответствие столбцов
            модели и чекбоксов настройки """

        for checkbox in self.checkboxes.values():
            checkbox.blockSignals(True)
            if self.header(checkbox) not in self.tree_model.header_horizontal:
                checkbox.setChecked(False)
            else:
                column = self.tree_model.header_horizontal.index(self.header(checkbox))
                checkbox.setChecked(not self.tree_model.isColumnHidden(column))
            checkbox.blockSignals(False)

    def header(self, checkbox: QCheckBox) -> str:
        """ Возвращает наименование столбца """

        return f'{checkbox.text()}'

    def addNewColumn(self) -> None:
        """ Вызывает метод добавления столбца в модель """

        data = self.generateData()
        self.tree_model.addNewColumn(data)

    def generateData(self) -> dict[str, str | bool | None | dict[Product, str]]:
        """ Запрашивает данные столбца для определенного свойства """

        setting = self.settings[self.sender().text()]
        data = {'type': 'product',
                'header': self.header(self.sender()),
                'setting': f'{setting}'}
        return data


class FrameMainSettings(FrameCheckboxSettings):
    """ Базовая рамка отображения расположения
        элементов для меню основных свойств """

    def __init__(self, document_class: str, tree_model: HierarchicalView):
        self.document_type = None
        self.document_class = document_class
        self.tree_model = tree_model
        self.widgetDocument(self.document_class)
        super().__init__(frame_name='Основные',
                         tree_model=tree_model)

    def widgetDocument(self, document_class: str):
        """ Виджет выбора вида документа из видов
            документов, которые есть в модели """

        self.doc_name = QLabel('Тип документа')
        self.doc_type = QComboBox()
        self.doc_type.addItems(self.cbValues(document_class))
        self.doc_type.setSizeAdjustPolicy(self.doc_type.AdjustToMinimumContentsLengthWithIcon)
        self.doc_type.setEditable(True)
        self.doc_type.currentTextChanged.connect(self.readSettings)
        self.documentType()

    def documentType(self) -> None:
        """ Определяет тип документа по наименованию и классу (КД/ТД) """

        self.document_type = \
            return_document_type(class_name=self.document_class,
                                 subtype_name=self.doc_type.currentText())

    def header(self, checkbox: QCheckBox) -> str:
        """ Возвращает наименования для столбцов модели """

        if self.document_type is None:
            return ''
        return f'{self.document_type.class_name}\n{self.document_type.sign}\n{checkbox.text()}'

    def addNewColumn(self) -> None:
        """ Вызывает метод добавления столбца в модель """

        if self.document_type is not None:
            data = self.generateData()
            self.tree_model.addNewColumn(data)

    def generateData(self) -> dict[str, str]:
        """ Запрашивает данные столбца для определенного свойства """

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
        """ Список наименований видов документов
            для комбобокса выбора вида документа """

        cb_values = [doc_type.subtype_name for doc_type in self.tree_model.document_types if
                     doc_type.class_name == document_class]
        return sorted(list(set(cb_values)))

    def widgetPosition(self) -> None:
        """ Расположение виджетов в рамке """

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
        """ Приведение в соответствие столбцов
            модели и чекбоксов настройки """

        self.documentType()
        for checkbox in self.checkboxes.values():
            checkbox.blockSignals(True)
            if self.header(checkbox) not in self.tree_model.header_horizontal:
                checkbox.setChecked(False)
            else:
                column = self.tree_model.header_horizontal.index(self.header(checkbox))
                checkbox.setChecked(not self.tree_model.isColumnHidden(column))
            checkbox.blockSignals(False)


class FrameMainSettingsKD(FrameMainSettings):
    """ Рамка для отображения свойств КД иерархической таблицы """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(document_class='КД',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        """ Создание словаря {наименование опции: наименование параметра}
            по которому создаются элементы рамки и запрашиваются данные """

        self.settings = {'Дата создания': 'date_created_str',
                         'Дата изменения': 'date_changed_str',
                         'Создал': 'name_created',
                         'Изменил': 'name_changed',
                         'Этап': 'stage',
                         'Наличие': 'sign'}


class FrameMainSettingsTD(FrameMainSettings):
    """ Рамка для отображения свойств ТД иерархической таблицы """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(document_class='ТД',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        """ Создание словаря {наименование свойства: наименование аттрибута}
            по которому создаются элементы рамки и запрашиваются данные """

        self.settings = {'Наименование': 'name',
                         'Обозначение': 'deno',
                         'Дата создания': 'date_created_str',
                         'Дата изменения': 'date_changed_str',
                         'Создал': 'name_created',
                         'Изменил': 'name_changed',
                         'Этап': 'stage',
                         'Наличие': 'sign'}


class FrameMainSettingsProduct(FrameCheckboxSettings):
    """ Рамка для отображения свойств
        изделия иерархической таблицы """

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__(frame_name='Изделие',
                         tree_model=tree_model)

    def setSettings(self) -> None:
        """ Создание словаря {наименование свойства: наименование аттрибута}
            по которому создаются элементы рамки и запрашиваются данные """

        self.settings = {'Первичная\nприменяемость': 'primary_product',
                         'Первичный\nпроект': 'primary_project',
                         # 'Проекты': 'all_projects',
                         # 'Документы\nв проектах': 'all_projects_with_doc',
                         'Дата последнего\nизменения': 'upd_date_f',
                         'Пользователь, внесший\n последнее изменение': 'upd_date_user',
                         'Актуальность\nиерархии': 'hierarchy_relevance',
                         'На сколько\nустарело': 'hierarchy_relevance_days',
                         'Вид': 'product_kind_name',
                         'Название\nпроекта': 'project_name'}
