""" Тулбары окна иерархической таблицы изделия """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.Qt import QColor
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QToolBar

from STC.config.config import CONFIG

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy.window import WindowTable


class ToolBar(QToolBar):
    """ Базовый тулбар """

    def __init__(self, window_table: WindowTable, title: str = 'toolbar') -> None:
        super().__init__(title)
        self.window_table = window_table
        self.initActions()

    def initActions(self):
        """ Родительский класс инициализации QAction """

    def actionNewColumn(self, name: str) -> QAction:
        """ Возвращает действие с определенным названием
            триггерящее добавление нового столбца к
            иерархической таблице """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(lambda: self.window_table.tree_view.addNewColumn(action.data()))
        return action


class ToolBarHierarchyLevels(ToolBar):
    """ Тулбар для уровней иерархии """

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Уровни')
        self.setStyleSheet(f"color: {CONFIG.style.toolbar_text_color}")

    def initActions(self) -> None:
        """ Добавляет действия по уровням иерархии """

        self.font = QFont(CONFIG.style.font,
                          CONFIG.style.font_size_toolbar, 1)
        self.getUniqueHierarchyLevels()
        for level in self.getUniqueHierarchyLevels():
            action = QAction(self.window_table.main_window)
            action.setText(str(level))
            action.setFont(self.font)
            action.setShortcut(QKeySequence(f"Ctrl+{level}"))
            action.triggered.connect(
                lambda: self.window_table.tree_view.customSetExpandToLevel(
                    self.window_table.sender().text()))
            self.addAction(action)

    def getUniqueHierarchyLevels(self) -> list:
        """ Возвращает список уровней входимости
            иерархического древа """

        tree_dicts = self.window_table.tree_view.model.tree.tree_dicts
        all_levels = [branch.level for branch in tree_dicts]
        return sorted(set(all_levels))

    def upd(self) -> None:
        """ Обновить тулбар (количество уровней может изменяться) """

        self.clear()
        self.initActions()


class ToolBarColors(ToolBar):
    """ Тулбар с цветом выделения строк """

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Цвета')
        self.setStyleSheet(f"color: {CONFIG.style.toolbar_text_color}")

    def initActions(self) -> None:
        """ Добавления действий в тулбар """

        colors = {'red': {'color': QColor(200, 0, 0, 200),
                          'shortcut': 'Shift+R'},
                  'green': {'color': QColor(0, 200, 0, 200),
                            'shortcut': 'Shift+G'},
                  'blue': {'color': QColor(0, 0, 200, 200),
                           'shortcut': 'Shift+B'},
                  'basic': {'color': QColor(0, 0, 0, 0),
                            'shortcut': 'Shift+T'}}
        for color_dict in colors.values():
            pixmap = QPixmap(16, 16)
            pixmap.fill(color_dict['color'])
            action = QAction(self.window_table.main_window)
            action.setShortcut(QKeySequence(color_dict['shortcut']))
            action.setIcon(QIcon(pixmap))
            action.triggered.connect(self.window_table.setColor)
            self.addAction(action)


class ToolBarOptions(ToolBar):
    """ Тулбар управления приложением """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Управление составом')

    def initActions(self):
        """ Добавление действий в тулбар """

        self.action_dbsync = self.actionSyncTreeView('Обновить')
        self.action_dbsync.setIcon(CONFIG.style.arrow_repeat)
        self.action_dbsync.setShortcut(QKeySequence("F5"))
        self.addAction(self.action_dbsync)

        # self.action_update = self.actionUpdTreeView('Обновить')
        # self.action_update.setIcon(CONFIG.style.arrow_repeat)
        # self.action_update.setShortcut(QKeySequence("F5"))
        # self.addAction(self.action_update)

        self.action_filter = self.actionShowWindowFilter('Фильтр')
        self.action_filter.setIcon(CONFIG.style.filter)
        self.action_filter.setShortcut(QKeySequence("Ctrl+Shift+F"))
        self.addAction(self.action_filter)

        self.action_newtab = self.actionShowProductSelector('Новый состав')
        self.action_newtab.setIcon(CONFIG.style.network_3_round)
        self.action_newtab.setShortcut(QKeySequence("Ctrl+N"))
        self.addAction(self.action_newtab)

        self.action_newdoc = self.actionNewDocumentWindow('Новый документ')
        self.action_newdoc.setIcon(CONFIG.style.file_plus)
        self.action_newdoc.setShortcut(QKeySequence("Ctrl+D"))
        self.addAction(self.action_newdoc)

        self.action_search = self.actionShowWindowSearch('Поиск')
        self.action_search.setIcon(CONFIG.style.search_left)
        self.action_search.setShortcut(QKeySequence("Ctrl+F"))
        self.addAction(self.action_search)

        self.action_export = self.actionExportToExcel('Excel (Технология)')
        self.action_export.setIcon(CONFIG.style.file_arrow_down)
        # self.action_export.setShortcut(QKeySequence("Ctrl+E"))
        self.addAction(self.action_export)

        self.action_export_full = self.actionExportToExcelFull('Excel (Технология) Полная')
        self.action_export_full.setIcon(CONFIG.style.file_arrow_down_full)

        self.action_export_norm = self.actionExportToExcelNorm('Excel (Нормирование)')
        self.action_export_norm.setIcon(CONFIG.style.file_arrow_down_norm)
        # self.action_export_norm.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.addAction(self.action_export_norm)

        self.action_export_ntd = self.actionExportToExcelNTD('Excel (НТД)')
        self.action_export_ntd.setIcon(CONFIG.style.file_arrow_down_serv)
        # self.action_export_ntd.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.addAction(self.action_export_ntd)

    def actionSyncTreeView(self, name: str) -> QAction:
        """ "Полное" обновление иерархической таблицы
            с подгрузкой последних данных из БД """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.syncTreeView)
        return action

    def actionUpdTreeView(self, name: str) -> QAction:
        """ Обновление отображаемых в БД данных """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.updTreeView)
        return action

    def actionShowWindowFilter(self, name: str) -> QAction:
        """ Вывести окно фильтра """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.showWindowFilter)
        return action

    def actionShowProductSelector(self, name: str) -> QAction:
        """ Вывести окно открытия нового изделия """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.showWindowProductSelector)
        return action

    def actionNewDocumentWindow(self, name: str) -> QAction:
        """ Окно создания нового документа """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.showWindowNewDocument)
        return action

    def actionShowWindowSearch(self, name: str) -> QAction:
        """ Окно поиска в таблице """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.showWindowSearch)
        return action

    def actionExportToExcel(self, name: str) -> QAction:
        """ Экспорт данных в Excel (шаблон состава изделия) """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.exportToExcel)
        return action

    def actionExportToExcelFull(self, name: str) -> QAction:
        """ Экспорт данных в Excel (шаблон состава изделия)
            Выгрузка всех данных, а не только изделий с
            децимальным номером """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.exportToExcelFull)
        return action

    def actionExportToExcelNorm(self, name: str) -> QAction:
        """ Экспорт данных в Excel (шаблон нормирования) """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.exportToExcelNorm)
        return action

    def actionExportToExcelNTD(self, name: str) -> QAction:
        """ Экспорт данных в Excel (шаблон НТД) """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.exportToExcelNTD)
        return action


class ToolBarProductOptions(ToolBar):
    """ Тулбар управления свойствами изделий """

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Свойства изделий')

    def initActions(self):
        """ Инициализация действий тулбара """

        actions = [('Индекс', {'header': 'Индекс'}),
                   ('Вид\nизделия', {'type': 'product',
                                     'header': 'Вид',
                                     'setting': 'product_kind_name',
                                     'delegate': 'delegate_product_kind',
                                     }),
                   # ('Документы\nв проектах', {'type': 'product',
                   #                            'header': 'Документы\nв проектах',
                   #                            'setting': 'all_projects_with_doc',
                   #                            }),
                   ('Дата\nобновления', {'type': 'product',
                                         'header': 'Дата последнего\nизменения',
                                         'setting': 'upd_date',
                                         }),
                   ('Актуальность\nсостава', {'type': 'product',
                                              'header': 'Актуальность\nиерархии',
                                              'setting': 'hierarchy_relevance'}),
                   ('На сколько\nустарело', {'type': 'product',
                                             'header': 'Дней с\nпоследнего\nобновления',
                                             'setting': 'hierarchy_relevance_days'}),
                   ('Первичная\nприменяемость', {'type': 'product',
                                                 'header': 'Первичное\nизделие',
                                                 'setting': 'primary_product'}),
                   ('Первичный\nпроект', {'type': 'product',
                                          'header': 'Первичный\nпроект',
                                          'setting': 'primary_project'}),
                   ('Название\nпроекта', {'type': 'product',
                                          'header': 'Название\nпроекта',
                                          'setting': 'project_name'}),
                   ]
        for name, data in actions:
            action = self.actionNewColumn(name)
            action.setData(data)
            self.addAction(action)


class ToolBarDocumentOptions(ToolBar):
    """ Тулбар управления свойствами документов """

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Закладки')

    def initActions(self):
        """ Инициализация действий тулбара """

        actions = [('МК', {'type': 'document',
                           'header': 'ТД\nМК\nОбозначение',
                           'class_name': 'ТД',
                           'subtype_name': 'Маршрутная карта',
                           'setting': 'deno',
                           'sub_products': {},
                           'only_relevant': True,
                           }),
                   ('МК\n(этап)', {'type': 'document',
                                   'header': 'ТД\nМК\nЭтап',
                                   'class_name': 'ТД',
                                   'subtype_name': 'Маршрутная карта',
                                   'setting': 'stage',
                                   'sub_products': {},
                                   'only_relevant': True,
                                   }),
                   ('КТТП', {'type': 'document',
                             'header': 'ТД\nКТТП\nОбозначение',
                             'class_name': 'ТД',
                             'subtype_name': 'Карта типового (группового) '
                                             'технологического процесса',
                             'organization_code': '2',
                             'setting': 'deno',
                             'delegate': 'delegate_kttp',
                             'only_relevant': True,
                             }),
                   ('КГТП', {'type': 'document',
                             'header': 'ТД\nКГТП\nОбозначение',
                             'class_name': 'ТД',
                             'subtype_name': 'Карта типового (группового) '
                                             'технологического процесса',
                             'organization_code': '3',
                             'setting': 'deno',
                             'delegate': 'delegate_kttp',
                             'only_relevant': True,
                             }),
                   ('КТП', {'type': 'document',
                            'header': 'ТД\nКТП\nОбозначение',
                            'class_name': 'ТД',
                            'subtype_name': 'Карта технологического процесса',
                            'setting': 'deno',
                            'only_relevant': True,
                            }),
                   ('СП\n(дата)', {'type': 'document',
                                   'header': 'КД\nСП\nИзменено',
                                   'class_name': 'КД',
                                   'subtype_name': 'Спецификация',
                                   'setting': 'date_changed_str',
                                   'only_relevant': True,
                                   }),
                   ]
        for name, data in actions:
            action = self.actionNewColumn(name)
            action.setData(data)
            self.addAction(action)


class ToolBarDocumentOptionsMain(ToolBar):
    """ Тулбар расширенного управления свойствами изделий """

    def __init__(self, window_table: WindowTable) -> None:
        super().__init__(window_table=window_table, title='Документы')

    def initActions(self):
        """ Инициализация действий тулбара """

        action = self.actionAllDocumentTypes('Виды\nдокументов')
        self.addAction(action)

        action = self.actionDocumentSettings('Свойства\nдокументов')
        self.addAction(action)

    def actionDocumentSettings(self, name: str) -> QAction:
        """ Окно выбора свойств документов и изделий """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.window_table.showWindowDocumentSettings)
        return action

    def actionAllDocumentTypes(self, name: str) -> QAction:
        """ Дополняет таблицу столбцами видов документов """

        action = QAction(self.window_table.main_window)
        action.setText(name)
        action.triggered.connect(self.showAllDocTypes)
        return action

    def showAllDocTypes(self):
        """ Вызывает метод дополнения таблицы столбцами видов документов """

        self.window_table.tree_view.showAllDocumentTypes()
