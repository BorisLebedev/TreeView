""" Структуры окон натройки параметров документов и изделий """

from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QPushButton
from STC.gui.splash_screen import SplashScreen
from STC.gui.windows.ancestors.structure import StructureSideMenu
from STC.gui.windows.config.frame import FrameAdminOperations
from STC.gui.windows.config.frame import FrameAdminOperationsDef
from STC.gui.windows.config.frame import FrameAdminSettingsDef
from STC.gui.windows.config.frame import FrameAdminSettings
from STC.gui.windows.config.frame import FrameAdminSentence
from STC.gui.windows.config.frame import FrameAdminArea
from STC.gui.windows.config.frame import FrameAdminWorkplace
from STC.gui.windows.config.frame import FrameAdminProfession
from STC.gui.windows.config.frame import FrameAdminDocDef
from STC.gui.windows.config.frame import FrameAdminDoc
from STC.gui.windows.config.frame import FrameAdminIOT
from STC.gui.windows.config.frame import FrameAdminIOTDef
from STC.gui.windows.config.frame import FrameAdminMat
from STC.gui.windows.config.frame import FrameAdminMatDef
from STC.gui.windows.config.frame import FrameAdminRig
from STC.gui.windows.config.frame import FrameAdminRigDef
from STC.gui.windows.config.frame import FrameAdminEqt
from STC.gui.windows.config.frame import FrameAdminEqtDef
from STC.gui.windows.config.frame import FrameAdminTTPErr
from STC.gui.windows.config.frame import FrameAdminPrimaryProduct


class StructureCreateMKConfig(StructureSideMenu):
    """ Структура окна создания маршрутной карты """

    # pylint: disable=too-many-instance-attributes
    # pylint: disable=attribute-defined-outside-init

    def __init__(self, main_layout: QGridLayout, default_frame: str = 'Операции'):
        super().__init__(main_layout)
        self.showFrame(frame_name=default_frame)
        self.alignTextInMenu()
        self.initUpdButton()
        SplashScreen().closeWithWindow()

    def initNewDocumentFrames(self) -> None:
        """ Инициализация рамок и сигналов рамок,
            привязка списка рамок к атрибуту """

        self.initNewFrames()
        self.initFrameSignals()
        self.frames = [
                       self.operation,
                       self.operation_def,
                       self.area,
                       self.workplace,
                       self.profession,
                       self.doc,
                       self.iot,
                       self.mat,
                       self.rig,
                       self.eqt,
                       self.setting,
                       self.setting_def,
                       self.sentence,
                       self.doc_def,
                       self.iot_def,
                       self.mat_def,
                       self.rig_def,
                       self.eqt_def,
                       ]

    def initNewFrames(self) -> None:
        """ Инициализация рамок окна """

        SplashScreen().newMessage(message='Загрузка данных...Операции',
                                  stage=1,
                                  stages=16)
        self.operation = FrameAdminOperations('Операции')

        SplashScreen().newMessage(message='Загрузка данных...Данные операций')
        self.operation_def = FrameAdminOperationsDef('Данные операций')

        SplashScreen().newMessage(message='Загрузка данных...Участок')
        self.area = FrameAdminArea('Участок')

        SplashScreen().newMessage(message='Загрузка данных...Рабочее место')
        self.workplace = FrameAdminWorkplace('Рабочее место')

        SplashScreen().newMessage(message='Загрузка данных...Профессия')
        self.profession = FrameAdminProfession('Профессия')

        SplashScreen().newMessage(message='Загрузка данных...Виды документов')
        self.doc = FrameAdminDoc('Виды документов')

        SplashScreen().newMessage(message='Загрузка данных...ИОТ')
        self.iot = FrameAdminIOT('ИОТ')

        SplashScreen().newMessage(message='Загрузка данных...Материалы')
        self.mat = FrameAdminMat('Материалы')

        SplashScreen().newMessage(message='Загрузка данных...Оснастка')
        self.rig = FrameAdminRig('Оснастка')

        SplashScreen().newMessage(message='Загрузка данных...Оборудование')
        self.eqt = FrameAdminEqt('Оборудование')

        SplashScreen().newMessage(message='Загрузка данных...Свойства')
        self.setting = FrameAdminSettings('Операция -> Свойства')

        SplashScreen().newMessage(message='Загрузка данных...Свойства -> Переход')
        self.setting_def = FrameAdminSettingsDef('Свойства -> Переход')

        SplashScreen().newMessage(message='Загрузка данных...Переходы')
        self.sentence = FrameAdminSentence('Переходы')

        SplashScreen().newMessage(message='Загрузка данных...Переход -> Вид документа')
        self.doc_def = FrameAdminDocDef('Переход -> Вид документа')

        SplashScreen().newMessage(message='Загрузка данных...Переход -> ИОТ')
        self.iot_def = FrameAdminIOTDef('Переход -> ИОТ')

        SplashScreen().newMessage(message='Загрузка данных...Переход -> Материалы')
        self.mat_def = FrameAdminMatDef('Переход -> Материалы')

        SplashScreen().newMessage(message='Загрузка данных...Переход -> Оснастка')
        self.rig_def = FrameAdminRigDef('Переход -> Оснастка')

        SplashScreen().newMessage(message='Загрузка данных...Переход -> Оборудование')
        self.eqt_def = FrameAdminEqtDef('Переход -> Оборудование')

    def initFrameSignals(self) -> None:
        """ Инициализация сигналов рамок и их взаимодействия"""

        self.operation.newItem.connect(self.newOperationAdded)
        self.area.newItem.connect(self.operation_def.updTable)
        self.workplace.newItem.connect(self.operation_def.updTable)
        self.profession.newItem.connect(self.operation_def.updTable)
        self.iot.newItem.connect(self.iot_def.updTable)
        self.mat.newItem.connect(self.mat_def.updTable)
        self.rig.newItem.connect(self.rig_def.updTable)
        self.eqt.newItem.connect(self.eqt_def.updTable)
        self.setting.newItem.connect(self.setting_def.updTable)
        self.workplace.newItem.connect(self.operation_def.updTable)
        self.sentence.newSentence.connect(self.newSentenceAdded)

    def initUpdButton(self) -> None:
        """ Кнопка обновления данных рамок окна """

        self.btn_upd = QPushButton('Обновить')
        self.btn_upd.clicked.connect(self.updTables)
        self.btns_layout.addWidget(self.btn_upd)

    def updTables(self):
        """ Обновление данных рамок окна """

        for table in self.frames:
            if table.isVisible():
                table.updTable()

    def newOperationAdded(self) -> None:
        """ Реакция окна на добавление операции """

        self.operation_def.updTable()
        self.setting.updTable()

    def newSentenceAdded(self) -> None:
        """ Реакция окна на добавление перехода """

        self.setting_def.updTable()
        self.iot.updTable()
        self.mat.updTable()
        self.rig.updTable()
        self.eqt.updTable()

    def alignTextInMenu(self):
        """ Выравнивание кнопок бокового меню """

        for btn in self.menu_buttons:
            btn.setStyleSheet("Text-align:left")


class StructureCreateProductConfig(StructureSideMenu):
    """ Структура окна администрирования изделий """

    # pylint: disable=attribute-defined-outside-init

    def __init__(self, main_layout: QGridLayout, default_frame: str = 'Ошибки с КТТП'):
        super().__init__(main_layout)
        self.showFrame(frame_name=default_frame)
        self.alignTextInMenu()
        self.initUpdButton()
        SplashScreen().closeWithWindow()

    def initNewDocumentFrames(self) -> None:
        """ Инициализация рамок и привязка списка рамок к атрибуту """

        self.initNewFrames()
        self.frames = [
            self.ttp_err,
            self.primary_product]

    def initNewFrames(self) -> None:
        """ Инициализация рамок окна """

        self.ttp_err = FrameAdminTTPErr('Ошибки с КТТП')
        self.primary_product = FrameAdminPrimaryProduct('Не указана\nпервичная\nприменяемость')

    def initUpdButton(self) -> None:
        """ Кнопка обновления данных рамок окна """

        self.btn_upd = QPushButton('Обновить')
        self.btn_upd.clicked.connect(self.updTables)
        self.btns_layout.addWidget(self.btn_upd)

    def updTables(self):
        """ Обновление данных рамок окна """

        for table in self.frames:
            if table.isVisible():
                table.updTable()

    def alignTextInMenu(self):
        """ Выравнивание кнопок бокового меню """

        for btn in self.menu_buttons:
            btn.setStyleSheet("Text-align:left")
