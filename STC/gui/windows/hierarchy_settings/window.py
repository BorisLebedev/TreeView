from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.gui.windows.hierarchy.model import HierarchicalView

from PyQt5.QtWidgets import QTabWidget

from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.hierarchy_settings.frame import FrameKDSettings
from STC.gui.windows.hierarchy_settings.frame import FrameProductSettings
from STC.gui.windows.hierarchy_settings.frame import FrameTDSettings


# Окно выбора свойств (дополнительных столбцов) иерархической таблицы
class WindowDocumentSettings(WindowBasic):

    def __init__(self, tree_model: HierarchicalView) -> None:
        super().__init__()
        self.title = 'Свойства документов'
        self.tree_model = tree_model
        self.initUI()
        self.setFrame()
        self.setTab()
        self.setPosition()

    def initUI(self) -> None:
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 640, 480)

    def setFrame(self) -> None:
        self.kd_settings = FrameKDSettings(tree_model=self.tree_model)
        self.td_settings = FrameTDSettings(tree_model=self.tree_model)
        self.product_settings = FrameProductSettings(tree_model=self.tree_model)

    def setTab(self) -> None:
        self.tab = QTabWidget()
        self.tab.setTabPosition(QTabWidget.West)
        self.tab.addTab(self.kd_settings, self.kd_settings.name)
        self.tab.addTab(self.td_settings, self.td_settings.name)
        self.tab.addTab(self.product_settings, self.product_settings.name)

    def setPosition(self) -> None:
        self.main_layout.addWidget(self.tab, 0, 0)
        self.main_layout.setSpacing(0)
