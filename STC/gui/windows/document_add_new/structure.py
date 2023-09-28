""" Модуль структур окна ввода документов """

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QGridLayout

from STC.gui.windows.ancestors.structure import StructureSideMenu
from STC.gui.windows.document_add_new.frame import NewDocumentDocumentTypes
from STC.gui.windows.document_add_new.frame import NewDocumentMainFrame
from STC.gui.windows.document_add_new.frame import NewDocumentSpecProductsWithDeno
from STC.gui.windows.document_add_new.frame import NewDocumentSpecProductsNoDeno
from STC.gui.windows.document_add_new.frame import FrameComplexDocument


class StructureNewDocument(StructureSideMenu):
    """ Структура окна меню внесения реквизитов документа """

    def __init__(self, main_layout: QGridLayout) -> None:
        super().__init__(main_layout)
        self.showFrame(frame_name='Основные данные')

    def initNewDocumentFrames(self) -> None:
        """ Рамки, которые добавляются в self.data_frame и
            между которыми нужно переключаться с помощью
            кнопок в рамке self.menu_frame """

        self.main_data = NewDocumentMainFrame()
        self.main_data.findDocument.connect(self.widgetVisibility)
        self.td_complex = FrameComplexDocument()
        self.spec_products = NewDocumentSpecProductsWithDeno()
        self.spec_products_no_deno = NewDocumentSpecProductsNoDeno()
        self.spec_documents = NewDocumentDocumentTypes()
        self.frames = [self.main_data,
                       self.spec_products,
                       self.spec_products_no_deno,
                       self.spec_documents,
                       self.td_complex]

    def widgetVisibility(self) -> None:
        """ Видимость опций бокового меню в
            зависимости от вида документа """

        if self.main_data.document_class == 'КД':
            if self.main_data.document_subtype == 'Спецификация':
                self.widgetVisibilitySpec(True)
            else:
                self.widgetVisibilitySpec(False)
        elif self.main_data.document_class == 'ТД':
            self.widgetVisibilitySpec(False)
        elif self.main_data.document_class == 'PLM':
            self.widgetVisibilitySpec(False)

    def widgetVisibilitySpec(self, visibility: bool) -> None:
        """ Изменяет видимость виджетов в зависимости от вида документа """

        self.changeButtonVisibility(button_name='Изделия с ДН',
                                    visibility=visibility)
        self.changeButtonVisibility(button_name='Изделия без ДН',
                                    visibility=visibility)
        self.changeButtonVisibility(button_name='Документы',
                                    visibility=visibility)
        self.changeButtonVisibility(button_name='Изготавливается\nсовместно',
                                    visibility=not visibility)

    def changeButtonVisibility(self, button_name: str, visibility: bool) -> None:
        """ Изменяет видимость виджетов в зависимости от вида документа """

        for widget in self.menu_frame.children():
            if isinstance(widget, QPushButton):
                if widget.text() == button_name:
                    widget.setVisible(visibility)
