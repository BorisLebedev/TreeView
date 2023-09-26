"""  """

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtWidgets import QComboBox
from STC.gui.splash_screen import show_dialog
from STC.gui.windows.ancestors.frame import FrameWithTable
from STC.gui.windows.config.context_menu import ContextMenuForFrameAdminDef
from STC.database.database import DbProduct
from STC.database.database import DbDocument
from STC.database.database import DbOperation
from STC.database.database import DbOperationDef
from STC.database.database import DbSetting
from STC.database.database import DbSettingDef
from STC.database.database import DbSentence
from STC.database.database import DbArea
from STC.database.database import DbWorkplace
from STC.database.database import DbIOT
from STC.gui.windows.document_generator.combobox import ComboBoxIotByName
from STC.database.database import DbIOTDef
from STC.database.database import DbMaterial
from STC.gui.windows.document_generator.combobox import ComboBoxMatByName
from STC.database.database import DbMaterialDef
from STC.database.database import DbRig
from STC.gui.windows.document_generator.combobox import ComboBoxRigByName
from STC.database.database import DbRigDef
from STC.database.database import DbEquipment
from STC.gui.windows.document_generator.combobox import ComboBoxEquipmentByName
from STC.database.database import DbEquipmentDef
from STC.database.database import DbDocumentType
from STC.database.database import DbDocDef
from STC.database.database import DbProfession
from STC.database.database import DbProductKind
from STC.database.database import DbPrimaryApplication
from STC.gui.windows.config.delegate import DelegatePlainText
from STC.gui.windows.config.delegate import DelegateComboBox
from STC.gui.windows.config.delegate import DelegateComboBoxRig
from STC.gui.windows.config.delegate import DelegateComboBoxIOT
from STC.gui.windows.config.delegate import DelegateComboBoxMat
from STC.gui.windows.config.delegate import DelegateComboBoxEqt
from STC.gui.windows.config.delegate import DelegateComboBoxSettings
from STC.gui.windows.config.delegate import DelegateComboBoxSentences
from STC.gui.windows.config.delegate import DelegateComboBoxOrder
from STC.gui.windows.config.delegate import DelegateComboBoxOperations
from STC.gui.windows.config.delegate import DelegateComboBoxArea
from STC.gui.windows.config.delegate import DelegateComboBoxWorkplace
from STC.gui.windows.config.delegate import DelegateComboBoxProfession
from STC.gui.windows.config.delegate import DelegateComboBoxProductKind
from STC.gui.windows.config.delegate import DelegateComboBoxDoc
from STC.gui.windows.config.delegate import DelegateComboBoxTTP
from STC.gui.windows.config.delegate import DelegateComboBoxPKI
from STC.product.product import ProductBuilder
from STC.product.product import DocumentBuilder
from STC.gui.splash_screen import SplashScreen
from STC.functions.func import deno_to_components


def upd_record_dialog():
    """ Сообщение об обновлении данных """

    show_dialog('Данные обновлены')


def new_record_dialog():
    """ Сообщение о внесении данных """

    show_dialog('Новые данные внесены')


def del_record_dialog():
    """ Сообщение об обновлении данных """

    show_dialog('Данные удалены')


def key_error(f):
    """  """

    def wrapper(*args, **kw):
        try:
            return f(*args, **kw)
        except KeyError:
            show_dialog('Попытка ввести данные, которых нет в списке.', 'ERROR')
    return wrapper


# class ComboBoxAdmin(QComboBox):
#     """  """
#
#     def __init__(self, items: list[str]) -> None:
#         super().__init__()
#         self.wheelEvent = lambda event: None
#         self.addItems(items)
#         self.setCurrentText(items[0])


class FrameAdmin(FrameWithTable):
    """ Родительский класс для рамок с таблицей окна
        ввода данных по умолчанию для маршрутных карт """

    newItem = pyqtSignal()
    new = '+'

    def __init__(self, frame_name, load_default: bool=True) -> None:
        super().__init__(frame_name=frame_name)
        if load_default:
            self.initDefaultData()
        self.table.setSortingEnabled(False)

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

    def showContextMenu(self, point: QPoint) -> None:
        """ Вызов контекстного меню """

        self.context_menu = ContextMenuForFrameAdminDef(self)
        qpoint = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qpoint)

    def copyRow(self):
        """ Копирование ниже активной строки таблицы """

        row = self.addRow()
        self.table.blockSignals(True)
        for column in range(self.table.columnCount()):
            self.table.setItem(row, column, QTableWidgetItem(self.table.item(row - 1, column)))
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.blockSignals(False)
        self.table.resizeRowToContents(row)

    def updTable(self):
        """ Удаление данных и загрузка данных по умолчанию """

        current_row = self.table.currentRow()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount(), -1, -1):
            self.table.removeRow(row - 1)
        self.initDefaultData()
        self.table.blockSignals(False)
        self.table.selectRow(current_row)

    def cellChanged(self) -> None:
        """ Реакция на изменение данных в ячейке таблицы """

    def addRow(self):
        """ Вставляет пустую строку ниже активной строки """

        row = self.table.currentRow()
        if row == -1:
            self.table.setRowCount(self.table.rowCount() + 1)
            return self.table.rowCount() - 1
        row += 1
        self.table.insertRow(row)
        return row

    def deleteRow(self) -> None:
        """ Удаление строки таблицы """

        show_dialog(text='Удаление данных не поддерживается')


class FrameAdminOperations(FrameAdmin):
    """ Рамка с таблицей операций """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 50, 'name': 'id'},
                                {'col': 1, 'width': 99, 'name': 'Операция'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbOperation.uniqueData()
        data = sorted(data, key=lambda x: x.name)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_operation))
            self.table.item(num, 1).setText(db_item.name)
        self.table.blockSignals(False)
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 1:
            row = item.row()
            id_operation = self.table.item(row, 0).text()
            if id_operation == self.__class__.new:
                db_operation = DbOperation.addNewOperation(name=item.text())
                self.table.item(row, 0).setText(str(db_operation.id_operation))
                new_record_dialog()
            else:
                DbOperation.updOperation(id_operation=int(self.table.item(item.row(), 0).text()),
                                         new_name=item.text())
                upd_record_dialog()
            self.newItem.emit()


class FrameAdminSentence(FrameAdmin):
    """ Рамка с таблицей переходов """

    newSentence = pyqtSignal()

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 99, 'name': 'Переход'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.delegate_sentence = DelegatePlainText()
        self.delegate_sentence.itemChanged.connect(self.itemChanged)
        self.table.setItemDelegateForColumn(1, self.delegate_sentence)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbSentence.uniqueData()
        data = sorted(data, key=lambda x: x.text)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_sentence))
            self.table.item(num, 1).setText(str(db_item.text))
            self.table.resizeRowToContents(num)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 1:
            row = item.row()
            id_sentence = self.table.item(row, 0).text()
            if id_sentence == self.__class__.new:
                if item.text() in DbSentence.data.keys():
                    show_dialog(f'Переход с введенным текстом уже существует')
                else:
                    db_sentence = DbSentence.addNewSentence(text=item.text())
                    self.table.item(row, 0).setText(str(db_sentence.id_sentence))
                    self.newSentence.emit()
                    new_record_dialog()
            else:
                DbSentence.updSentence(id_sentence=int(id_sentence),
                                       text=item.text())
                upd_record_dialog()
            self.newItem.emit()
            self.table.resizeRowToContents(row)


class FrameAdminArea(FrameAdmin):
    """ Рамка с таблицей участков """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 50, 'name': 'id'},
                                {'col': 1, 'width': 800, 'name': 'Наименование'},
                                {'col': 2, 'width': 150, 'name': 'Сокращение'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbArea.uniqueData()
        data = sorted(data, key=lambda x: x.id_area)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_area))
            self.table.item(num, 1).setText(db_item.name)
            self.table.item(num, 2).setText(db_item.name_short)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_area = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            name_short = self.table.item(row, 2).text()
            if name and name_short:
                if id_area == self.__class__.new:
                    db_area = DbArea.addNewArea(name=name,
                                                name_short=name_short)
                    self.table.item(row, 0).setText(str(db_area.id_area))
                    new_record_dialog()
                else:
                    DbArea.updArea(id_area=int(id_area),
                                   name=name,
                                   name_short=name_short)
                    upd_record_dialog()
                self.newItem.emit()


class FrameAdminWorkplace(FrameAdmin):
    """ Рамка с таблицей рабочих мест """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Наименование'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbWorkplace.uniqueData()
        data = sorted(data, key=lambda x: x.id_workplace)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_workplace))
            self.table.item(num, 1).setText(db_item.name)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 1:
            row = item.row()
            id_workplace = self.table.item(row, 0).text()
            if id_workplace == self.__class__.new:
                db_workplace = DbWorkplace.addNewWorkplace(name=item.text())
                self.table.item(row, 0).setText(str(db_workplace.id_workplace))
                new_record_dialog()
            else:
                DbWorkplace.updWorkplace(id_workplace=int(id_workplace),
                                         name=item.text())
                upd_record_dialog()
            self.newItem.emit()


class FrameAdminProfession(FrameAdmin):
    """ Рамка с таблицей профессий """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Профессия'},
                                {'col': 2, 'width': 300, 'name': 'Код'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbProfession.uniqueData()
        data = sorted(data, key=lambda x: x.name)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_profession))
            self.table.item(num, 1).setText(db_item.name)
            self.table.item(num, 2).setText(db_item.code)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_profession = self.table.item(row, 0).text()
            name = self.table.item(row, 1).text()
            code = self.table.item(row, 2).text()
            if name and code:
                if id_profession == self.__class__.new:
                    db_profession = DbProfession.addNewProfession(name=name,
                                                                  code=code)
                    self.table.item(row, 0).setText(str(db_profession.id_profession))
                    new_record_dialog()
                else:
                    DbProfession.updProfession(id_profession=int(id_profession),
                                               name=name,
                                               code=code)
                    upd_record_dialog()
                self.newItem.emit()


class FrameAdminIOT(FrameAdmin):
    """ Рамка с таблицей инструкций по охране труда (ИОТ) """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Сокращение (тип)'},
                                {'col': 2, 'width': 300, 'name': 'Сокращение (наим.)'},
                                {'col': 3, 'width': 300, 'name': 'Номер'},
                                {'col': 4, 'width': 300, 'name': 'Наименование'},
                                {'col': 5, 'width': 300, 'name': 'Тип'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))
        self.table.setItem(row, 4, QTableWidgetItem(''))
        self.table.setItem(row, 5, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbIOT.uniqueData()
        data = sorted(data, key=lambda x: x.name_short)
        data = sorted(data, key=lambda x: x.type_short)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_iot))
            self.table.item(num, 1).setText(db_item.type_short)
            self.table.item(num, 2).setText(db_item.name_short)
            self.table.item(num, 3).setText(db_item.deno)
            self.table.item(num, 4).setText(db_item.name)
            self.table.item(num, 5).setText(db_item.type)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_iot = self.table.item(row, 0).text()
            type_short = self.table.item(row, 1).text()
            name_short = self.table.item(row, 2).text()
            deno = self.table.item(row, 3).text()
            name = self.table.item(row, 4).text()
            type_long = self.table.item(row, 5).text()
            if type_short and name_short and deno and name and type_long:
                if id_iot == self.__class__.new:
                    db_iot = DbIOT.addNewIOT(type=type_long,
                                             type_short=type_short,
                                             deno=deno,
                                             name=name,
                                             name_short=name_short)
                    self.table.item(row, 0).setText(str(db_iot.id_iot))
                    new_record_dialog()
                else:
                    DbIOT.updIOT(id_iot=int(id_iot),
                                 type=type_long,
                                 type_short=type_short,
                                 deno=deno,
                                 name=name,
                                 name_short=name_short)
                    upd_record_dialog()
                ComboBoxIotByName.updItemDictCls()
                self.newItem.emit()


class FrameAdminDoc(FrameAdmin):
    """ Рамка с таблицей видов документов """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Класс'},
                                {'col': 2, 'width': 300, 'name': 'Подкласс'},
                                {'col': 3, 'width': 300, 'name': 'Тип'},
                                {'col': 4, 'width': 300, 'name': 'Наименование'},
                                {'col': 5, 'width': 300, 'name': 'Обозначение'},
                                {'col': 6, 'width': 300, 'name': 'Описание'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))
        self.table.setItem(row, 4, QTableWidgetItem(''))
        self.table.setItem(row, 5, QTableWidgetItem(''))
        self.table.setItem(row, 6, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbDocumentType.uniqueData()
        data = sorted(data, key=lambda x: x.type_name)
        data = sorted(data, key=lambda x: x.subclass_name)
        data = sorted(data, key=lambda x: x.class_name)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_type))
            self.table.item(num, 1).setText(db_item.class_name)
            self.table.item(num, 2).setText(db_item.subclass_name)
            self.table.item(num, 3).setText(db_item.type_name)
            self.table.item(num, 4).setText(db_item.subtype_name)
            self.table.item(num, 5).setText(db_item.sign)
            self.table.item(num, 6).setText(db_item.description)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_type = self.table.item(row, 0).text()
            class_name = self.table.item(row, 1).text()
            subclass_name = self.table.item(row, 2).text()
            type_name = self.table.item(row, 3).text()
            subtype_name = self.table.item(row, 4).text()
            sign = self.table.item(row, 5).text()
            description = self.table.item(row, 6).text()
            if id_type and class_name and subclass_name and type_name and subtype_name and sign:
                if id_type == self.__class__.new:
                    db_type = DbDocumentType.addNewDocumentType(class_name=class_name,
                                                                subclass_name=subclass_name,
                                                                type_name=type_name,
                                                                subtype_name=subtype_name,
                                                                sign=sign,
                                                                description=description)
                    self.table.item(row, 0).setText(str(db_type.id_type))
                    new_record_dialog()
                else:
                    DbDocumentType.updDocumentType(id_type=int(id_type),
                                                   class_name=class_name,
                                                   subclass_name=subclass_name,
                                                   type_name=type_name,
                                                   subtype_name=subtype_name,
                                                   sign=sign,
                                                   description=description)
                    upd_record_dialog()
                # ComboBoxIotByName.updItemDictCls()
                self.newItem.emit()


class FrameAdminMat(FrameAdmin):
    """ Рамка с таблицей материалов """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Вид'},
                                {'col': 2, 'width': 300, 'name': 'Тип'},
                                {'col': 3, 'width': 300, 'name': 'Наименование'},
                                {'col': 4, 'width': 300, 'name': 'Сокращение'},
                                {'col': 5, 'width': 300, 'name': 'Документ'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))
        self.table.setItem(row, 4, QTableWidgetItem(''))
        self.table.setItem(row, 5, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbMaterial.uniqueData()
        data = sorted(data, key=lambda x: x.mat_type)
        data = sorted(data, key=lambda x: x.kind)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_material))
            self.table.item(num, 1).setText(db_item.kind)
            self.table.item(num, 2).setText(db_item.mat_type)
            self.table.item(num, 3).setText(db_item.name)
            self.table.item(num, 4).setText(db_item.name_short)
            self.table.item(num, 5).setText(db_item.document)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_material = self.table.item(row, 0).text()
            kind = self.table.item(row, 1).text()
            mat_type = self.table.item(row, 2).text()
            name = self.table.item(row, 3).text()
            name_short = self.table.item(row, 4).text()
            document = self.table.item(row, 5).text()
            if kind and mat_type and name and name_short:
                if id_material == self.__class__.new:
                    db_material = DbMaterial.addNewMat(name=name,
                                                       mat_type=mat_type,
                                                       name_short=name_short,
                                                       document=document,
                                                       kind=kind)
                    self.table.item(row, 0).setText(str(db_material.id_material))
                    new_record_dialog()
                else:
                    DbMaterial.updMat(id_material=int(id_material),
                                      name=name,
                                      mat_type=mat_type,
                                      name_short=name_short,
                                      document=document,
                                      kind=kind)
                    upd_record_dialog()
                ComboBoxMatByName.updItemDictCls()
                self.newItem.emit()


class FrameAdminRig(FrameAdmin):
    """ Рамка с таблицей оснастки """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Вид'},
                                {'col': 2, 'width': 300, 'name': 'Тип'},
                                {'col': 3, 'width': 300, 'name': 'Наименование'},
                                {'col': 4, 'width': 300, 'name': 'Сокращение'},
                                {'col': 5, 'width': 300, 'name': 'Документ'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))
        self.table.setItem(row, 4, QTableWidgetItem(''))
        self.table.setItem(row, 5, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbRig.uniqueData()
        data = sorted(data, key=lambda x: x.rig_type)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_rig))
            self.table.item(num, 1).setText(db_item.kind)
            self.table.item(num, 2).setText(db_item.rig_type)
            self.table.item(num, 3).setText(db_item.name)
            self.table.item(num, 4).setText(db_item.name_short)
            self.table.item(num, 5).setText(db_item.document)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(1, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_rig = self.table.item(row, 0).text()
            kind = self.table.item(row, 1).text()
            rig_type = self.table.item(row, 2).text()
            name = self.table.item(row, 3).text()
            name_short = self.table.item(row, 4).text()
            document = self.table.item(row, 5).text()
            if rig_type and name and name_short:
                if id_rig == self.__class__.new:
                    db_rig = DbRig.addNewRig(kind=kind,
                                             rig_type=rig_type,
                                             name=name,
                                             name_short=name_short,
                                             document=document)
                    self.table.item(row, 0).setText(str(db_rig.id_rig))
                    new_record_dialog()
                else:
                    DbRig.updRig(id_rig=int(id_rig),
                                 kind=kind,
                                 rig_type=rig_type,
                                 name=name,
                                 name_short=name_short,
                                 document=document)
                    upd_record_dialog()
                ComboBoxRigByName.updItemDictCls()
                self.newItem.emit()


class FrameAdminEqt(FrameAdmin):
    """ Рамка с таблицей оборудования """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 300, 'name': 'Тип'},
                                {'col': 2, 'width': 300, 'name': 'Наименование'},
                                {'col': 3, 'width': 300, 'name': 'Сокращение (наим.)'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbEquipment.uniqueData()
        data = sorted(data, key=lambda x: x.type)
        self.table.blockSignals(True)
        for num, db_item in enumerate(data):
            self.addNewRow()
            self.table.item(num, 0).setText(str(db_item.id_equipment))
            self.table.item(num, 1).setText(db_item.type)
            self.table.item(num, 2).setText(db_item.name)
            self.table.item(num, 3).setText(db_item.name_short)
        self.table.blockSignals(False)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() != 0:
            row = item.row()
            id_equipment = self.table.item(row, 0).text()
            type = self.table.item(row, 1).text()
            name = self.table.item(row, 2).text()
            name_short = self.table.item(row, 3).text()
            if type and name and name_short:
                if id_equipment == self.__class__.new:
                    db_equipment = DbEquipment.addNewEquipment(name=name,
                                                               name_short=name_short,
                                                               type_name=type)
                    self.table.item(row, 0).setText(str(db_equipment.id_equipment))
                    new_record_dialog()
                else:
                    DbEquipment.updEquipment(id_equipment=int(id_equipment),
                                             name=name,
                                             name_short=name_short,
                                             type_name=type)
                    upd_record_dialog()
                ComboBoxEquipmentByName.updItemDictCls()
                self.newItem.emit()


class FrameAdminDef(FrameAdmin):
    """ Родительский класс для рамок с таблицами
        отношений двух сущностей типа переход -> свойство """

    def __init__(self, frame_name: str = 'Frame name', header: str = 'Наименование') -> None:
        self.header = header
        super().__init__(frame_name=frame_name)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 600, 'name': 'Переход'},
                                {'col': 2, 'width': 300, 'name': self.header},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.combobox_delegate_sentence = DelegateComboBoxSentences()
        self.combobox_delegate_sentence.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(1, self.combobox_delegate_sentence)

        self.combobox_delegate = self.initDelegate()
        self.combobox_delegate.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(2, self.combobox_delegate)

    def initDelegate(self) -> DelegateComboBox:
        """ Возвращает делегат в виде комбобокса """

        return DelegateComboBox()

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = []

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = []

    def getDefaultSentences(self):
        """ Список уникальных переходов для таблиц вида  """

        self.sentence = sorted([item.text for item in DbSentence.uniqueData()])

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        self.getDefaultData()
        # self.getDefaultItems()
        self.getDefaultSentences()
        for row, db_item in enumerate(self.data):
            self.initNewRow(row=row, db_item=db_item)
            self.initFlags(row=row)
        # self.table.setSortingEnabled(True)
        # self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def initFlags(self, row):
        """  """

        self.table.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def cbChanged(self):
        """  """

        row = self.table.currentRow()
        id_item = self.table.item(row, 0).text()
        sentence = self.table.item(row, 1).text()
        item = self.table.item(row, 2).text()
        if item and sentence:
            self.addData(row=row, id_item=id_item, item=item, sentence=sentence)

    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        pass

    def getText(self, source: dict, item: str, item_name: str) -> str:
        """  """

        if item in source.keys():
            return source[item]
        else:
            show_dialog(f'Не найден: {item}')
            return ""

    def deleteRow(self) -> None:
        """  """

        id_item = self.table.item(self.table.currentRow(), 0).text()
        if id_item != self.__class__.new:
            self.delItem(id_item=int(id_item))
        self.table.removeRow(self.table.currentRow())
        self.newItem.emit()

    def delItem(self, id_item):
        """  """

        show_dialog(text='Удаление данных из данной таблицы не поддерживается')


class FrameAdminIOTDef(FrameAdminDef):
    """ Рамка с таблицей связей ИОТ и переходов """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name, header='ИОТ')

    def initDelegate(self) -> DelegateComboBoxIOT:
        """  """

        return DelegateComboBoxIOT()

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_iot_def)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.iot.deno))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    @key_error
    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        id_iot = DbIOT.data[item].id_iot
        id_sentence = DbSentence.data[sentence].id_sentence
        if id_item == self.__class__.new:
            db_iot_def = DbIOTDef.addNewIOTDef(id_sentence=int(id_sentence),
                                               id_iot=int(id_iot))
            self.table.item(row, 0).setText(str(db_iot_def.id_iot_def))
            new_record_dialog()
        else:
            DbIOTDef.updIOTDef(id_iot_def=int(id_item),
                               id_sentence=int(id_sentence),
                               id_iot=int(id_iot))
            upd_record_dialog()

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbIOTDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence.text)
        # self.data = sorted(self.data, key=lambda x: x.id_sentence)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = sorted([item.deno for item in DbIOT.uniqueData()])

    def delItem(self, id_item):
        """  """

        DbIOTDef.delIOTDef(id_iot_def=id_item)
        del_record_dialog()


class FrameAdminMatDef(FrameAdminDef):
    """ Рамка с таблицей связей материалов и переходов """


    def __init__(self, frame_name: str = 'Frame name') -> None:
        """  """

        super().__init__(frame_name=frame_name, header='Материал')

    def initDelegate(self) -> DelegateComboBoxMat:
        """  """

        return DelegateComboBoxMat()

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_material_def)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.material.name))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    @key_error
    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        id_material = DbMaterial.data[item].id_material
        id_sentence = DbSentence.data[sentence].id_sentence
        if id_item == self.__class__.new:
            db_mat_def = DbMaterialDef.addNewMatDef(id_sentence=int(id_sentence),
                                                    id_material=int(id_material))
            self.table.item(row, 0).setText(str(db_mat_def.id_material_def))
            new_record_dialog()
        else:
            DbMaterialDef.updMatDef(id_material_def=int(id_item),
                                    id_sentence=int(id_sentence),
                                    id_material=int(id_material))
            upd_record_dialog()

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbMaterialDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence.text)
        # self.data = sorted(self.data, key=lambda x: x.id_sentence)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = sorted([item.name for item in DbMaterial.uniqueData()])

    def delItem(self, id_item):
        """  """

        DbMaterialDef.delMatDef(id_material_def=id_item)
        del_record_dialog()


class FrameAdminRigDef(FrameAdminDef):
    """ Рамка с таблицей связей оснастки и переходов """


    def __init__(self, frame_name: str = 'Frame name') -> None:
        """  """

        super().__init__(frame_name=frame_name, header='Оснастка')

    def initDelegate(self) -> DelegateComboBoxRig:
        """  """

        return DelegateComboBoxRig()

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_rig_def)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.rig.name))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    @key_error
    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        id_rig = DbRig.data[item].id_rig
        id_sentence = DbSentence.data[sentence].id_sentence
        if id_item == self.__class__.new:
            db_rig_def = DbRigDef.addNewRigDef(id_sentence=int(id_sentence),
                                               id_rig=int(id_rig))
            self.table.item(row, 0).setText(str(db_rig_def.id_rig_def))
            new_record_dialog()
        else:
            DbRigDef.updRigDef(id_rig_def=int(id_item),
                               id_sentence=int(id_sentence),
                               id_rig=int(id_rig))
            upd_record_dialog()

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbRigDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence.text)
        # self.data = sorted(self.data, key=lambda x: x.id_sentence)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = sorted([item.name for item in DbRig.uniqueData()])

    def delItem(self, id_item):
        """  """

        DbRigDef.delRigDef(id_rig_def=id_item)
        del_record_dialog()


class FrameAdminEqtDef(FrameAdminDef):
    """ Рамка с таблицей связей оборудования и переходов """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        """  """

        super().__init__(frame_name=frame_name, header='Оборудование')

    def initDelegate(self) -> DelegateComboBoxEqt:
        """  """

        return DelegateComboBoxEqt()

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_equipment_def)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.equipment.name))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    @key_error
    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        id_equipment = DbEquipment.data[item].id_equipment
        id_sentence = DbSentence.data[sentence].id_sentence
        if id_item == self.__class__.new:
            db_equipment_def = DbEquipmentDef.addNewEqtDef(id_sentence=int(id_sentence),
                                                           id_equipment=int(id_equipment))
            self.table.item(row, 0).setText(str(db_equipment_def.id_equipment_def))
            new_record_dialog()
        else:
            DbEquipmentDef.updEqtDef(id_equipment_def=int(id_item),
                                     id_sentence=int(id_sentence),
                                     id_equipment=int(id_equipment))
            upd_record_dialog()

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbEquipmentDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence.text)
        # self.data = sorted(self.data, key=lambda x: x.id_sentence)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = sorted([item.name for item in DbEquipment.uniqueData()])

    def delItem(self, id_item):
        """  """

        DbEquipmentDef.delEqtDef(id_equipment_def=id_item)
        del_record_dialog()


class FrameAdminDocDef(FrameAdminDef):
    """ Рамка с таблицей связей видами документов и переходами """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        """  """

        super().__init__(frame_name=frame_name, header='Вид документа')

    def initDelegate(self) -> DelegateComboBoxDoc:
        """  """

        return DelegateComboBoxDoc()

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_doc_def)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.document_type.subtype_name))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    @key_error
    def addData(self, row: int, id_item: str, item: str, sentence: str):
        """  """

        id_type = DbDocumentType.data[('КД', item)].id_type
        id_sentence = DbSentence.data[sentence].id_sentence
        if id_item == self.__class__.new:
            db_doc_def = DbDocDef.addNewDocDef(id_sentence=int(id_sentence),
                                               id_type=int(id_type))
            self.table.item(row, 0).setText(str(db_doc_def.id_doc_def))
            new_record_dialog()
        else:
            DbDocDef.updDocDef(id_doc_def=int(id_item),
                               id_sentence=int(id_sentence),
                               id_type=int(id_type))
            upd_record_dialog()

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbDocDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence.text)
        # self.data = sorted(self.data, key=lambda x: x.id_sentence)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.items = sorted([item.subtype_name for item in DbDocumentType.uniqueData()])

    def delItem(self, id_item):
        """  """

        DbDocDef.delDocDef(id_doc_def=id_item)
        del_record_dialog()


class FrameAdminSettingsDef(FrameAdminDef):
    """ Рамка с таблицей какие переходы соответствуют
        определенному свойству операции """


    def __init__(self, frame_name: str = 'Frame name') -> None:
        """  """

        super().__init__(frame_name=frame_name)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 50, 'name': 'id'},
                                # {'col': 1, 'width': 200, 'name': 'Операция'},
                                {'col': 1, 'width': 60, 'name': 'Порядок'},
                                {'col': 2, 'width': 200, 'name': 'Свойство'},
                                {'col': 3, 'width': 200, 'name': 'Переход'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.combobox_delegate_order = DelegateComboBoxOrder()
        self.combobox_delegate_order.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(1, self.combobox_delegate_order)

        self.combobox_delegate_settings = DelegateComboBoxSettings()
        self.combobox_delegate_settings.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(2, self.combobox_delegate_settings)

        self.combobox_delegate_sentences = DelegateComboBoxSentences()
        self.combobox_delegate_sentences.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(3, self.combobox_delegate_sentences)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.setItem(row, 3, QTableWidgetItem(''))

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        setting_with_operation = f'{db_item.setting.operation.name} - {db_item.setting.text}'
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_setting_def)))
        self.table.setItem(row, 1, QTableWidgetItem(str(db_item.sentence_order + 1)))
        self.table.setItem(row, 2, QTableWidgetItem(setting_with_operation))
        self.table.setItem(row, 3, QTableWidgetItem(db_item.sentence.text))
        self.table.resizeRowToContents(row)

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbSettingDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.sentence_order)
        self.data = sorted(self.data, key=lambda x: f'{x.setting.operation.name}\n{x.setting.text}')

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.setting = sorted([item.text for item in DbSetting.uniqueData()])

    @key_error
    def cbChanged(self) -> None:
        """  """

        row = self.table.currentRow()
        id_setting_def = self.table.item(row, 0).text()
        sentence_order = self.table.item(row, 1).text()
        setting_with_operation = self.table.item(row, 2).text()
        sentence = self.table.item(row, 3).text()
        if sentence_order and setting_with_operation and sentence:
            setting = setting_with_operation[setting_with_operation.find(' - ') + 3:]
            operation = setting_with_operation[:setting_with_operation.find(' - ')]
            id_setting = DbSetting.data[(operation, setting)].id_setting
            id_sentence = DbSentence.data[sentence].id_sentence
            if id_setting_def == self.__class__.new:
                db_setting_def = DbSettingDef.addNewSettingDef(id_setting=int(id_setting),
                                                               id_sentence=int(id_sentence),
                                                               sentence_order=int(sentence_order) - 1)
                self.table.item(row, 0).setText(str(db_setting_def.id_setting_def))
                new_record_dialog()
            else:
                DbSettingDef.updSettingDef(id_setting_def=int(id_setting_def),
                                           id_setting=int(id_setting),
                                           id_sentence=int(id_sentence),
                                           sentence_order=int(sentence_order) - 1)
                upd_record_dialog()
            self.newItem.emit()

    def initFlags(self, row):
        """  """

        self.table.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def delItem(self, id_item):
        """  """

        DbSettingDef.delSettingDef(id_setting_def=id_item)
        del_record_dialog()


class FrameAdminSettings(FrameAdminDef):
    """ Рамка с таблицей, отображающей свойства,
        соответствущие различным операциям """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)
        self.table.itemChanged.connect(self.itemChanged)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 20, 'name': 'id'},
                                {'col': 1, 'width': 150, 'name': 'Операция'},
                                {'col': 2, 'width': 150, 'name': 'Свойство'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.combobox_delegate = DelegateComboBoxOperations()
        self.combobox_delegate.itemChanged.connect(self.cbChanged)
        self.table.setItemDelegateForColumn(1, self.combobox_delegate)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.blockSignals(True)
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))
        self.table.blockSignals(False)

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_setting)))
        self.table.setItem(row, 1, QTableWidgetItem(str(db_item.operation.name)))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.text))
        self.table.resizeRowToContents(row)

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbSetting.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.text)
        self.data = sorted(self.data, key=lambda x: x.operation.name)

    # def getDefaultItems(self):
    #     """  """
    #
    #     self.operations = sorted([item.name for item in DbOperation.uniqueData()])

    def getDefaultSentences(self):
        """  """

    @key_error
    def cbChanged(self) -> None:
        """  """

        row = self.table.currentRow()
        id_setting = self.table.item(row, 0).text()
        operation = self.table.item(row, 1).text()
        text = self.table.item(row, 2).text()
        if operation and text:
            id_operation = DbOperation.data[operation].id_operation
            if id_setting == self.__class__.new:
                db_settings = DbSetting.addNewSetting(id_operation=id_operation,
                                                      text=text)
                self.table.item(row, 0).setText(str(db_settings.id_setting))
                new_record_dialog()
            else:
                DbSetting.updSetting(id_setting=int(id_setting),
                                     id_operation=id_operation,
                                     text=text)
                upd_record_dialog()
            self.newItem.emit()

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        row = item.row()
        id_setting = self.table.item(row, 0).text()
        operation = self.table.item(row, 1).text()
        text = self.table.item(row, 2).text()
        if operation and text:
            id_operation = DbOperation.data[operation].id_operation
            if id_setting == self.__class__.new:
                db_settings = DbSetting.addNewSetting(id_operation=id_operation,
                                                      text=text)
                self.table.item(row, 0).setText(str(db_settings.id_setting))
                new_record_dialog()
            else:
                DbSetting.updSetting(id_setting=int(id_setting),
                                     id_operation=id_operation,
                                     text=text)
                upd_record_dialog()
            self.newItem.emit()


class FrameAdminOperationsDef(FrameAdminDef):
    """ Рамка с таблицей возможных мест проведения и
        исполнителей различных операций """

    def __init__(self, frame_name: str = 'Frame name') -> None:
        super().__init__(frame_name=frame_name)

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 50, 'name': 'id'},
                                {'col': 1, 'width': 200, 'name': 'Операция'},
                                {'col': 2, 'width': 200, 'name': 'Участок'},
                                {'col': 3, 'width': 200, 'name': 'Рабочее место'},
                                {'col': 4, 'width': 100, 'name': 'Профессия'},
                                {'col': 5, 'width': 200, 'name': 'Вид изделия'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.combobox_delegate_oper = DelegateComboBoxOperations()
        self.combobox_delegate_area = DelegateComboBoxArea()
        self.combobox_delegate_work = DelegateComboBoxWorkplace()
        self.combobox_delegate_prof = DelegateComboBoxProfession()
        self.combobox_delegate_kind = DelegateComboBoxProductKind()

        self.combobox_delegate_oper.itemChanged.connect(self.cbChanged)
        self.combobox_delegate_area.itemChanged.connect(self.cbChanged)
        self.combobox_delegate_work.itemChanged.connect(self.cbChanged)
        self.combobox_delegate_prof.itemChanged.connect(self.cbChanged)
        self.combobox_delegate_kind.itemChanged.connect(self.cbChanged)

        self.table.setItemDelegateForColumn(1, self.combobox_delegate_oper)
        self.table.setItemDelegateForColumn(2, self.combobox_delegate_area)
        self.table.setItemDelegateForColumn(3, self.combobox_delegate_work)
        self.table.setItemDelegateForColumn(4, self.combobox_delegate_prof)
        self.table.setItemDelegateForColumn(5, self.combobox_delegate_kind)

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(self.__class__.new))
        # for col, items in enumerate([self.oper, self.area, self.work, self.prof, self.kind]):
        for col in range(4):
            self.table.setItem(row, col + 1, QTableWidgetItem(''))

    def initNewRow(self, row, db_item) -> None:
        """ Создание новой строки
            (родительский метод addRow + доп. функции для определенного класса) """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(str(db_item.id_operation_def)))
        self.table.setItem(row, 1, QTableWidgetItem(db_item.operation.name))
        self.table.setItem(row, 2, QTableWidgetItem(db_item.area.name))
        self.table.setItem(row, 3, QTableWidgetItem(db_item.workplace.name))
        self.table.setItem(row, 4, QTableWidgetItem(db_item.profession.name))
        self.table.setItem(row, 5, QTableWidgetItem(db_item.kind.name_short))
        self.table.resizeRowToContents(row)

    def getDefaultData(self):
        """ Получение и обработка данных из БД для
            метода инициализации начальных данных """

        self.data = DbOperationDef.uniqueData()
        self.data = sorted(self.data, key=lambda x: x.profession.name)
        self.data = sorted(self.data, key=lambda x: x.workplace.name)
        self.data = sorted(self.data, key=lambda x: x.area.name)
        self.data = sorted(self.data, key=lambda x: x.operation.name)

    # def getDefaultItems(self):
    #     """ Получение текущих уникальных значений для переменных данных таблицы """
    #     self.oper = sorted([item.name for item in DbOperation.uniqueData()])
    #     self.area = sorted([item.name for item in DbArea.uniqueData()])
    #     self.work = sorted([item.name for item in DbWorkplace.uniqueData()])
    #     self.prof = sorted([item.name for item in DbProfession.uniqueData()])
    #     self.kind = sorted([item.name_short for item in DbProductKind.uniqueData()])

    @key_error
    def cbChanged(self):
        """ Реакция на изменение комбобокса в таблице """

        row = self.table.currentRow()
        id_operation_def = self.table.item(row, 0).text()
        operation = self.table.item(row, 1).text()
        area = self.table.item(row, 2).text()
        workplace = self.table.item(row, 3).text()
        profession = self.table.item(row, 4).text()
        kind = self.table.item(row, 5).text()
        if operation and area and workplace and profession and kind:
            id_operation = DbOperation.data[operation].id_operation
            id_area = DbArea.data[area].id_area
            id_workplace = DbWorkplace.data[workplace].id_workplace
            id_profession = DbProfession.data[profession].id_profession
            id_kind = DbProductKind.data[kind].id_kind
            if id_operation_def == self.__class__.new:
                db_operation_def = DbOperationDef.addNewOperationDef(id_operation=int(id_operation),
                                                                     id_area=int(id_area),
                                                                     id_workplace=int(id_workplace),
                                                                     id_profession=int(id_profession),
                                                                     id_kind=int(id_kind))
                self.table.item(row, 0).setText(str(db_operation_def.id_operation_def))
                new_record_dialog()
            else:
                DbOperationDef.updOperationDef(id_operation_def=int(id_operation_def),
                                               id_operation=int(id_operation),
                                               id_area=int(id_area),
                                               id_workplace=int(id_workplace),
                                               id_profession=int(id_profession),
                                               id_kind=int(id_kind))
                upd_record_dialog()

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        self.getDefaultData()
        self.getDefaultItems()
        for row, db_item in enumerate(self.data):
            self.initNewRow(row=row, db_item=db_item)
            self.initFlags(row=row)
        # self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.setColumnHidden(0, True)

    def initFlags(self, row):
        """  """

        self.table.item(row, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def delItem(self, id_item):
        """  """

        DbOperationDef.delOperationDef(id_operation_def=id_item)
        del_record_dialog()


class FrameAdminTTPErr(FrameAdmin):
    """ Рамка с таблицей изделий которым присвоено
        более 1 типового технологического процесса """

    def __init__(self, frame_name):
        super(FrameAdminTTPErr, self).__init__(frame_name=frame_name,
                                               load_default=False)
        self.table.itemChanged.connect(self.itemChanged)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 400, 'name': 'Наименование'},
                                {'col': 1, 'width': 200, 'name': 'Децимальный\nномер'},
                                {'col': 2, 'width': 200, 'name': 'КТТП'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)
        # self.table.setSortingEnabled(True)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.delegate_sentence = DelegateComboBoxTTP()
        # self.delegate_sentence.itemChanged.connect(self.itemChanged)
        self.table.setItemDelegateForColumn(2, self.delegate_sentence)

    def addRow(self):
        """ Вставляет пустую строку ниже активной строки """

        row = self.table.currentRow()
        if row == -1:
            self.table.setRowCount(self.table.rowCount() + 1)
            return self.table.rowCount() - 1
        row += 1
        self.table.insertRow(row)
        return row

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(''))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbDocument.getErrorTTP()
        data = sorted(data.items(), key=lambda x: x[0].name)
        self.product_builder = ProductBuilder()
        self.document_builder = DocumentBuilder()
        self.table.blockSignals(True)
        for num, (db_product, db_documents) in enumerate(data):
            self.product_builder.getDbProductByDenotation(deno=db_product.deno)
            product = self.product_builder.product
            for db_document in db_documents:
                self.document_builder.setDbDocument(db_document)
                document = self.document_builder.document
                product.documents.add(document)
            ttp_doc = product.getDocumentByType(class_name='ТД',
                                                subtype_name='Карта типового (группового) технологического процесса',
                                                setting='deno',
                                                org_code='2',
                                                only_relevant=True)
            self.addNewRow()
            self.table.item(num, 0).setText(product.name)
            self.table.item(num, 1).setText(product.deno)
            self.table.item(num, 2).setText(ttp_doc)
        self.table.blockSignals(False)
        self.table.resizeRowsToContents()
        # self.table.resizeColumnsToContents()
        # self.table.setColumnHidden(0, True)

    def updTable(self):
        """ Удаление данных и загрузка данных по умолчанию """

        current_row = self.table.currentRow()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount(), -1, -1):
            self.table.removeRow(row - 1)
        self.initDefaultData()
        self.table.blockSignals(False)
        self.table.selectRow(current_row)
        self.table.horizontalHeader().setStretchLastSection(True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 2:
            row = item.row()
            db_document_real = self.delegate_sentence.db_documents_real.get(item.text(), None)
            if db_document_real is not None:
                deno = self.table.item(row, 1).text()
                self.product_builder.getDbProductByDenotation(deno=deno)
                product = self.product_builder.product
                product.updKttp(documents=[db_document_real])
            self.newItem.emit()


class FrameAdminPrimaryProduct(FrameAdmin):
    """ Рамка с таблицей изделий у которых
        не указана первичная применяемость """

    def __init__(self, frame_name):
        super(FrameAdminPrimaryProduct, self).__init__(frame_name=frame_name,
                                                       load_default=False)
        self.table.itemChanged.connect(self.itemChanged)
        # self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 400, 'name': 'Наименование'},
                                {'col': 1, 'width': 200, 'name': 'Децимальный\nномер'},
                                {'col': 2, 'width': 200, 'name': 'Первичная применяемость'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)


    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        data = DbProduct.getProductWithoutPrimaryApplication()
        data = sorted(data, key=lambda x: x.deno[4:])
        self.product_builder = ProductBuilder()
        self.table.blockSignals(True)
        SplashScreen().basicProceed('Загрузка изделий без первичной применяемости')
        SplashScreen().changeSubProgressBar(stage=0,
                                            stages=len(data))
        self.table.setRowCount(len(data))
        for num, db_product in enumerate(data):
            self.product_builder.getDbProductByDenotation(deno=db_product.deno)
            product = self.product_builder.product
            self.table.setItem(num, 0, QTableWidgetItem(product.name))
            self.table.setItem(num, 1, QTableWidgetItem(product.deno))
            self.table.setItem(num, 2, QTableWidgetItem(product.primary_product))
            SplashScreen().changeSubProgressBar()
        SplashScreen().close()
        self.table.blockSignals(False)
        self.table.resizeRowsToContents()

    def updTable(self):
        """ Удаление данных и загрузка данных по умолчанию """

        current_row = self.table.currentRow()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount(), -1, -1):
            self.table.removeRow(row - 1)
        self.initDefaultData()
        self.table.blockSignals(False)
        self.table.selectRow(current_row)
        self.table.horizontalHeader().setStretchLastSection(True)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 2:

            deno = item.text()
            code_org, code_class, num, ver = deno_to_components(deno)
            if code_org is None:
                show_dialog(f'Неправильный формат децимального номера')
            else:
                row = item.row()
                self.product_builder.getDbProductByDenotation(deno=self.table.item(row, 1).text())
                product = self.product_builder.product
                child = product.db_product
                parent = DbProduct.addDbProduct(deno=deno)
                DbPrimaryApplication.addDbPrimaryApplication(parent=parent,
                                                             child=child)
                show_dialog(f'{child.name} {child.deno }\n'
                           f'теперь первично применяется в \n'
                           f'{parent.name} {parent.deno}')



            # row = item.row()
            # db_document_real = self.delegate_sentence.db_documents_real.get(item.text(), None)
            # if db_document_real is not None:
            #     deno = self.table.item(row, 1).text()
            #     self.product_builder.getDbProductByDenotation(deno=deno)
            #     product = self.product_builder.product
            #     product.updKttp(documents=[db_document_real])
            # self.newItem.emit()


class FrameAdminProduct(FrameAdmin):
    """ Родительский класс рамок для покупных и изготавливаемых изделий """

    def __init__(self, frame_name):
        super(FrameAdminProduct, self).__init__(frame_name=frame_name,
                                                load_default=False)
        self.table.itemChanged.connect(self.itemChanged)
        self.initDelegateSettings()

    def initTableSettings(self) -> None:
        """ Начальные параметры таблицы """

        self.header_settings = ({'col': 0, 'width': 400, 'name': 'Наименование'},
                                {'col': 1, 'width': 200, 'name': 'Децимальный\nномер'},
                                {'col': 2, 'width': 200, 'name': 'ПКИ'},
                                )
        self.start_rows = 0
        self.start_cols = len(self.header_settings)
        # self.table.setSortingEnabled(True)

    def initDelegateSettings(self) -> None:
        """ Назначение делегата для определенных столбцов таблицы """

        self.delegate_sentence = DelegateComboBoxPKI()
        # self.delegate_sentence.itemChanged.connect(self.itemChanged)
        self.table.setItemDelegateForColumn(2, self.delegate_sentence)

    def addRow(self):
        """ Вставляет пустую строку ниже активной строки """

        row = self.table.currentRow()
        if row == -1:
            self.table.setRowCount(self.table.rowCount() + 1)
            return self.table.rowCount() - 1
        row += 1
        self.table.insertRow(row)
        return row

    def addNewRow(self) -> None:
        """ Добавление новой строки в таблицу """

        row = self.addRow()
        self.table.setItem(row, 0, QTableWidgetItem(''))
        self.table.setItem(row, 1, QTableWidgetItem(''))
        self.table.setItem(row, 2, QTableWidgetItem(''))

    def initDefaultData(self) -> None:
        """ Инициализация данных по умолчанию """

        row = 0
        data = DbProduct.data
        self.table.blockSignals(True)
        for db_product in data.values():
            if self.getProductToTable(db_product=db_product):
                self.addNewRow()
                self.setRowData(db_product=db_product, row=row)
                row += 1
        self.table.blockSignals(False)
        self.table.resizeRowsToContents()
        self.table.resizeColumnsToContents()
        # self.table.setColumnHidden(0, True)

    def setRowData(self, db_product, row):
        """  """

        self.table.item(row, 0).setText(str(db_product.name))
        if db_product.name != db_product.deno:
            self.table.item(row, 1).setText(str(db_product.deno))
        self.table.item(row, 2).setText(str(db_product.purchased))

    def getProductToTable(self, db_product: DbProduct) -> bool:
        """  """

        return True if db_product.purchased is not None else False

    def updTable(self):
        """ Удаление данных и загрузка данных по умолчанию """

        current_row = self.table.currentRow()
        self.table.blockSignals(True)
        for row in range(self.table.rowCount(), -1, -1):
            self.table.removeRow(row - 1)
        self.initDefaultData()
        self.table.blockSignals(False)
        self.table.selectRow(current_row)

    def itemChanged(self, item):
        """ Реакция на изменения данных таблицы """

        if item.text() and item.column() == 2:
            row = item.row()
            deno = self.table.item(row, 1)
            db_product = DbProduct.data[deno]
            DbProduct.addDbProduct(deno=db_product.deno,
                                   name=db_product.name,
                                   purchased=item.text())
            self.newItem.emit()


class FrameAdminProductPKI(FrameAdminProduct):
    """ Рамка с таблицей не изготавливаемых изделий с
        возможностью изменения типа изготовления """

    def __init__(self, frame_name) -> None:
        super(FrameAdminProductPKI, self).__init__(frame_name=frame_name)

    def getProductToTable(self, db_product: DbProduct) -> bool:
        """  """

        return False if db_product.purchased in [None, 0] else True


class FrameAdminProductSTC(FrameAdminProduct):
    """ Рамка с таблицей изготавливаемых изделий с
        возможностью изменения типа изготовления """

    def __init__(self, frame_name) -> None:
        super(FrameAdminProductSTC, self).__init__(frame_name=frame_name)

    def getProductToTable(self, db_product: DbProduct) -> bool:
        """  """

        return True if db_product.purchased in [None, 0] else False