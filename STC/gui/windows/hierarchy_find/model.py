""" Модель данных для окна поиска """

from __future__ import annotations

from typing import TYPE_CHECKING

from STC.gui.windows.ancestors.model import StandartModel

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy.model import HierarchicalView


class StandartModelSearch(StandartModel):
    """ Модель для данных найденных
        по определенному тексту """

    def __init__(self, source_model: HierarchicalView,
                 search_text: str = '') -> None:
        super().__init__(source_model)
        self.source_model = source_model
        self.getIndexes(search_text)
        self.addData()

    def getIndexes(self, search_text: str) -> None:
        """ Поиск индексов элементов модели,
            где есть искомый текст """

        self.indexes = self.source_model.findText(search_text,
                                                  item=None,
                                                  indexes=[])
