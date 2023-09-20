from PyQt5.QtCore import Qt
from PyQt5.QtCore import QPoint
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QTableWidget
from STC.gui.windows.ancestors.context_menu import ContextMenuForBasicTable


# Базовая рамка с настройками в зависимости от типа запрашиваемой рамки
class FrameBasic(QFrame):

    def __init__(self, frame_name: str | None = None) -> None:
        super().__init__()
        self.name = frame_name
        self.type = frame_type
        self.setFrameSettings()
        self.setLayout(self.main_layout)

    def setFrameSettings(self) -> None:
        """ Устанавливает общие настройки в зависимости от типа рамки """

        self.setGeometry(100, 100, 100, 100)
        self.setFrameStyle(QFrame.Panel | QFrame.HLine)
        self.setLineWidth(2)
        self.main_layout = QGridLayout()


# Базовая рамка с таблицей внутри
class FrameWithTable(FrameBasic):

    def __init__(self, frame_name: str | None = None,) -> None:
        super().__init__(frame_name=frame_name)
        self.start_rows = 0
        self.start_cols = 0
        self.header_settings = None
        self.initTableWidget()
        self.initWidgetPosition()
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.showContextMenu)

    def initTableWidget(self) -> None:
        self.table = QTableWidget()
        self.table.cellChanged.connect(self.cellChanged)
        self.initTableSettings()
        self.table.setRowCount(self.start_rows)
        self.table.setColumnCount(self.start_cols)
        self.table.setHorizontalHeaderLabels(
            [setting['name'] for setting in self.header_settings])
        self.table.horizontalHeader().setStretchLastSection(True)
        for setting in self.header_settings:
            self.table.setColumnWidth(setting['col'], setting['width'])

    def initTableSettings(self) -> None:
        self.header_settings = ({'col': 0, 'width': 100, 'name': 'Column 0'},
                                {'col': 1, 'width': 100, 'name': 'Column 1'})
        self.start_rows = 0
        self.start_cols = 2

    def initWidgetPosition(self) -> None:
        self.layout().addWidget(self.table)

    def cellChanged(self) -> None:
        if self.table.currentRow() == self.table.rowCount() - 1:
            self.addNewRow()

    def showContextMenu(self, point: QPoint) -> None:
        self.context_menu = ContextMenuForBasicTable(self)
        qp = self.sender().mapToGlobal(point)
        self.context_menu.exec_(qp)

    def deleteRow(self) -> None:
        self.table.removeRow(self.table.currentRow())

    def addNewRow(self) -> None:
        self.table.setRowCount(self.table.rowCount() + 1)

    def defaultValues(self, *args, **kwargs) -> None:
        pass

    def getData(self) -> None:
        pass
