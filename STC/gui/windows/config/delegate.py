from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from PyQt5.Qt import QModelIndex
    from PyQt5.Qt import QStyleOptionViewItem
    from PyQt5.Qt import QWidget

from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QStyledItemDelegate
from PyQt5.QtWidgets import QPlainTextEdit
from STC.database.database import DbSetting
from STC.database.database import DbSentence
from STC.database.database import DbIOT
from STC.database.database import DbMaterial
from STC.database.database import DbRig
from STC.database.database import DbEquipment
from STC.database.database import DbOperation
from STC.database.database import DbArea
from STC.database.database import DbWorkplace
from STC.database.database import DbProfession
from STC.database.database import DbProductKind
from STC.database.database import DbDocumentType
from STC.product.product import Document
from STC.product.product import return_document_type
from STC.config.config import CONFIG


class DelegatePlainText(QStyledItemDelegate):

    itemChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QComboBox:
        editor = QPlainTextEdit(parent)
        current_text = str(index.model().itemData(index)[0])
        editor.setPlainText(current_text)
        return editor

    def setModelData(self, editor: QPlainTextEdit, model, index: QModelIndex) -> None:
        model.setData(index, editor.toPlainText(), Qt.EditRole)


class DelegateComboBox(QStyledItemDelegate):

    itemChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QComboBox:
        editor = QComboBox(parent)
        editor.setEditable(True)
        current_text = str(index.model().itemData(index)[0])
        editor.addItems(self.items)
        editor.setCurrentText(current_text)
        return editor

    def setModelData(self, editor: QComboBox, model, index: QModelIndex) -> None:
        model.setData(index, editor.currentText(), Qt.EditRole)
        self.itemChanged.emit()

    @property
    def items(self) -> list[str]:
        return []


class DelegateComboBoxRig(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbRig.uniqueData()])


class DelegateComboBoxIOT(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.deno for item in DbIOT.uniqueData()])


class DelegateComboBoxMat(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbMaterial.uniqueData()])


class DelegateComboBoxEqt(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbEquipment.uniqueData()])


class DelegateComboBoxSettings(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([f'{item.operation.name} - {item.text}' for item in DbSetting.uniqueData()])


class DelegateComboBoxSentences(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.text for item in DbSentence.uniqueData()])


class DelegateComboBoxOrder(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return [str(num) for num in range(1, 20)]


class DelegateComboBoxOperations(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbOperation.uniqueData()])


class DelegateComboBoxArea(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbArea.uniqueData()])


class DelegateComboBoxWorkplace(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbWorkplace.uniqueData()])


class DelegateComboBoxProfession(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name for item in DbProfession.uniqueData()])


class DelegateComboBoxProductKind(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.name_short for item in DbProductKind.uniqueData()])


class DelegateComboBoxDoc(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        return sorted([item.subtype_name for item in DbDocumentType.uniqueData() if item.class_name == 'КД'])


class DelegateComboBoxTTP(DelegateComboBox):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.document_type = return_document_type(class_name='ТД',
                                                  subtype_name='Карта типового (группового) технологического процесса',
                                                  organization_code='2')
        self.db_documents_real = Document.getAllDocuments(document_type=self.document_type)

    @property
    def items(self) -> list[str]:
        return sorted(self.db_documents_real.keys())


class DelegateComboBoxPKI(DelegateComboBox):
    _config = CONFIG

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.pki_type = self.__class__._config.data['product_settings']['pki_type'].split(',')

    @property
    def items(self) -> list[str]:
        return self.pki_type

