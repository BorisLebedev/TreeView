""" Модуль классов описывающих типовые структуры окон приложения """

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QVBoxLayout
from STC.gui.windows.ancestors.frame import FrameBasic
from STC.config.config import CONFIG

if TYPE_CHECKING:
    from STC.gui.windows.document_add_new.frame import NewDocumentMainFrame
    from STC.gui.windows.document_generator.structure import FrameMkMain


class StructureSideMenu:
    """ Класс для описания структуры окна с боковым меню """

    # pylint: disable=too-many-instance-attributes

    def __init__(self, main_layout: QGridLayout):
        self.main_layout = main_layout
        self.menu_buttons = []
        self.frames = []
        self.initFrames()
        self.initNewDocumentFrames()
        self.addFrames()

    def initFrames(self) -> None:
        """
            self.menu_frame - рамка с кнопками переключения
            между рамками в self.data_frame
            self.btns_frame - рамка для общих кнопок управления
            не относящиеся к рамкам в self.data_frame
        """

        self.menu_layout = QGridLayout()
        self.menu_frame = QFrame()
        self.menu_frame.setLayout(self.menu_layout)

        self.data_layout = QVBoxLayout()
        self.data_frame = QFrame()
        self.data_frame.setLayout(self.data_layout)

        self.btns_layout = QVBoxLayout()
        self.btns_frame = QFrame()
        self.btns_frame.setLayout(self.btns_layout)

        self.main_layout.addWidget(self.menu_frame, 0, 0)
        self.main_layout.addWidget(self.data_frame, 0, 1, 2, 1)
        self.main_layout.addWidget(self.btns_frame, 1, 0)
        self.main_layout.setRowStretch(0, 1)
        self.main_layout.setColumnStretch(1, 1)

    def initNewDocumentFrames(self) -> None:
        """ Рамки, которые добавляются в self.data_frame и
            между которыми нужно переключаться с помощью
            кнопок в рамке self.menu_frame """

        self.basic1 = FrameBasic('basic1')
        self.basic2 = FrameBasic('basic2')
        self.basic3 = FrameBasic('basic3')
        self.frames = [self.basic1,
                       self.basic2,
                       self.basic3]

    def addFrames(self) -> None:
        """ Проходит по списку рамок для self.data_frame
            и вызывает метод добавления их в окно """

        self.menu_frame.layout().setRowStretch(1000, 1)
        for frame in self.frames:
            self.updateContentsFrame(frame)

    def hideAllFrames(self) -> None:
        """ Скрывает все рамки, добавленные в self.data_frame """

        for frame in self.frames:
            frame.hide()

    def updateContentsFrame(self, frame) -> None:
        """ Добавляет определенную рамку в рамку self.data_frame,
            создавая кнопку в боковом меню и помещая ее в рамку self.menu_frame"""

        button = QPushButton()
        button.setText(frame.name)
        button.setObjectName(frame.name)
        button.clicked.connect(lambda: self.frameSwitcher(button.objectName()))
        button.setStyleSheet(CONFIG.style.btn_stylesheet_table)
        self.menu_buttons.append(button)
        self.menu_layout.addWidget(button, self.menu_frame.layout().count(), 0)
        self.data_layout.addWidget(frame)
        frame.hide()

    def frameSwitcher(self, frame_name: str):
        """ Аналог нажатия на кнопку меню для определенной рамки,
            но без дополнительных сигналов, которые посылаются
            при нажатии на кнопку """

        self.hideAllFrames()
        self.showFrame(frame_name)
        self.activateMenuBtn(frame_name)

    def showFrame(self, frame_name: str | None = None, frame=None):
        """ Скрывает все рамки из self.data_frame, кроме одной """

        for frame_item in self.frames:
            if frame_name:
                if frame_item.name == frame_name:
                    frame_item.show()
            elif frame:
                if frame_item == frame:
                    frame_item.show()

    def activateMenuBtn(self, frame_name: str):
        """ Изменяет стиль отрисовки кнопки если она относиться к
            определенной рамке """

        for btn in self.menu_buttons:
            if btn.text() == frame_name:
                btn.setStyleSheet(CONFIG.style.btn_stylesheet_active_table)
            else:
                btn.setStyleSheet(CONFIG.style.btn_stylesheet_table)
