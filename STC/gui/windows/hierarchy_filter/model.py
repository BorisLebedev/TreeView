""" Модель данных для окна фильтрации данных """

from __future__ import annotations

from typing import TYPE_CHECKING

from STC.gui.windows.ancestors.model import StandartModel

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy.model import HierarchicalView


class StandartModelFilter(StandartModel):
    """ Модель данных для окна фильтрации данных """

    def __init__(self, tree_view: HierarchicalView) -> None:
        super().__init__(tree_view)
        self.getIndexes()
        self.addData()

    def getData(self, column: int) -> list[str]:
        """ Возвращает список уникальных значений для столбца """

        data = []
        for row in range(self.rowCount()):
            data.append(self.item(row, column).text())
        return sorted(list(set(data)))
