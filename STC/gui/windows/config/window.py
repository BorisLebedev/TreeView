from STC.gui.windows.ancestors.window import WindowBasic
from STC.gui.windows.config.structure import StructureCreateMKConfig
from STC.gui.windows.config.structure import StructureCreateProductConfig


# Окно с параметрами конфигурации для создания маршрутных карт
class WindowMkConfig(WindowBasic):

    def __init__(self) -> None:
        super().__init__()
        self.title = "Настройка конструктора маршрутных карт"
        self.initUI()

    def initUI(self) -> None:
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 1280, 720)
        self.initStructure()

    def initStructure(self) -> None:
        self.structure = StructureCreateMKConfig(main_layout=self.main_layout)


# Окно с параметрами конфигурации для изделий
class WindowProductConfig(WindowBasic):

    def __init__(self) -> None:
        super().__init__()
        self.title = "Администрирование изделий"
        self.initUI()

    def initUI(self) -> None:
        self.basic_layout.itemAt(0).widget().layout.itemAt(0).widget().setText(self.title)
        self.setGeometry(150, 150, 1280, 720)
        self.initStructure()

    def initStructure(self) -> None:
        self.structure = StructureCreateProductConfig(main_layout=self.main_layout)