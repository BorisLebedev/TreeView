from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.QtCore import QModelIndex
    from STC.gui.windows.hierarchy.model import HierarchicalView

from PyQt5.Qt import QSortFilterProxyModel
from PyQt5.Qt import QStandardItem
from PyQt5.Qt import QStandardItemModel
from PyQt5.QtCore import QItemSelection
from PyQt5.QtCore import QItemSelectionModel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QDateTime


class StandartModel(QStandardItemModel):

    def __init__(self, tree_view: HierarchicalView) -> None:
        super().__init__()
        self.unhidden_columns = None
        self.indexes = []
        self.tree_view = tree_view
        self.settings()

    def settings(self) -> None:
        total_columns = self.tree_view.model.columnCount()
        self.unhidden_columns = [col for col in range(total_columns)
                                 if not self.tree_view.header().isSectionHidden(col)]
        header_labels = ['index'] + [self.tree_view.model.horizontalHeaderItem(col).text()
                                     for col in self.unhidden_columns]
        self.setHorizontalHeaderLabels(header_labels)

    # Подсветка и фокус на строке в таблице, когда она выделена в окне поиска
    def selectionChanged(self, index: QModelIndex) -> None:
        index_sibling = index.sibling(index.row(), 0)
        index_main = self.data(index_sibling)
        index_main_start = index_main.sibling(index_main.row(), 0)
        index_main_end = index_main.sibling(index_main.row(), self.tree_view.model.columnCount() - 1)

        self.tree_view.scrollTo(index_main)
        self.tree_view.selectionModel().select(
            QItemSelection(index_main_start, index_main_end),
            QItemSelectionModel.ClearAndSelect)

    def getIndexes(self, *args, **kwargs) -> None:
        self.indexes = []
        index = self.tree_view.model.index(0, 0, self.tree_view.model.invisibleRootItem().index())
        self.indexes.extend(self.tree_view.model.match(index, Qt.DisplayRole, '',
                                                       hits=-1,
                                                       flags=Qt.MatchContains | Qt.MatchRecursive))

    def addData(self) -> None:
        for index in self.indexes:
            item = QStandardItem()
            item.setData(index, Qt.DisplayRole)
            result_row = [item]
            for col in self.unhidden_columns:
                sibling_index = index.sibling(index.row(), col)
                item = QStandardItem()
                data = self.tree_view.model.data(sibling_index)
                item.setData(data, Qt.DisplayRole)
                result_row.append(item)
            self.appendRow(result_row)

    def createProxy(self) -> SortFilterProxyModel:
        proxy = SortFilterProxyModel(self)
        return proxy


class SortFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, source_model: StandartModel | QSortFilterProxyModel) -> None:
        super().__init__()
        self.setSourceModel(source_model)
        self.tree_view = source_model.tree_view
        self.tree = self.tree_view.model.tree
        self.filters = {}

    def getData(self, column: int) -> list[str]:
        data = []
        for row in range(self.rowCount()):
            index = self.index(row, column)
            item = self.itemConversion(item=self.data(index))
            data.append(item)
        return data

    def createProxy(self) -> SortFilterProxyModel:
        proxy = SortFilterProxyModel(self)
        return proxy

    def selectionChanged(self, index: QModelIndex) -> None:
        index_sibling = index.sibling(index.row(), 0)
        index_main = self.data(index_sibling)
        index_main_start = index_main.sibling(index_main.row(), 0)
        index_main_end = index_main.sibling(index_main.row(), self.tree_view.model.columnCount() - 1)

        self.tree_view.scrollTo(index_main)
        self.tree_view.selectionModel().select(
            QItemSelection(index_main_start, index_main_end),
            QItemSelectionModel.ClearAndSelect)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        for key, regex in self.filters.items():
            ix = self.sourceModel().index(source_row, key, source_parent)
            item = self.itemConversion(item=self.sourceModel().data(ix))
            if regex.indexIn(item) == -1:
                return False
        return True

    def updKttp(self, names: list) -> None:
        documents = []
        for name in names:
            documents.append(self.tree.kttp_deno_only[name])
        self.tree_view.model.updKttpSignal.emit(documents)

    @staticmethod
    def itemConversion(item: str | int | QDateTime) -> str:
        if isinstance(item, int):
            return str(item)
        elif isinstance(item, QDateTime):
            return item.toString(Qt.LocalDate)
        else:
            return item
