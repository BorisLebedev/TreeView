""" Модель, представление и делегаты для иерархической таблицы """

from __future__ import annotations

from typing import TYPE_CHECKING

import datetime
import logging
from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDateTime
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QStyleOptionComboBox
from PyQt5.QtWidgets import QStyle
from PyQt5.QtWidgets import QTreeView
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QStylePainter
from PyQt5.QtWidgets import QComboBox
from STC.gui.splash_screen import SplashScreen
from STC.product.hierarchical_tree import HierarchicalTree
from STC.product.product import ProductKind
from STC.gui.splash_screen import show_dialog

if TYPE_CHECKING:
    from PyQt5.Qt import QModelIndex
    from PyQt5.Qt import QColor
    from PyQt5.Qt import QPaintEvent
    from PyQt5.Qt import QStyleOptionViewItem
    from PyQt5.Qt import QWidget
    from STC.product.product import Product


class HierarchicalModel(QStandardItemModel):
    """ Модель иерархического древа """

    updKttpSignal = pyqtSignal(list)
    addKttpSignal = pyqtSignal(list)
    delKttpSignal = pyqtSignal(list)
    updProductKindSignal = pyqtSignal(str)

    def __init__(self, product_denotation: str, reverse: bool = False) -> None:
        super().__init__()
        self.tree = HierarchicalTree(product_denotation, reverse)

    def updKttp(self, names: list) -> None:
        """ Посылает сигнал со списком типовых
            технологических процессов, выбирая
            их по их наименованиям """

        documents = []
        for name in names:
            documents.append(HierarchicalTree.kttp_deno_only[name])
        self.updKttpSignal.emit(documents)

    def addKttp(self):
        """ Посылает сигнал с типовым технологическим процессом
            (для привязки КТТП к изделию) """

        self.addKttpSignal.emit([HierarchicalTree.kttp[self.sender().text()]])

    def delKttp(self):
        """ Посылает сигнал с типовым технологическим процессом
            (для удаления связи КТТП и изделия) """

        self.delKttpSignal.emit([HierarchicalTree.kttp[self.sender().text()]])

    def updProductKind(self, kind_name: str) -> None:
        """ Посылает сигнал на изменение вида изделия """

        self.updProductKindSignal.emit(kind_name)

    @staticmethod
    def selectedProduct(index) -> Product:
        """ Возвращает изделие по индексу """

        try:
            product = index.model().itemFromIndex(index.sibling(0, 0)).data()
        except (IndexError, AttributeError):
            product = None
        return product


class HierarchicalView(QTreeView):
    """ Представление иерархического древа, которое
        отображается в главном окне """

    # pylint: disable=too-many-public-methods

    def __init__(self, product_denotation: str,
                 reverse: bool = False,
                 header_labels=('Индекс', 'Уровень', 'Наименование', 'Обозначение',
                                'Тип согласно\nспецификации', 'Кол-во', 'Ед.\nизм.')):
        logging.info('Инициализация иерархического древа')
        super().__init__()
        self.model = HierarchicalModel(product_denotation, reverse)
        self.model.updKttpSignal.connect(self.updKttp)
        self.model.addKttpSignal.connect(self.addKttp)
        self.model.delKttpSignal.connect(self.delKttp)
        self.model.updProductKindSignal.connect(self.updProductKind)
        self.setModel(self.model)
        self.document_types = self.model.tree.document_types.values()
        self.header_horizontal = header_labels
        self.column_settings = {}
        self.expand_settings = {}
        self.importData()
        self.modifyModelSettings()
        self.expanded.connect(self.modifyModelSettingsOnUpdate)
        self.collapsed.connect(self.modifyModelSettingsOnUpdate)
        self.delegate_settings = DelegateSettings(view=self)

    @ property
    def header_horizontal(self) -> list[str]:
        """ Список названий столбцов """

        header = []
        for column in range(self.model.columnCount()):
            header.append(self.model.horizontalHeaderItem(column).text())
        return header

    @ header_horizontal.setter
    def header_horizontal(self, header: list[str]) -> None:
        """ Изменяет названия столбцов """

        self.model.setHorizontalHeaderLabels(header)

    def modifyModelSettings(self) -> None:
        """ Настройка внешнего вида представления """

        self.blockSignals(True)
        self.expandAll()
        self.setSortingEnabled(True)
        self.setUniformRowHeights(False)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setTreePosition(1)
        self.setColumnHidden(0, True)
        self.setExpandToLevel(expand_level=1)
        self.header().setDefaultAlignment(Qt.AlignCenter)
        self.header().setMaximumSectionSize(500)
        self.blockSignals(False)
        self.modifyModelSettingsOnUpdate()

    def modifyModelSettingsOnUpdate(self) -> None:
        """ Установка параметров после обновления """

        for column in range(self.model.columnCount()):
            self.resizeColumnToContents(column)

    @staticmethod
    def qDataRow(data_row: list[str, int, None]) -> list[QStandardItem]:
        """ Записывает данные в модель """

        q_data_row = []
        for item in data_row:
            q_item = QStandardItem()
            q_item.setData(item, Qt.DisplayRole)
            q_data_row.append(q_item)
        return q_data_row

    def importData(self, root: QStandardItem | None = None) -> None:
        """ Вносит в модель данные родитель: дети """

        self.model.setRowCount(0)
        if root is None:
            root = self.model.invisibleRootItem()
        root_branch = self.model.tree.tree_dicts[0]
        q_data_row = self.qDataRow([None, 0,
                                    root_branch.name,
                                    root_branch.deno,
                                    root_branch.child_data.child_type,
                                    root_branch.child_data.child_quantity,
                                    root_branch.child_data.child_unit])
        root.appendRow(q_data_row)
        root.child(root.rowCount() - 1).setData(root_branch.product)
        parent = root.child(root.rowCount() - 1)
        SplashScreen().newMessage(message='Построение модели...\nВнесение дочерних изделий',
                                  log=True,
                                  logging_level='DEBUG')
        self.addChildren(parent=parent,
                         parent_id=root_branch.unique_id,
                         level=0,
                         main_index='')

    def addChildren(self, parent: QStandardItem,
                    parent_id: int,
                    level: int,
                    main_index: str) -> None:
        """ Рекурсивно вносит в модель данные родитель: дети """

        for branch in self.model.tree.tree_dicts:
            if branch.parent_id == parent_id:
                index = main_index + str(parent.rowCount() + 1) + '.'
                self.column_settings['Индекс'] = {'data': index,
                                                  'visible': False}
                self.column_settings['Наименование'] = {'data': {'type': 'product',
                                                                 'header': 'Наименование',
                                                                 'setting': 'name'},
                                                        'visible': True}
                q_data_row = self.qDataRow([index, level + 1,
                                            branch.name,
                                            branch.deno,
                                            branch.child_data.child_type,
                                            branch.child_data.child_quantity,
                                            branch.child_data.child_unit])
                parent.appendRow(q_data_row)
                parent.child(parent.rowCount() - 1).setData(branch.product)
                if level < 30:
                    self.addChildren(parent=parent.child(parent.rowCount() - 1),
                                     parent_id=branch.unique_id,
                                     level=level + 1,
                                     main_index=index)
                else:
                    name = branch.name
                    deno = branch.deno
                    SplashScreen().close()
                    show_dialog(f'Обнаружена рекурсивная зависимость в {name} {deno}')

    def setExpandToLevel(self, expand_level: int) -> None:
        """ Раскрывает представление модели до определенного уровня """

        expand_level = expand_level - 1
        self.collapseAll()
        if expand_level >= 0:
            self.expandToDepth(expand_level)

    def addNewColumn(self, data: dict[str, str | bool | None | dict[Product, str]],
                     modify_settings: bool = True, new_column: bool = True) -> None:
        """ Добавляет новый или скрывает/показывает уже имеющийся столбец """

        header = data['header']
        root = self.model.invisibleRootItem()
        if header not in self.header_horizontal:
            column = self.model.columnCount()
            self.getDataFromProduct(item=root,
                                    data=data,
                                    column=column,
                                    new_column=new_column)
            self.column_settings[data['header']] = {'data': data,
                                                    'visible': True}
            if 'delegate' in data:
                self.delegate_settings.setDelegate(
                    delegate_name=data['delegate'],
                    column=column)
        else:
            column = self.header_horizontal.index(header)
            visibility = not self.isColumnHidden(column)
            self.setColumnHidden(column, visibility)
            self.column_settings[data['header']]['visible'] = visibility
        self.model.setHorizontalHeaderItem(column, QStandardItem(header))
        if modify_settings:
            self.modifyModelSettingsOnUpdate()

    def getDataFromProduct(self, data: dict[str, str | bool | None | dict[Product, str]],
                           item: QStandardItem, column: int, new_column: bool) -> None:
        """ Изменяет данные столбца, запрашивая
            определенный аттрибут для каждой строки """

        if new_column:
            item.appendColumn([QStandardItem() for _ in range(item.rowCount())])
        for row in range(item.rowCount()):
            child = item.child(row)
            data = self.addDataToModel(item=item,
                                       child=child,
                                       data=data,
                                       row=row,
                                       column=column)
            self.getDataFromProduct(item=child,
                                    data=data,
                                    column=column,
                                    new_column=new_column)

    # pylint: disable=too-many-arguments
    def addDataToModel(self, item: QStandardItem, child: QStandardItem, row: int, column: int,
                       data: dict[str, str | bool | None | dict[Product, str]]
                       ) -> dict[str, str | bool | None | dict[Product, str]]:
        """ Запрос определенных аттрибутов у определенного изделия.
            В случае, когда определенный аттрибут относиться
            к нескольким изделиям (несколько изделий изготавливаются
            совместно по одному технологическому процессу) вызывается
            метод дополняющий данные аттрибутов для этих изделий """

        product = child.data()
        text = product.getData(data=data)
        if 'sub_products' in data.keys():
            data = self.addComplexDocumentInfo(product=product, data=data)
            text = self.addComplexDocumentText(product=product, data=data, text=text)
        if text is not None:
            if isinstance(text, datetime.date) and text is not None:
                date = QDateTime()
                date.setSecsSinceEpoch(int(text.timestamp()))
                text = date
            item.child(row, column).setData(text, Qt.DisplayRole)
        return data

    @staticmethod
    def addComplexDocumentText(product, text: str,
                               data: dict[str, str | bool | None | dict[Product, str]]) -> str:
        """ Дополняет данными для документов совместного изготовления """

        product_dict = data['sub_products']
        additional_text = product_dict.pop(product, None)
        if additional_text is not None:
            if text:
                return '\n'.join([additional_text, text])
            return additional_text
        return text

    def addComplexDocumentInfo(self, data: dict[str, str | bool | None | dict[Product, str]],
                               product: Product) -> dict[str, str | bool | None | dict[Product, str]]:
        """ Сохраняет данные об изделиях в составе составной МК """

        sub_data = data.copy()
        sub_data['setting'] = 'sub_products_new'
        sub_data['only_text'] = False
        documents_data = product.getData(sub_data)

        if documents_data is not None:
            for document_data in documents_data:
                for sub_product, document in document_data:
                    data['sub_products'][product] = \
                        self.addComplexDocumentText(
                            product=sub_product,
                            data=data,
                            text=f'В составе {document.deno}')
        return data

    def findText(self, text: str, item: QStandardItem | None = None,
                 indexes: list[QModelIndex] | None = None) -> list[QModelIndex]:
        """ Возвращает список индексов по совпадению текста """

        if indexes is None:
            indexes = []
        item = self.model.invisibleRootItem() if item is None else item
        for col in range(self.model.columnCount()):
            index = self.model.index(0, col, item.index())
            indexes.extend(
                self.model.match(index,
                                 Qt.DisplayRole,
                                 text,
                                 hits=-1,
                                 flags=Qt.MatchFixedString | Qt.MatchContains | Qt.MatchRecursive))
        return indexes

    def findTextInColumn(self, text,
                         item=None,
                         column=0,
                         indexes: tuple[QModelIndex] = ()) -> list[QModelIndex]:
        """ Возвращает список индексов по совпадению текста, но
            ищет только в одном столбце """

        indexes = list(indexes)
        item = self.model.invisibleRootItem() if item is None else item
        index = self.model.index(0, column, item.index())
        indexes.extend(self.model.match(index,
                                        Qt.DisplayRole,
                                        text,
                                        hits=-1,
                                        flags=Qt.MatchExactly | Qt.MatchRecursive))
        return indexes

    def getExpandSettings(self, item: QStandardItem | None = None) -> None:
        """ Сохраняет какие строки скрыты/показаны """

        if item is None:
            item = self.model.invisibleRootItem()
        for row in range(item.rowCount()):
            child = item.child(row)
            code = item.child(row, 0).text()
            index = child.index()
            self.expand_settings[code] = self.isExpanded(index)
            self.getExpandSettings(child)

    def setExpandSettings(self, item: QStandardItem | None = None) -> None:
        """ Разворачивает и сворачивает уровни """

        if item is None:
            item = self.model.invisibleRootItem()
        for row in range(item.rowCount()):
            child = item.child(row)
            code = item.child(row, 0).text()
            index = child.index()
            try:
                self.setExpanded(index, self.expand_settings[code])
            except KeyError:
                self.setExpanded(index, False)
            self.setExpandSettings(child)

    def customSelectedIndexes(self, column: int = 0) -> QModelIndex | None:
        """ Возвращает индекс выделенной ячейки """

        try:
            self.setColumnHidden(0, False)
            index = self.selectedIndexes()[column]
            self.setColumnHidden(0, True)
            return index
        except IndexError:
            self.setColumnHidden(0, True)
            return None

    def customSetExpandToLevel(self, expand_level: int) -> None:
        """ SetExpandToLevel с блокировкой сигналов и настройкой столбцов
            (сделать через декоратор?) """

        self.blockSignals(True)
        self.setExpandToLevel(int(expand_level))
        self.modifyModelSettingsOnUpdate()
        self.blockSignals(False)

    def showAllDocumentTypes(self):
        """ Вывести столбцы наличия определенного вида документа,
            но для всех видов документов, которые можно встретить
            в этом изделии и его дочерних """

        self.blockSignals(True)
        self.getExpandSettings()
        self.collapseAll()
        self.document_types = sorted(self.document_types, key=lambda x: x.id_type)
        logging.debug(self.document_types)
        self.addMultipleColumns()
        self.setExpandSettings()
        try:
            self.scrollTo(self.customSelectedIndexes(1))
        except IndexError:
            pass
        except TypeError:
            logging.warning('Индекс не выбран')
        self.blockSignals(False)
        self.modifyModelSettingsOnUpdate()

    def addMultipleColumns(self) -> None:
        """ Добавление нескольких столбцов, а не одного """

        types_num = len(self.document_types)
        for num, document_type in enumerate(self.document_types):
            SplashScreen().newMessage(message=f'{document_type.subtype_name}',
                                      stage=num,
                                      stages=types_num)

            class_name = document_type.class_name
            subtype_name = document_type.subtype_name
            sign = document_type.sign_with_exceptions
            self.addNewColumn(data={'type': 'document',
                                    'header': f'{class_name}\n{sign}',
                                    'class_name': class_name,
                                    'subtype_name': subtype_name,
                                    'organization_code': document_type.organization_code,
                                    'setting': 'sign_with_exceptions',
                                    'first': True},
                              modify_settings=False)
        SplashScreen().closeWithWindow()

    def setRowColor(self, mark_index: str, color: QColor) -> None:
        """ Изменить цвет строки """

        if self.isColumnHidden(0):
            self.setColumnHidden(0, False)
            indexes = self.findTextInColumn(text=mark_index)
            self.setColumnHidden(0, True)
        else:
            indexes = self.findTextInColumn(text=mark_index)
        try:
            indexes = [indexes[0].siblingAtColumn(col)
                       for col, name in enumerate(self.header_horizontal)]
            for index in indexes:
                index.model().itemFromIndex(index).setData(color, Qt.BackgroundColorRole)
        except IndexError:
            pass

    def redrawColumn(self, data: dict[str, str | bool | None | dict[Product, str]]) -> None:
        """ Обновить данные определенного столбца """

        header = data['header']
        if header in self.header_horizontal:
            root = self.model.invisibleRootItem()
            column = self.header_horizontal.index(header)
            self.getDataFromProduct(item=root,
                                    data=data,
                                    column=column,
                                    new_column=False)

    def redrawAllColumns(self) -> None:
        """ Обновить данные всех столбцов """

        for header, header_data in self.column_settings.items():
            if header != 'Индекс':
                self.redrawColumn(header_data['data'])

    def updKttp(self, documents: list) -> None:
        """ Обновить список типовых ТП, относящихся
            к определенному изделию """

        product = self.selected_product
        product.updKttp(documents=documents)
        self.redrawAllColumns()

    def addKttp(self, documents: list) -> None:
        """ Привязать типовой ТП к изделию """

        product = self.selected_product
        product.addDocument(documents[0])
        self.redrawAllColumns()

    def delKttp(self, documents: list) -> None:
        """ Отвязать типовой ТП от изделия """

        product = self.selected_product
        product.delDocument(documents[0])
        self.redrawAllColumns()

    def updProductKind(self, kind_name) -> None:
        """ Изменить вид изделия """

        product = self.selected_product
        kind_dict = ProductKind.all_db_kinds()
        product.product_kind = kind_dict[kind_name]
        self.redrawAllColumns()

    @property
    def selected_product(self) -> Product:
        """ Определить изделие, которое относиться к выбранной строке """

        try:
            index = self.customSelectedIndexes()
            product = index.model().itemFromIndex(index).data()
        except (IndexError, AttributeError):
            product = None
        return product

    @property
    def selected_product_index(self) -> QModelIndex:
        """ Индекс, выбранной строки """

        try:
            index = self.customSelectedIndexes().data()
        except (IndexError, AttributeError):
            index = None
        return index


class DelegateSettings:
    """ Определяет какие делегаты используются
        в представлении для различных столбцов """

    def __init__(self, view: HierarchicalView) -> None:
        self.view = view
        self.settings = {}

    def setDelegate(self, delegate_name: str, column: int) -> None:
        """ Сопоставляет делегата столбцу.
            Определяет делегата по его наименованию """

        delegate = getattr(self, delegate_name)
        self.view.setItemDelegateForColumn(column, delegate)
        self.settings[column] = delegate

    @property
    def delegate_kttp(self) -> DelegateKTTP:
        """ Делегат для типовых технологических процессов """

        return DelegateKTTP()

    @property
    def delegate_product_kind(self) -> DelegateProductKind:
        """ Делегат для видов изделий """

        return DelegateProductKind()


class DelegateKTTP(QStyledItemDelegate):
    """ Делегат для типовых технологических процессов """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    @staticmethod
    def setItems(current_text: str, model: HierarchicalModel) -> list[str]:
        """ Определяет список документов, выводя
            текущие документы в верх списка """

        items = sorted(model.tree.kttp_deno_only.keys())
        if current_text:
            current_item = current_text.split('\n')
            for item in current_item:
                items.remove(item)
            items = sorted(current_item) + items
        return items

    def createEditor(self, parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> ComboboxWithCheckBox:
        """ Создание редактора для выбора документов """

        editor = ComboboxWithCheckBox(parent)
        current_text = str(index.model().itemData(index)[0])
        editor.current_items = current_text.split('\n')
        editor.text = current_text
        editor.addItems(self.setItems(current_text=current_text, model=index.model()))
        return editor

    def setModelData(self, editor: ComboboxWithCheckBox,
                     model: HierarchicalModel,
                     index: QModelIndex) -> None:
        """ Изменение данных модели """

        model.updKttp(names=editor.checkItems())
        model.setData(index, '\n'.join(editor.checkItems()), Qt.EditRole)


class DelegateProductKind(QStyledItemDelegate):
    """ Делегат для видов изделий """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def createEditor(self, parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QComboBox:
        """  Создание редактора для выбора вида документа """

        editor = QComboBox(parent)
        current_text = str(index.model().itemData(index)[0])
        editor.addItems(ProductKind.all_db_kinds().keys())
        editor.setCurrentText(current_text)
        return editor

    def setModelData(self, editor: QComboBox, model: HierarchicalModel, index: QModelIndex) -> None:
        """ Изменение данных модели """

        model.updProductKind(kind_name=editor.currentText())
        model.setData(index, editor.currentText(), Qt.EditRole)


class ComboboxWithCheckBox(QComboBox):
    """ Виджет выбора элементов в виде
        комбобокса с выпадающим списком чекбоксов
        с возможностью множественного выбора """

    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.current_items = []
        self.text = ''

    def addItem(self, text: str, *args, **kwargs) -> None:
        """ Переопределение метода добавления элементов в комбобокс """

        super().addItem(text)
        item = self.model().item(self.count() - 1, 0)
        item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        if item.text() in self.current_items:
            item.setCheckState(Qt.Checked)
        else:
            item.setCheckState(Qt.Unchecked)

    def addItems(self, items: list[str]) -> None:
        """ Множественное добавление элементов """

        for item in items:
            self.addItem(item)

    def itemChecked(self, index) -> bool:
        """ Возвращает наличие выбора в чекбоксе """

        item = self.model().item(index, 0)
        return item.checkState() == Qt.Checked

    def checkItems(self) -> list[str]:
        """ Возвращает список названий выбранных элементов """

        checked_items = []
        for i in range(self.count()):
            if self.itemChecked(i):
                checked_items.append(self.model().item(i, 0).text())
        return checked_items

    def showPopup(self) -> None:
        """ Переопределение метода вывода элемента """

        super().showPopup()

    def paintEvent(self, event: QPaintEvent) -> None:
        """ Отрисовка элемента """

        painter = QStylePainter(self)
        painter.setPen(self.palette().color(QPalette.Text))
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.currentText = self.text
        painter.drawComplexControl(QStyle.CC_ComboBox, opt)
        painter.drawControl(QStyle.CE_ComboBoxLabel, opt)
        self.setToolTip("\n".join(self.checkItems()))
