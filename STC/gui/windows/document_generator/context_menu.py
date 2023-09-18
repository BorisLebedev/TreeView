from PyQt5.QtWidgets import QAction
from STC.gui.windows.ancestors.context_menu import ContextMenuForBasicTable


# Контекстное меню для таблицы переходов
class ContextMenuForSentenceTable(ContextMenuForBasicTable):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionText(self) -> None:
        self.del_action_text = 'Удалить переход'
        self.add_action_text = 'Добавить переход'

    def actionDelRow(self) -> QAction:
        action = QAction(self.object)
        action.setText(self.del_action_text)
        action.triggered.connect(lambda: self.object.delSentence())
        return action

    def actionAddRow(self) -> QAction:
        action = QAction(self.object)
        row = self.object.table.currentRow()
        action.setText(self.add_action_text)
        action.triggered.connect(lambda: self.object.addSentence(row=row))
        return action


# Контекстное меню для текста
class ContextMenuForSentence(ContextMenuForSentenceTable):

    def __init__(self, obj) -> None:
        obj = obj.frame
        super().__init__(obj)


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов)
class ContextMenuForSentenceAdditionalData(ContextMenuForSentenceTable):

    def __init__(self, obj) -> None:
        self.combobox_frame = obj
        obj = obj.frame
        super().__init__(obj)
        self.initActionTextAdditionalData()
        self.addAction(self.actionAddCombobox())

    def initActionText(self) -> None:
        self.del_action_text = 'Удалить переход'
        self.add_action_text = 'Добавить переход'

    def initBasicActions(self) -> None:
        pass

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить'

    def actionAddCombobox(self) -> QAction:
        action = QAction(self.combobox_frame)
        action.setText(self.add_action_combobox)
        action.triggered.connect(lambda: self.combobox_frame.newWidget())
        return action


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов)
class ContextMenuForSentenceCombobox(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        self.combobox = obj
        obj = self.combobox.cb_frame
        super().__init__(obj)
        self.initActionTextForCombobox()
        self.addAction(self.actionDelComboBox())

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить'

    def actionDelComboBox(self) -> QAction:
        action = QAction(self.combobox_frame)
        action.setText(self.del_action_combobox)
        action.triggered.connect(lambda: self.combobox_frame.delWidget(self.combobox))
        return action


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов) для ИОТ
class ContextMenuForSentenceIot(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить ИОТ'


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов) для документов
class ContextMenuForSentenceDoc(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить документ'


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов) для оснастки
class ContextMenuForSentenceRig(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить оснастку'


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов) для оснастки
class ContextMenuForSentenceEquipment(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить оборудование'


# Контекстное меню для виджета рамки с двумя столбцами комбобоксов (в таблице переходов) для материалов
class ContextMenuForSentenceMat(ContextMenuForSentenceAdditionalData):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить материал'


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов) для ИОТ
class ContextMenuForSentenceIotCombobox(ContextMenuForSentenceCombobox):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить ИОТ'

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить ИОТ'


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов) для документов
class ContextMenuForSentenceDocCombobox(ContextMenuForSentenceCombobox):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить документ'

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить документ'


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов) для оснаски
class ContextMenuForSentenceRigCombobox(ContextMenuForSentenceCombobox):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить оснастку'

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить оснаску'


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов) для материалов
class ContextMenuForSentenceMatCombobox(ContextMenuForSentenceCombobox):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить материал'

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить материал'


# Контекстное меню для комбобокса в рамке с двумя столбцами комбобоксов (в таблице переходов) для оборудования
class ContextMenuForSentenceEquipmentCombobox(ContextMenuForSentenceCombobox):

    def __init__(self, obj) -> None:
        super().__init__(obj)

    def initActionTextForCombobox(self) -> None:
        self.del_action_combobox = 'Удалить оборудование'

    def initActionTextAdditionalData(self) -> None:
        self.add_action_combobox = 'Добавить оборудование'
