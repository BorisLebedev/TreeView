from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy.model import HierarchicalView

from STC.gui.windows.ancestors.model import StandartModel


class StandartModelFilter(StandartModel):

    def __init__(self, tree_view: HierarchicalView) -> None:
        super().__init__(tree_view)
        self.getIndexes()
        self.addData()

    def getData(self, column: int) -> list[str]:
        data = []
        for row in range(self.rowCount()):
            data.append(self.item(row, column).text())
        return sorted(list(set(data)))
