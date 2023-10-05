import logging
import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox

from STC.config.config import CONFIG
from STC.excel.xl_export.hierarchy import Excel
from STC.excel.xl_export.document import ExcelDocumentCreator
from STC.excel.xl_export.hierarchy import ExcelNorm
from STC.excel.xl_export.hierarchy import ExcelNTD
from STC.gui.splash_screen import SplashScreen
from STC.gui.splash_screen import show_dialog
from STC.gui.style import StyleFactory
from STC.gui.windows.config.window import WindowMkConfig
from STC.gui.windows.config.window import WindowProductConfig
from STC.gui.windows.document_add_new.window import WindowNewDocument
from STC.gui.windows.document_generator.window import WindowCreateMK
from STC.gui.windows.document_generator.window import WindowSelectorMk
from STC.gui.windows.hierarchy.window import WindowTable
from STC.gui.windows.hierarchy_filter.model import StandartModelFilter
from STC.gui.windows.hierarchy_filter.window import WindowFilter
from STC.gui.windows.hierarchy_find.model import StandartModelSearch
from STC.gui.windows.hierarchy_find.window import WindowSearchTreeView
from STC.gui.windows.hierarchy_settings.window import WindowDocumentSettings
from STC.gui.windows.product_selector.window import WindowProductSelector
from STC.product.document_from_form import DocumentFromForm
from STC.product.excel_import import ExcelDataFromTdDb
from STC.product.excel_import import ExcelSync
from STC.product.plm_import import PLMSync
from STC.product.product import Connection
from STC.product.product import Product
from STC.product.product import User
from STC.database.test_data_generator import generate_test_data


class Controller:
    connection = None
    controllers = []

    def __init__(self, proj_start=False) -> None:
        self.__class__.controllers.append(self)
        self.windows = []
        self.window_search_list = []
        self.window_filter_list = []
        self.table = None
        self.product_selector_window = None
        self.__class__.connection = connection
        if self.__class__.connection is None:
            self.__class__.connection = Connection()
        SplashScreen().closeWithWindow(window=self.product_selector_window)
        self.user = User(user_name=os.getlogin())
        if self.user.product is not None and proj_start:
            msg_box = show_dialog(text=f'Продолжить работу с {self.user.product.name}?',
                                  m_type='continue_project')
            if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.Yes:
                self.showMainTable(product_name=self.user.product.name,
                                   product_denotation=self.user.product.deno)
            if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.No:
                self.showProductSelector()
        else:
            self.showProductSelector()

    # Удаляет из списка окон
    def deleteFromWindows(self, windows_for_del: list) -> None:
        for window in windows_for_del:
            self.windows.remove(window)
        if not self.windows:
            self.__class__.controllers.remove(self)

    # Окно выбора изделия
    def showProductSelector(self) -> None:
        product_data = Product.getAllProductsInDict()
        if not product_data:
            msg_box = show_dialog(text=f'Нет данных об изделиях.\n'
                                      f'Сгенерировать тестовые данные?',
                                  m_type='continue_project')
            if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.Yes:
                generate_test_data()
            product_data = Product.getAllProductsInDict()
        self.product_selector_window = WindowProductSelector(product_data)
        self.windows.append(self.product_selector_window)
        self.product_selector_window.newDocumentWindow.connect(self.showNewDocumentWindow)
        self.product_selector_window.showMainTable.connect(self.showMainTable)
        self.product_selector_window.syncWithExcel.connect(self.syncWithExcel)
        self.product_selector_window.syncWithExcelTdDb.connect(self.syncWithExcelTdDb)
        self.product_selector_window.syncWithPLM.connect(self.syncWithPLM)
        self.product_selector_window.adminMK.connect(self.showWindowAdminMk)
        self.product_selector_window.closeWindow.connect(self.closeProductSelector)
        self.product_selector_window.show()
        self.product_selector_window.activateWindow()
        self.product_selector_window.raise_()

    # Закрытие окна выбора изделия
    def closeProductSelector(self) -> None:
        self.deleteFromWindows(windows_for_del=[self.product_selector_window])
        self.product_selector_window = None

    # Обновить комбобоксы в окне выбора изделия после ввода новых изделий
    def updProductSelector(self) -> None:
        self.product_selector_window.product_data = Product.getAllProductsInDict(upd=True)
        self.product_selector_window.initDefaultValues()

    # Окно отображения таблицы иерархии состава изделия
    def showMainTable(self, product_name=None, product_denotation=None) -> None:
        reverse = False
        if product_name is None and product_denotation is None:
            product_name = self.product_selector_window.cb_name.currentText()
            product_denotation = self.product_selector_window.cb_deno.currentText()
            reverse = self.product_selector_window.reverse
        if product_denotation != '' and product_name != '':
            SplashScreen().newMessage(message=f'Открытие таблицы {product_name} {product_denotation}',
                                      stage=0,
                                      stages=12,
                                      log=True,
                                      logging_level='INFO')
            self.table = WindowTable(product_denotation=product_denotation, reverse=reverse)
            self.windows.append(self.table)
            self.table.showWindowSearch.connect(self.showWindowSearch)
            self.table.showWindowFilter.connect(self.showWindowFilter)
            self.table.showWindowProductSelector.connect(lambda: Controller())
            self.table.showWindowNewDocument.connect(self.showNewDocumentWindow)
            self.table.showWindowCreateMk.connect(self.showSelectMkWindow)
            self.table.showWindowDocumentSettings.connect(self.showWindowDocumentSettings)
            self.table.exportToExcel.connect(lambda: Excel(self.table.tree_view))
            self.table.exportToExcelNorm.connect(lambda: ExcelNorm(self.table.tree_view))
            self.table.exportToExcelNTD.connect(lambda: ExcelNTD(self.table.tree_view))
            self.table.updTreeView.connect(lambda: self.updTreeView(load_from_db=False))
            self.table.syncTreeView.connect(lambda: self.updTreeView(load_from_db=True))
            self.table.copyText.connect(lambda: app.clipboard().setText(
                self.table.tree_view.model.data(self.table.tree_view.currentIndex())))
            self.table.importExcelDb.connect(self.syncWithExcelTdDb)
            self.table.assignKindSignal.connect(self.assignKind)
            self.table.closeWindow.connect(self.updUserSettings)
            self.table.closeWindow.connect(self.closeAllWindows)
            self.table.showWindowAdminMk.connect(self.showWindowAdminMk)
            self.table.showWindowAdminProduct.connect(self.showWindowAdminProduct)
            # self.table.showWindowAdminColorTheme.connect(self.showWindowAdminColorTheme)
            SplashScreen().newMessage(message=f'Открыта иерархия изделия {product_name} {product_denotation}',
                                      stage=8,
                                      stages=8,
                                      log=True,
                                      logging_level='INFO')
            SplashScreen().closeWithWindow(window=self.table)
            self.table.show()
            self.table.activateWindow()
            self.table.raise_()
            if self.product_selector_window is not None:
                self.product_selector_window.close()
        else:
            show_dialog(text='Не указаны децимальный номер и наименование')

    # Окно реквизитов документа
    def showNewDocumentWindow(self) -> None:
        try:
            product = self.table.tree_view.selected_product
        except AttributeError:
            product = None
            logging.warning('Ввод нового изделия')
        self.window_new_document = WindowNewDocument(product)
        self.windows.append(self.window_new_document)
        self.window_new_document.addDocument.connect(self.addNewDocument)
        self.window_new_document.closeWindow.connect(self.deleteFromWindows)
        self.window_new_document.show()

    # Окно выбора свойств документа
    def showWindowDocumentSettings(self) -> None:
        self.window_document_settings = WindowDocumentSettings(tree_model=self.table.tree_view)
        self.windows.append(self.window_document_settings)
        self.window_document_settings.closeWindow.connect(self.deleteFromWindows)
        self.window_document_settings.show()

    # Окно поиска
    def showWindowSearch(self) -> None:
        self.window_search = WindowSearchTreeView()
        self.window_search_list.append(self.window_search)
        self.windows.append(self.window_search)
        self.window_search.findData.connect(lambda: self.findData(window=self.window_search))
        self.window_search.closeWindow.connect(self.deleteFromSearchList)
        self.window_search.show()

    # Окно фильтра
    def showWindowFilter(self) -> None:
        model = StandartModelFilter(tree_view=self.table.tree_view)
        proxy = model.createProxy()
        self.window_filter = WindowFilter(model=proxy)
        self.window_filter_list.append(self.window_filter)
        self.windows.append(self.window_filter)
        self.window_filter.closeWindow.connect(self.deleteFromFilterList)
        self.window_filter.show()

    # Окно редактирования параметров по умолчанию для маршрутных карт
    def showWindowAdminMk(self) -> None:
        self.window_mk_config = WindowMkConfig()
        self.windows.append(self.window_mk_config)
        self.window_mk_config.closeWindow.connect(self.deleteFromWindows)
        self.window_mk_config.show()

    # Окно редактирования параметров по умолчанию для изделий
    def showWindowAdminProduct(self) -> None:
        self.window_product_config = WindowProductConfig()
        self.windows.append(self.window_product_config)
        self.window_product_config.closeWindow.connect(self.deleteFromWindows)
        self.window_product_config.show()

    # Удаляет окно из списка фильров
    def deleteFromFilterList(self, windows):
        self.window_filter_list.remove(windows[0])
        self.windows.remove(windows[0])

    # Удаляет окно из списка окон поиска
    def deleteFromSearchList(self, windows):
        self.window_search_list.remove(windows[0])
        self.windows.remove(windows[0])

    # Окно выбора маршрутной карты
    def showSelectMkWindow(self) -> None:
        try:
            product = self.table.tree_view.selected_product
        except AttributeError:
            product = None
            logging.warning('Изделие не определено')
        if product:
            self.selector_window = WindowSelectorMk(product)
            match len(self.selector_window.documents):
                case 1:
                    self.showCreateMkWindow()
                case 0:
                    show_dialog(text='Документ не найден', m_type='warning')
                case _:
                    self.windows.append(self.selector_window)
                    self.selector_window.closeWindow.connect(self.deleteFromWindows)
                    self.selector_window.documentChanged.connect(self.showCreateMkWindow)


    # Окно создания маршрутной карты
    def showCreateMkWindow(self) -> None:
        document_name = self.selector_window.selector.currentText()
        document = self.selector_window.documents[document_name]
        self.selector_window.close()
        window_create_mk = WindowCreateMK(document)
        window_create_mk.closeWindow.connect(self.deleteFromWindows)
        self.windows.append(window_create_mk)
        window_create_mk.exportToExcel.connect(ExcelDocumentCreator)
        window_create_mk.show()

    # Определяет вид изделия
    def assignKind(self) -> None:
        if self.table.current_context_menu_kind is not None:
            product = self.table.tree_view.selected_product
            product.product_kind = self.table.current_context_menu_kind
            pass

    # Обновление иерархической таблицы
    def updTreeView(self, load_from_db: bool = True) -> None:
        if load_from_db:
            self.__class__.connection.update()
        self.table.updTreeModel(product_denotation=self.table.main_product.deno)
        for window in self.window_search_list:
            self.findData(window)
        for window in self.window_filter_list:
            model = StandartModelFilter(tree_view=self.table.tree_view)
            proxy = model.createProxy()
            window.base_model = proxy
            window.table.setModel(proxy)
        SplashScreen().newMessage(message=f'Обновление завершено',
                                  stage=1,
                                  stages=1,
                                  log=True,
                                  logging_level='INFO')
        SplashScreen().closeWithWindow()

    # Импорт данных из иерархических таблиц Excel
    def syncWithExcel(self) -> None:
        msg_box = show_dialog(text='Сохранить структуру изделия?',
                              m_type='continue_project')
        upd = False
        if msg_box.standardButton(msg_box.clickedButton()) == QMessageBox.No:
            upd = True
        ExcelSync(upd=upd)
        self.updProductSelector()
        show_dialog(text='Импорт данных из иерархических таблиц Excel завершен', m_type='info')

    # Импорт данных из таблицы технологических документов
    def syncWithExcelTdDb(self) -> None:
        ExcelDataFromTdDb()
        if self.product_selector_window is not None:
            self.updProductSelector()
        if self.table in self.windows:
            self.updTreeView(load_from_db=False)

    # Импорт данных из системы PLM
    def syncWithPLM(self) -> None:
        PLMSync()
        if self.product_selector_window is not None:
            self.updProductSelector()

    # Добавление нового документа
    def addNewDocument(self) -> None:
        DocumentFromForm(self.window_new_document)
        self.window_new_document.close()
        if self.table in self.windows:
            self.updTreeView(load_from_db=False)
        if self.product_selector_window in self.windows:
            self.updProductSelector()

    # Поиск информации по таблице
    def findData(self, window: WindowSearchTreeView) -> None:
        text = window.line.text()
        model = StandartModelSearch(source_model=self.table.tree_view,
                                    search_text=text)
        window.showSearchResults(model)

    # Закрытие дочерних окон
    def closeAllWindows(self) -> None:
        windows = self.windows.copy()
        for window in windows:
            window.close()
        self.deleteFromWindows(windows_for_del=self.windows)

    # Обновить настройки пользователя после закрытия состава
    def updUserSettings(self):
        self.user.product = self.table.main_product


if __name__ == '__main__':
    global connection

    config_type = 'log'
    filename = CONFIG.data[config_type]['filename']
    logging_level = CONFIG.data[config_type]['logging_level']
    if logging_level == 'INFO':
        logging_level = logging.INFO
    elif logging_level == 'DEBUG':
        logging_level = logging.DEBUG
    elif logging_level == 'ERROR':
        logging_level = logging.ERROR
    else:
        logging_level = logging.INFO

    if filename:
        logging.basicConfig(level=logging_level,
                            format='%(asctime)s - %(levelname)s - %(message)s',
                            filename=filename)
    else:
        logging.basicConfig(level=logging_level,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    # logger = logging.getLogger()
    # sys.stderr = StreamToLogger(logger, logging.ERROR)
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    SplashScreen.app = app
    # style(app)
    StyleFactory(app=app)

    SplashScreen().newMessage(message=f'Инициализация списка изделий',
                              stage=0,
                              stages=26,
                              log=True,
                              logging_level='INFO')
    connection = Connection()

    SplashScreen().newMessage(message=f'Завершено',
                              stage=26,
                              stages=26,
                              log=True,
                              logging_level='INFO')

    controller = Controller(proj_start=True)
    sys.exit(app.exec())


# TODO Медленная отрисовка формы ввода документа
# TODO Методы getData и getDocumentByType класса Product упростить
