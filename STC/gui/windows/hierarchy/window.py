from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.Qt import QModelIndex
    from PyQt5.Qt import QPoint
import sys

from PyQt5.Qt import QColor
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QAction

from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.hierarchy.context_menu import ContextMenuForTree
from STC.gui.windows.hierarchy.model import HierarchicalView
from STC.gui.windows.hierarchy.toolbar import ToolBarOptions
from STC.gui.windows.hierarchy.toolbar import ToolBarDocumentOptionsMain
from STC.gui.windows.hierarchy.toolbar import ToolBarDocumentOptions
from STC.gui.windows.hierarchy.toolbar import ToolBarProductOptions
from STC.gui.windows.hierarchy.toolbar import ToolBarHierarchyLevels
from STC.gui.windows.hierarchy.toolbar import ToolBarColors
from STC.gui.splash_screen import show_dialog

from STC.config.config import CONFIG


# Настройки иерархической таблицы
class SettingsWindowTable:

    def __init__(self, tree: HierarchicalView) -> None:
        self.updateSettings(tree)
        self.current_code = '1.'

    def updateSettings(self, tree: HierarchicalView) -> None:
        self.header_visibility, self.header_column = self.headerLabels(tree)
        self.expand_settings = self.getExpandSettings(tree)

    @staticmethod
    def headerLabels(tree: HierarchicalView) -> tuple[dict[str, bool], dict[int, str]]:
        header_visibility = {}
        header_column = {}
        header_labels = tree.headerHorizontal
        for label in header_labels:
            column = tree.header().visualIndex(tree.headerHorizontal.index(label))
            action = True if tree.isColumnHidden(column) else False
            header_visibility[label] = action
            header_column[column] = label
        return header_visibility, header_column

    @staticmethod
    def getExpandSettings(tree: HierarchicalView) -> dict[str, QModelIndex]:
        tree.getExpandSettings()
        return tree.expand_settings

    def setExpandSettings(self, tree: HierarchicalView) -> None:
        tree.blockSignals(True)
        tree.setAnimated(False)
        tree.expand_settings = self.expand_settings
        tree.setExpandSettings()
        tree.setAnimated(True)
        tree.modifyModelSettingsOnUpdate()
        tree.blockSignals(False)

    def setAdditionalColumns(self, tree: HierarchicalView) -> None:
        current_labels = tree.headerHorizontal
        for column in sorted(self.header_column.keys()):
            label = self.header_column[column]
            if label not in current_labels:
                tree.addNewColumn(data=self.column_settings[label]['data'],
                                  modify_settings=False)
                tree.setColumnHidden(column, self.header_visibility[label])
        tree.modifyModelSettingsOnUpdate()

    def getCurrentCode(self, tree: HierarchicalView) -> None:
        index = tree.customSelectedIndexes()
        if index:
            self.current_code = index.data()

    def setCurrentCode(self, tree: HierarchicalView) -> None:
        if self.current_code:
            try:
                index = tree.findTextInColumn(text=self.current_code)[0]
                index_main_start = index.siblingAtColumn(0)
                index_main_end = index.siblingAtColumn(tree.model.columnCount() - 1)
                tree.scrollTo(index_main_start)
                tree.selectionModel().select(
                    QItemSelection(index_main_start, index_main_end),
                    QItemSelectionModel.ClearAndSelect)
            except IndexError:
                self.current_code = ''
                self.setCurrentCode(tree=tree)

    def getColumnSettings(self, tree: HierarchicalView) -> None:
        self.column_settings = tree.column_settings


# Окно иерархической таблицы
class WindowTable(WindowBasic):
    closeChildWindows = pyqtSignal()

    """Главное окно с иерархической таблицей и интерфейсом управления"""
    showWindowSearch = pyqtSignal()
    showWindowFilter = pyqtSignal()
    showWindowProductSelector = pyqtSignal()
    showWindowNewDocument = pyqtSignal()
    showWindowDocumentSettings = pyqtSignal()
    showWindowCreateMk = pyqtSignal()
    showWindowAdminMk = pyqtSignal()
    showWindowAdminProduct = pyqtSignal()
    # showWindowAdminColorTheme = pyqtSignal()

    exportToExcel = pyqtSignal()
    exportToExcelNorm = pyqtSignal()
    exportToExcelNTD = pyqtSignal()
    assignKindSignal = pyqtSignal()
    updTreeView = pyqtSignal()
    syncTreeView = pyqtSignal()
    copyText = pyqtSignal()
    importExcelDb = pyqtSignal()


    def __init__(self, product_denotation: str, reverse: bool = False) -> None:
        super().__init__()
        self.reverse = reverse
        self.tree_view = HierarchicalView(product_denotation=product_denotation, reverse=self.reverse)
        self.mark_index = {}
        self.main_menu = None
        self.file_menu = None
        self.excel_menu = None
        self.action_import_db = None
        self.action_menu_product = None
        self.action_menu_mk = None
        self.admin_menu = None
        self.color_theme_menu = None
        self.context_menu = None
        self.toolbar_for_options = None
        self.toolbar_document_settings_main = None
        self.toolbar_document_settings = None
        self.toolbar_product_settings = None
        self.toolbar_for_hierarchy = None
        self.toolbar_for_colors = None
        self.header_labels = None
        self.current_context_menu_kttp = None
        self.current_context_menu_kind = None
        self.context_menu_kttp = self.tree_view.model.tree.kttp
        self.context_menu_kind = self.tree_view.model.tree.product_kinds
        self.main_product = self.tree_view.model.invisibleRootItem().child(0).data()
        self.InitUI()
        self.settings = SettingsWindowTable(self.tree_view)
        self.main_window.setCentralWidget(self.tree_view)
        self.setContextMenu()

    def InitUI(self) -> None:
        self.setWindowFlags(Qt.CustomizeWindowHint)
        title = self.main_product.name
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(title)
        self.setGeometry(100, 100, 640, 480)
        self.addToolBar()
        self.mainMenu()

    def mainMenu(self) -> None:
        self.main_menu = self.main_window.menuBar()
        self.fileMenu()
        self.excelMenu()
        self.adminMenu()

    def fileMenu(self) -> None:
        self.file_menu = self.main_menu.addMenu('Файл')
        self.file_menu.addAction(self.toolbar_for_options.action_dbsync)
        self.file_menu.addAction(self.toolbar_for_options.action_update)
        self.file_menu.addAction(self.toolbar_for_options.action_filter)
        self.file_menu.addAction(self.toolbar_for_options.action_newtab)
        self.file_menu.addAction(self.toolbar_for_options.action_newdoc)
        self.file_menu.addAction(self.toolbar_for_options.action_search)

    def excelMenu(self) -> None:
        self.excel_menu = self.main_menu.addMenu('Excel')
        self.action_import_db = self.actionImportExcelDb('Импорт из "База ТД"')
        self.excel_menu.addAction(self.action_import_db)
        self.excel_menu.addAction(self.toolbar_for_options.action_export)
        self.excel_menu.addAction(self.toolbar_for_options.action_export_norm)
        self.excel_menu.addAction(self.toolbar_for_options.action_export_ntd)

    def adminMenu(self) -> None:
        self.action_menu_product = self.actionAdminWindowProduct('Изделия')
        self.action_menu_mk = self.actionAdminWindow('Маршрутные карты')
        self.admin_menu = self.main_menu.addMenu('Администрирование')
        self.admin_menu.addAction(self.action_menu_mk)
        self.admin_menu.addAction(self.action_menu_product)
        self.colorThemeMenu()

    def colorThemeMenu(self):
        self.color_theme_menu = self.admin_menu.addMenu('Цветовая схема')
        for color_style in CONFIG.color_style.color_style_list:
            action = self.newAction(color_style)
            action.triggered.connect(self.changeColorStyle)
            self.color_theme_menu.addAction(action)

    def changeColorStyle(self):
        CONFIG.setCurrentStyle(style_name=self.sender().text())
        show_dialog(text='Внешний вид приложения измениться при следующем запуске')

    def setContextMenu(self) -> None:
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.showContextMenu)

    def showContextMenu(self, point: QPoint) -> None:
        self.context_menu = ContextMenuForTree(obj=self,
                                               kttp_list=self.context_menu_kttp,
                                               kind_list=self.context_menu_kind)
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    def addToolBar(self) -> None:
        self.toolbar_for_options = ToolBarOptions(self)
        self.toolbar_document_settings_main = ToolBarDocumentOptionsMain(window_table=self)
        self.toolbar_document_settings = ToolBarDocumentOptions(window_table=self)
        self.toolbar_product_settings = ToolBarProductOptions(window_table=self)
        self.toolbar_for_hierarchy = ToolBarHierarchyLevels(self)
        self.toolbar_for_colors = ToolBarColors(self)

        self.main_window.addToolBar(Qt.LeftToolBarArea, self.toolbar_for_options)
        self.main_window.addToolBar(Qt.TopToolBarArea, self.toolbar_document_settings_main)
        self.main_window.addToolBar(Qt.RightToolBarArea, self.toolbar_document_settings)
        self.main_window.addToolBar(Qt.TopToolBarArea, self.toolbar_product_settings)
        self.main_window.addToolBar(Qt.LeftToolBarArea, self.toolbar_for_hierarchy)
        self.main_window.addToolBar(Qt.LeftToolBarArea, self.toolbar_for_colors)

    def newAction(self, name: str) -> QAction:
        action = QAction(self.main_window)
        action.setText(name)
        return action

    def actionAdminWindow(self, name: str) -> QAction:
        action = self.newAction(name)
        action.triggered.connect(self.showWindowAdminMk)
        return action

    def actionAdminWindowProduct(self, name: str) -> QAction:
        action = self.newAction(name)
        action.triggered.connect(self.showWindowAdminProduct)
        return action

    def actionImportExcelDb(self, name: str) -> QAction:
        action = self.newAction(name)
        action.triggered.connect(lambda: self.importExcelDb.emit())
        return action

    def updTreeModel(self, product_denotation: str) -> None:
        self.header_labels = self.tree_view.headerHorizontal
        self.settings = SettingsWindowTable(self.tree_view)
        self.settings.getCurrentCode(self.tree_view)
        self.settings.getColumnSettings(self.tree_view)
        self.tree_view = HierarchicalView(product_denotation=product_denotation, reverse=self.reverse)
        self.main_window.setCentralWidget(self.tree_view)
        self.settings.setAdditionalColumns(self.tree_view)
        self.settings.setExpandSettings(self.tree_view)
        self.settings.setCurrentCode(self.tree_view)
        self.setContextMenu()
        self.toolbar_for_hierarchy.upd()
        self.colorizeTree()

    def setKind(self) -> None:
        self.current_context_menu_kind = self.context_menu_kind[self.sender().text()]
        self.assignKindSignal.emit()
        self.tree_view.redrawColumn(data={'type': 'product',
                                          'header': 'Вид',
                                          'setting': 'product_kind_name'})

    def setColor(self) -> None:
        color = QColor(self.sender().icon().pixmap(16, 16).toImage().pixelColor(0, 0))
        self.mark_index.update({self.tree_view.selectedProductIndex: color})
        self.colorizeTree()

    def colorizeTree(self) -> None:
        for index, color in self.mark_index.items():
            self.tree_view.setRowColor(mark_index=index, color=color)
