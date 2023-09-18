from PyQt5.QtWidgets import QAction
from STC.gui.windows.ancestors.context_menu import ContextMenuForBasicTable

class ContextMenuForFrameAdminDef(ContextMenuForBasicTable):

    def __init__(self, obj):
        super(ContextMenuForFrameAdminDef, self).__init__(obj)
        self.addAction(self.copyRow())

    def copyRow(self) -> QAction:
        action = QAction(self.object)
        action.setText("Копировать строку")
        action.triggered.connect(lambda: self.object.copyRow())
        return action