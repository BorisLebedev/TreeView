""" Модуль с делегатами для таблиц
    администрирования данных БД """

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from PyQt5.Qt import QModelIndex
    from PyQt5.Qt import QStyleOptionViewItem
    from PyQt5.Qt import QWidget


class DelegatePlainText(QStyledItemDelegate):
    """ Делегат для текста """

    itemChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def createEditor(self, parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QPlainTextEdit:
        """ Создание многострочного редактора текста в ячейке
            и добавление в него текущего текста ячейки """

        editor = QPlainTextEdit(parent)
        current_text = str(index.model().itemData(index)[0])
        editor.setPlainText(current_text)
        return editor

    def setModelData(self, editor: QPlainTextEdit, model, index: QModelIndex) -> None:
        """ Вставка текста делегата в таблицу """

        model.setData(index, editor.toPlainText(), Qt.EditRole)


class DelegateComboBox(QStyledItemDelegate):
    """ Родительский класс для делегатов в виде комбобокса """

    itemChanged = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

    def createEditor(self, parent: QWidget,
                     option: QStyleOptionViewItem,
                     index: QModelIndex) -> QComboBox:
        """ Создание делегата в виде комбобокса с
            заполнением значений по умолчанию"""

        editor = QComboBox(parent)
        editor.setEditable(True)
        current_text = str(index.model().itemData(index)[0])
        editor.addItems(self.items)
        editor.setCurrentText(current_text)
        return editor

    def setModelData(self, editor: QComboBox, model, index: QModelIndex) -> None:
        """ Вставка текста делегата в таблицу """

        model.setData(index, editor.currentText(), Qt.EditRole)
        self.itemChanged.emit()

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return []


class DelegateComboBoxRig(DelegateComboBox):
    """ Делегат с наименованиями оснастки """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbRig.uniqueData()])


class DelegateComboBoxIOT(DelegateComboBox):
    """ Делегат с номерами инструкций по охране труда """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.deno for item in DbIOT.uniqueData()])


class DelegateComboBoxMat(DelegateComboBox):
    """ Делегат с наименованиями материалов """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbMaterial.uniqueData()])


class DelegateComboBoxEqt(DelegateComboBox):
    """ Делегат с наименованиями оборудования """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbEquipment.uniqueData()])


class DelegateComboBoxSettings(DelegateComboBox):
    """ Делегат вида "название операции - свойство операции" """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([f'{item.operation.name} - {item.text}' for item in DbSetting.uniqueData()])


class DelegateComboBoxSentences(DelegateComboBox):
    """ Делегат с текстами переходов """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.text for item in DbSentence.uniqueData()])


class DelegateComboBoxOrder(DelegateComboBox):
    """ Делегат с порядковыми номерами переходов """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return [str(num) for num in range(1, 20)]


class DelegateComboBoxOperations(DelegateComboBox):
    """ Делегат с наименованиями операций """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbOperation.uniqueData()])


class DelegateComboBoxArea(DelegateComboBox):
    """ Делегат с наименованиями участков """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbArea.uniqueData()])


class DelegateComboBoxWorkplace(DelegateComboBox):
    """ Делегат с наименованиями рабочих мест """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbWorkplace.uniqueData()])


class DelegateComboBoxProfession(DelegateComboBox):
    """ Делегат с наименованиями профессий """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name for item in DbProfession.uniqueData()])


class DelegateComboBoxProductKind(DelegateComboBox):
    """ Делегат с видами изделий """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.name_short for item in DbProductKind.uniqueData()])


class DelegateComboBoxDoc(DelegateComboBox):
    """ Делегат с наименованиями видов конструкторских документов """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted([item.subtype_name for item in DbDocumentType.uniqueData()
                       if item.class_name == 'КД'])


class DelegateComboBoxTTP(DelegateComboBox):
    """ Делегат с типовыми технологическими процессами """

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.document_type = return_document_type(
            class_name='ТД',
            subtype_name='Карта типового (группового) технологического процесса',
            organization_code='2')
        self.db_documents_real = Document.getAllDocuments(document_type=self.document_type)

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return sorted(self.db_documents_real.keys())


class DelegateComboBoxPKI(DelegateComboBox):
    """ Делегат с типами изделий по кооперации """

    _config = CONFIG

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.pki_type = self.__class__._config.data['product_settings']['pki_type'].split(',')

    @property
    def items(self) -> list[str]:
        """ Данные для комбобокса """

        return self.pki_type
