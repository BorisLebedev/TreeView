""" Классы окон с настройкой параметров документов и изделий """

from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.config.structure import StructureCreateMKConfig
from STC.gui.windows.config.structure import StructureCreateProductConfig


class WindowMkConfig(WindowBasic):
    """ Родительское окно для окон настроек
        маршрутных карт """

    def __init__(self) -> None:
        super().__init__()
        self.title = "Настройка конструктора маршрутных карт"
        self.structure = None
        self.initUI()

    def initUI(self) -> None:
        """ Настройки окна и инициализация структуры окна """

        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 1280, 720)
        self.initStructure()

    def initStructure(self) -> None:
        """ Инициализация структуры окна """

        self.structure = StructureCreateMKConfig(main_layout=self.main_layout)


class WindowProductConfig(WindowBasic):
    """ Родительское окно для окон с
        параметрами конфигурации изделий """

    def __init__(self) -> None:
        super().__init__()
        self.title = "Администрирование изделий"
        self.structure = None
        self.initUI()

    def initUI(self) -> None:
        """ Настройки окна и инициализация структуры окна """

        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 1280, 720)
        self.initStructure()

    def initStructure(self) -> None:
        """ Инициализация структуры окна """

        self.structure = StructureCreateProductConfig(main_layout=self.main_layout)
