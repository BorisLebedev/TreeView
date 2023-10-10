""" Окна создания """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtGui import QCloseEvent
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QPushButton
from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.document_generator.structure import StructureCreateMK
from STC.gui.splash_screen import show_dialog
from STC.gui.splash_screen import SplashScreen
from STC.product.product import OperationBuilder

if TYPE_CHECKING:
    from STC.product.product import Document
    from STC.product.product import Operation
    from STC.product.product import Product


class WindowCreateMK(WindowBasic):
    """ Окно создания МК """

    exportToExcel = pyqtSignal(list)

    def __init__(self, document: Document) -> None:
        SplashScreen().newMessage(
            message='Инициализация окна создания маршрутной карты',
            stage=1,
            stages=4,
            log=True,
            logging_level='INFO')
        super().__init__()
        self.title = f'{document.subtype_name} ' \
                     f'{document.product.deno} ' \
                     f'({document.deno}) ' \
                     f'{document.name}'
        self.structure = None
        self.apply_btn = None
        self.excel_btn = None
        self.product = document.product
        self.document = document
        self.initUI()

    def initUI(self) -> None:
        """ Установка внешнего вида окна """

        SplashScreen().newMessage(
            message='Установка параметров окна создания маршрутной карты',
            stage=2,
            stages=4,
            log=True,
            logging_level='INFO')
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 1280, 720)
        self.initStructure()
        self.initApplyBtn()
        self.initExcelBtn()
        self.initDefaultData()
        SplashScreen().closeWithWindow()

    def initStructure(self) -> None:
        """ Инициализация структуры окна и реакций
            на изменение состояния виджетов """

        self.structure = StructureCreateMK(main_layout=self.main_layout)
        self.structure.main_data_frame.changeLitera.connect(self.changeLitera)
        self.structure.main_data_frame.changeStage.connect(self.changeStage)
        self.structure.main_data_frame.changeDeveloper.connect(self.changeDeveloper)
        self.structure.main_data_frame.changeChecker.connect(self.changeChecker)
        self.structure.main_data_frame.changeApprover.connect(self.changeApprover)
        self.structure.main_data_frame.changeNContr.connect(self.changeNContr)
        self.structure.main_data_frame.changeMContr.connect(self.changeMContr)
        self.structure.operations_frame.createNewOperation.connect(self.newOperation)
        self.structure.operations_frame.changeOperation.connect(self.updOperation)
        self.structure.operations_frame.deleleOperation.connect(self.delOperation)

    def initApplyBtn(self) -> None:
        """ Кнопка для сохранения МК """

        self.apply_btn = QPushButton('Сохранить')
        self.apply_btn.clicked.connect(self.createDocument)
        self.structure.btns_layout.addWidget(self.apply_btn)

    def initExcelBtn(self) -> None:
        """ Кнопка выгрузки МК в xls """

        self.excel_btn = QPushButton('Создать xls')
        self.excel_btn.clicked.connect(lambda: self.exportToExcel.emit([self.document]))
        self.structure.btns_layout.addWidget(self.excel_btn)

    def initDefaultData(self) -> None:
        """ Инициализация начальных данных """

        if self.product is not None:
            self.initDefaultProductData()
        if self.document is not None:
            self.initDefaultDocumentData()

    def initDefaultProductData(self) -> None:
        """ Заполняет виджеты с информацией об изделии """

        self.structure.main_data_frame.product_name = self.product.name
        self.structure.main_data_frame.product_deno = self.product.deno
        self.structure.main_data_frame.product_kind = self.product.product_kind_name_short
        self.structure.main_data_frame.product_type = self.product.product_type_name

    def initDefaultDocumentData(self) -> None:
        """ Заполняет виджеты аттрибутов документа для вкладки основных данных
            и создает вкладки как для редактирования каждой операции,
            так и редактирования перечня операций """

        SplashScreen().newMessage(message='Создание операций',
                                  stage=3,
                                  stages=4,
                                  log=True,
                                  logging_level='INFO')
        self.structure.main_data_frame.blockSignals(True)
        self.structure.main_data_frame.document_name = self.document.name
        self.structure.main_data_frame.document_deno = self.document.deno
        self.structure.main_data_frame.document_developer = self.document.name_developer
        self.structure.main_data_frame.document_checker = self.document.name_checker
        self.structure.main_data_frame.document_approver = self.document.name_approver
        self.structure.main_data_frame.document_n_contr = self.document.name_n_contr
        self.structure.main_data_frame.document_m_contr = self.document.name_m_contr
        self.structure.main_data_frame.document_litera = self.document.litera
        self.structure.main_data_frame.document_stage = self.document.stage
        self.structure.main_data_frame.blockSignals(False)
        indent = '  ' * 20
        SplashScreen().newMessage(message=f'{indent}Создание операций...Поиск операций',
                                  stage=3,
                                  stages=4,
                                  log=True,
                                  logging_level='INFO',
                                  align=Qt.AlignLeft)
        self.structure.operations_frame.document_main = self.document
        operations = self.document.operations_db
        self.document.operations = operations
        SplashScreen().newMessage(message=f'{indent}Создание операций...Найдено {len(operations)}',
                                  stage=3,
                                  stages=4,
                                  log=True,
                                  logging_level='INFO',
                                  align=Qt.AlignLeft)
        operations_num = len(operations)
        SplashScreen().changeSubProgressBar(stage=0,
                                            stages=operations_num)
        if operations:
            # enumerate, т.к. случается ошибка с нумерацией не с 0
            num = 0
            for order in sorted(operations.keys()):  # range(len(operations))
                diff = order - num
                # while num < order:
                #     self.newOperation()
                #     num += 1
                SplashScreen().changeSubProgressBar(stage=order,
                                                    stages=operations_num)
                operation = operations[order]
                if diff != 0:
                    operation.order = order - diff
                SplashScreen().newMessage(
                    message=f'{indent}Создание операций...'
                            f'{operation.num} {operation.name}',
                    stage=3,
                    stages=4,
                    log=True,
                    logging_level='INFO',
                    align=Qt.AlignLeft)
                self.newOperation(operation=operation)
                num += 1
        else:
            self.newOperation()

    def newOperation(self, operation: Operation | None = None) -> None:
        """ Создает рамку для редактирования операции
            и кнопку для переключения на эту рамку """

        self.structure.operations_frame.addOperationButtonClicked(operation=operation)
        self.structure.newOperation(document=self.document)

    def updOperation(self) -> None:
        """ Обновляет рамку операции удаляя старую
            и инициализируя новую """

        self.newOperation()
        self.delOperation()

    def delOperation(self) -> None:
        """ Вызывает метод удаления операции в случае,
            если операция не единственная """

        if self.structure.operations_frame.table.rowCount() > 1:
            self.structure.operations_frame.delOperationButtonClicked()
            self.structure.delOperation()
        else:
            show_dialog('Последнюю операцию удалить невозможно.')

    def createDocument(self) -> None:
        """ Вызывает метод создания документа """

        self.document.createMk()

    def changeStage(self) -> None:
        """ Изменить этап разработки документа """

        if self.document is not None:
            self.document.stage = self.structure.main_data_frame.document_stage

    def changeLitera(self) -> None:
        """ Изменить литеру документа """

        if self.document is not None:
            self.document.litera = self.structure.main_data_frame.document_litera

    def changeDeveloper(self) -> None:
        """ Изменить ФИО разработчика документа """

        if self.document is not None:
            self.document.name_developer = self.structure.main_data_frame.document_developer

    def changeChecker(self) -> None:
        """ Изменить ФИО проверяющего """

        if self.document is not None:
            self.document.name_checker = self.structure.main_data_frame.document_checker

    def changeApprover(self) -> None:
        """ Изменить ФИО утверждающего """

        if self.document is not None:
            self.document.name_approver = self.structure.main_data_frame.document_approver

    def changeNContr(self) -> None:
        """ Изменить ФИО нормоконтролера """

        if self.document is not None:
            self.document.name_n_contr = self.structure.main_data_frame.document_n_contr

    def changeMContr(self) -> None:
        """ Изменить ФИО метролога """

        if self.document is not None:
            self.document.name_m_contr = self.structure.main_data_frame.document_m_contr

    def closeEvent(self, event: QCloseEvent) -> None:
        """ Событие закрытия окна """

        if self.document is not None:
            OperationBuilder.cleanOperationByDocument(document=self.document)
        self.closeWindow.emit([self])


class WindowSelectorMk(WindowBasic):
    """ Окно выбора МК """

    documentChanged = pyqtSignal()

    def __init__(self, product: Product) -> None:
        super().__init__()
        self.product = product
        self.documents = self.findDocuments()
        if self.documents:
            self.initUI()
            self.show()
        else:
            self.close()

    def initUI(self) -> None:
        """ Инициализация виджета окна """

        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText("Выбор документа")
        self.basic_layout.itemAt(0).widget().layout.itemAt(1).widget().setHidden(True)
        self.basic_layout.itemAt(0).widget().layout.itemAt(2).widget().setHidden(True)
        self.setGeometry(100, 100, 180, 180)
        self.setMinimumSize(180, 180)
        self.selector = QComboBox()
        self.approve = QPushButton('Выбрать')
        self.discard = QPushButton('Отмена')
        self.approve.clicked.connect(self.documentChanged)
        self.discard.clicked.connect(self.close)
        self.selector.addItems(self.documents.keys())
        self.main_layout.addWidget(self.selector, 0, 0)
        self.main_layout.addWidget(self.approve, 1, 0)
        self.main_layout.addWidget(self.discard, 2, 0)

    def findDocuments(self) -> dict[str, Document]:
        """ Поиск документов """

        documents = []
        td_names = ['Маршрутная карта']
        for name in td_names:
            documents = self.product.getDocumentByType(
                class_name='ТД',
                subtype_name=name,
                only_relevant=True,
                only_text=False)
        return self.convertToDict(documents=documents)

    @staticmethod
    def convertToDict(documents: list[Document]) -> dict[str, Document]:
        """ Возвращает словарь {децимальный номер: документ} """

        result = {}
        for document in documents:
            result.update({document.deno: document})
        return result
