
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from STC.product.product import Document

import logging
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QGridLayout
from STC.gui.windows.ancestors.structure import StructureSideMenu
from STC.gui.windows.document_generator.frame import FrameMkMain
from STC.gui.windows.document_generator.frame import FrameMkOperations
from STC.gui.windows.document_generator.frame import FrameMkOperationMain
from STC.gui.windows.document_generator.frame import FrameOperationButtons


# Структура окна создания маршрутной карты
class StructureCreateMK(StructureSideMenu):

    def __init__(self, main_layout: QGridLayout):
        super().__init__(main_layout)
        self.showFrame(frame_name='Основные данные')
        self.initButtonsFrame()
        self.menu_frame.setMinimumWidth(180)

    def initNewDocumentFrames(self) -> None:
        self.main_data_frame = FrameMkMain()
        self.operations_frame = FrameMkOperations()
        self.operations_frame.updateButtons.connect(self.updButtons)
        self.frames = [self.main_data_frame,
                       self.operations_frame
                       ]

    def initButtonsFrame(self) -> None:
        self.buttons_frame = FrameOperationButtons()
        self.buttons_frame.showFrame.connect(lambda: self.frameSwitcher(self.buttons_frame.current_frame))
        self.scrollarea = QScrollArea()
        self.scrollarea.setWidgetResizable(True)
        self.menu_frame.layout().addWidget(self.scrollarea, self.menu_frame.layout().count(), 0)
        self.menu_frame.layout().setRowStretch(self.menu_frame.layout().count() - 1, 100)
        self.scrollarea.setWidget(self.buttons_frame)

    def newOperation(self, document: Document) -> None:
        new_operation = self.operations_frame.new_operation
        operation_frame = FrameMkOperationMain(document=document, operation=new_operation)
        self.data_frame.layout().addWidget(operation_frame)
        operation_frame.hide()
        self.frames.append(operation_frame)
        self.updButtons()

    def delOperation(self) -> None:
        del_operation = self.operations_frame.del_operation
        operation_frame = [frame for frame in self.frames[2:] if frame.operation == del_operation][0]
        logging.debug(f'operation_frame to delete: {operation_frame}')
        self.frames.remove(operation_frame)
        self.data_frame.layout().removeWidget(operation_frame)
        operation_frame.setParent(None)
        operation_frame = None
        self.updButtons()

    def updButtons(self) -> None:
        self.buttons_frame.updButtons(self.frames)
