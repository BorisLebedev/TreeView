""" Контекстное меню для строк переходов
    окна создания маршрутных карт """

from PyQt5.QtWidgets import QAction
from STC.gui.windows.ancestors.context_menu import ContextMenuForBasicTable


class ContextMenuForSentenceTable(ContextMenuForBasicTable):
    """ Контекстное меню для таблицы переходов """

    def initActionText(self) -> None:
        """ Текст элементов контекстного меню """

        self.del_action_text = 'Удалить переход'
        self.add_action_text = 'Добавить переход'

    def actionDelRow(self) -> QAction:
        """ Удалить переход """

        action = QAction(self.object)
        action.setText(self.del_action_text)
        action.triggered.connect(self.object.delSentence)
        return action

    def actionAddRow(self) -> QAction:
        """ Добавить переход """

        action = QAction(self.object)
        row = self.object.table.currentRow()
        action.setText(self.add_action_text)
        action.triggered.connect(lambda: self.object.addSentence(row=row))
        return action


class ContextMenuForSentence(ContextMenuForSentenceTable):
    """ Контекстное меню для текста """

    def __init__(self, obj) -> None:
        obj = obj.frame
        super().__init__(obj)


class ContextMenuForSentenceAdditionalData(ContextMenuForSentenceTable):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов (в таблице переходов) """

    def __init__(self, obj) -> None:
        self.combobox_frame = obj
        obj = obj.frame
        super().__init__(obj)
        self.initActionTextAdditionalData()
        self.addAction(self.actionAddCombobox())

    def initActionText(self) -> None:
        """ Текст элементов контекстного меню """

        self.del_action_text = 'Удалить переход'
        self.add_action_text = 'Добавить переход'

    def initBasicActions(self) -> None:
        """ Переопределение метода добавления
            или удаления строк """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить'

    def actionAddCombobox(self) -> QAction:
        """ Добавить дополнительные опции в меню """

        action = QAction(self.combobox_frame)
        action.setText(self.add_action_combobox)
        action.triggered.connect(self.combobox_frame.newWidget)
        return action


class ContextMenuForSentenceCombobox(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для комбобокса в
        рамке с двумя столбцами комбобоксов
        (в таблице переходов) """

    def __init__(self, obj) -> None:
        self.combobox = obj
        obj = self.combobox.cb_frame
        super().__init__(obj)
        self.initActionTextForCombobox()
        self.addAction(self.actionDelComboBox())

    def initActionTextForCombobox(self) -> None:
        """ Дополнительные опции """

        self.del_action_combobox = 'Удалить'

    def actionDelComboBox(self) -> QAction:
        """ Добавление опции в меню """

        action = QAction(self.combobox_frame)
        action.setText(self.del_action_combobox)
        action.triggered.connect(lambda: self.combobox_frame.delWidget(self.combobox))
        return action


class ContextMenuForSentenceIot(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов
        (в таблице переходов) для ИОТ """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить ИОТ'


class ContextMenuForSentenceDoc(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов
        (в таблице переходов) для документов """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить документ'


class ContextMenuForSentenceRig(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов
        (в таблице переходов) для оснастки """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить оснастку'


class ContextMenuForSentenceEquipment(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов
        (в таблице переходов) для оснастки """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить оборудование'


class ContextMenuForSentenceMat(ContextMenuForSentenceAdditionalData):
    """ Контекстное меню для виджета рамки
        с двумя столбцами комбобоксов
        (в таблице переходов) для материалов """

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить материал'


class ContextMenuForSentenceIotCombobox(ContextMenuForSentenceCombobox):
    """ Контекстное меню для комбобокса в рамке
        с двумя столбцами комбобоксов
        (в таблице переходов) для ИОТ """

    def initActionTextForCombobox(self) -> None:
        """ Переопределение текста
            дополнительных опций """

        self.del_action_combobox = 'Удалить ИОТ'

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить ИОТ'


class ContextMenuForSentenceDocCombobox(ContextMenuForSentenceCombobox):
    """ Контекстное меню для комбобокса в рамке
        с двумя столбцами комбобоксов
        (в таблице переходов) для документов """

    def initActionTextForCombobox(self) -> None:
        """ Переопределение текста
            дополнительных опций """

        self.del_action_combobox = 'Удалить документ'

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить документ'


class ContextMenuForSentenceRigCombobox(ContextMenuForSentenceCombobox):
    """ Контекстное меню для комбобокса в рамке
        с двумя столбцами комбобоксов
        (в таблице переходов) для оснаски """

    def initActionTextForCombobox(self) -> None:
        """ Переопределение текста
            дополнительных опций """

        self.del_action_combobox = 'Удалить оснастку'

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить оснаску'


class ContextMenuForSentenceMatCombobox(ContextMenuForSentenceCombobox):
    """ Контекстное меню для комбобокса в рамке
        с двумя столбцами комбобоксов
        (в таблице переходов) для материалов """

    def initActionTextForCombobox(self) -> None:
        """ Переопределение текста
            дополнительных опций """

        self.del_action_combobox = 'Удалить материал'

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить материал'


class ContextMenuForSentenceEquipmentCombobox(ContextMenuForSentenceCombobox):
    """ Контекстное меню для комбобокса в рамке
        с двумя столбцами комбобоксов
        (в таблице переходов) для оборудования """

    def initActionTextForCombobox(self) -> None:
        """ Переопределение текста
            дополнительных опций """

        self.del_action_combobox = 'Удалить оборудование'

    def initActionTextAdditionalData(self) -> None:
        """ Дополнительные опции """

        self.add_action_combobox = 'Добавить оборудование'
