""" Модуль с классами дополнительной всплывающей информации """

from __future__ import annotations
import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QProgressBar
from PyQt5.QtWidgets import QSplashScreen

from STC.config.config import CONFIG


def show_dialog(text: str, m_type: str | None = None) -> MessageBox:
    """ Возвращает диалоговое окно """

    msg_box = MessageBox(text, m_type)
    msg_box.exec()
    msg_box.raise_()
    return msg_box


def singleton(cls):
    """ Возвращает синглтон реализации классов """
    instances = {}

    def getinstance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return getinstance


class MessageBox(QMessageBox):
    """ Диалоговое окно """

    def __init__(self, text: str, m_type: str = 'info'):
        super().__init__()
        q_type = self.setType(m_type)
        self.setIcon(q_type)
        self.setText(text)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setButtons(m_type=m_type)

    @staticmethod
    def setType(m_type: str) -> QMessageBox.Icon:
        """ Возвращает тип диалогового окна """
        match m_type:
            case 'critical':
                return QMessageBox.Critical
            case 'info':
                return QMessageBox.Information
            case 'question':
                return QMessageBox.Question
            case 'warning':
                return QMessageBox.Warning
            case 'continue_project':
                return QMessageBox.Question
        return QMessageBox.Warning

    def setButtons(self, m_type):
        """ Устанавливает кнопки диалогового окна """

        if m_type == 'critical':
            self.setStandardButtons(QMessageBox.Ok)
        elif m_type == 'info':
            self.setStandardButtons(QMessageBox.Ok)
        elif m_type == 'question':
            self.setStandardButtons(QMessageBox.Ok)
        elif m_type == 'warning':
            self.setStandardButtons(QMessageBox.Ok)
        elif m_type == 'continue_project':
            self.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            self.button(self.Yes).setText("Да")
            self.button(self.No).setText("Нет")
        else:
            self.setStandardButtons(QMessageBox.Ok)


@singleton
class SplashScreen(QSplashScreen):
    """ Экран обработки данных """

    app = QApplication(sys.argv)

    def __init__(self) -> None:
        super().__init__()
        self.stage = 0
        self.sub_stage = 0
        self.initWindowGeometry()
        self.initProgressBar()
        self.initSubProgressBar()

    def initWindowGeometry(self) -> None:
        """ Геометрические параметры окна """

        screen = self.__class__.app.primaryScreen()
        height = 120
        width = 640
        x_pos = (screen.size().width() - width) // 2
        y_pos = (screen.size().height() - height) // 2
        self.setGeometry(x_pos, y_pos, width, height)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    def initProgressBar(self) -> None:
        """ Добавление прогресс бара """

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(50, self.height() - 60, self.width() - 100, 20)
        self.changeProgressBar(stage=0, stages=1)

    def initSubProgressBar(self) -> None:
        """ Добавление дополнительного прогресс бара """

        self.progress_bar_sub = QProgressBar(self)
        self.progress_bar_sub.setGeometry(50, self.height() - 30, self.width() - 100, 20)
        self.changeSubProgressBar(stage=0, stages=1)

    def newMessage(self, message: str,
                   stage: int | None = None,
                   stages: int | None = None,
                   log: bool = False,
                   upd_bar: bool = True,
                   logging_level: str = 'NOTSET',
                   hide_pb: bool = False,
                   align: Qt.AlignmentFlag = Qt.AlignHCenter) -> None:
        """ Выводит прогресс бар с определенным текстом, добавляет текст в лог
            и изменяет состояние прогресс бара"""

        # pylint: disable=too-many-arguments

        self.showMessage(message,  Qt.AlignTop | align, CONFIG.style.splash_screen_text_color)
        if log:
            self.addToLog(message.replace('\n', ' '), logging_level)
        if upd_bar:
            self.changeProgressBar(stage=stage,
                                   stages=stages)
        if hide_pb:
            self.progress_bar_sub.setHidden(True)
            self.progress_bar.setHidden(True)
        self.show()
        self.updWindow()

    def writeToDB(self):
        """ Сообщение о записи данных в БД """

        self.newMessage(message='Запись информации в базу данных...',
                        hide_pb=True,
                        upd_bar=False)

    def changeProgressBar(self, stage: int | None = None, stages: int | None = None) -> None:
        """ Изменение прогресс бара """

        if stages is not None:
            self.progress_bar.setMaximum(stages)
        if stage is not None and isinstance(stage, int):
            self.progress_bar.setValue(stage)
            self.stage = stage
        else:
            self.stage += 1
            self.progress_bar.setValue(self.stage)
        if stage == stages and stage is not None and stages is not None:
            self.progress_bar.setHidden(True)
        else:
            self.progress_bar.setVisible(True)

    def changeSubProgressBar(self, stage: int | None = None, stages: int | None = None):
        """ Изменение дополнительного прогресс бара """

        if stages is not None:
            self.progress_bar_sub.setMaximum(stages)
        if stage is not None and isinstance(stage, int):
            self.progress_bar_sub.setValue(stage)
            self.sub_stage = stage
        else:
            self.sub_stage += 1
            self.progress_bar_sub.setValue(self.sub_stage)
        if stage == stages and stage is not None and stages is not None:
            self.progress_bar_sub.setHidden(True)
        else:
            self.progress_bar_sub.setVisible(True)
        self.updWindow()

    def basicReceive(self, title: str, upd_bar: bool = True) -> None:
        """ Стандартное сообщение для 3-х этапного получения данных:
            1. Ожидание ответа ...
            2. Обработка данных...
            3. Обработка данных завершена"""

        self.newMessage(message=f'{title}\nОжидание ответа ...',
                        log=True,
                        stage=1,
                        stages=3,
                        upd_bar=upd_bar,
                        logging_level='INFO')

    def basicProceed(self, title: str, upd_bar: bool = True) -> None:
        """ Стандартное сообщение для 3-х этапного получения данных:
            1. Ожидание ответа ...
            2. Обработка данных...
            3. Обработка данных завершена"""

        self.newMessage(message=f'{title}\nОбработка данных...',
                        log=True,
                        upd_bar=upd_bar,
                        logging_level='DEBUG')

    def basicCompletion(self, title: str, upd_bar: bool = True) -> None:
        """ Стандартное сообщение для 3-х этапного получения данных:
            1. Ожидание ответа ...
            2. Обработка данных...
            3. Обработка данных завершена"""

        self.newMessage(message=f'{title}\nОбработка данных завершена',
                        log=True,
                        stage=0,
                        stages=0,
                        upd_bar=upd_bar,
                        logging_level='DEBUG')
        self.changeSubProgressBar(stage=0, stages=0)
        self.close()

    def basicMsg(self, title: str):
        """ Шаблон простого сообщения """

        self.newMessage(message=f'{title} ...',
                        hide_pb=True)

    def closeWithWindow(self, window=None, msg: str | None = None, m_type: str = 'info') -> None:
        """ Закрыть splashscreen """

        if window is not None:
            self.finish(window)
        elif msg is not None:
            msg = MessageBox(text=msg, m_type=m_type)
            self.finish(window)
            msg.exec()
        else:
            self.close()

    def updWindow(self) -> None:
        """ Перерисовать окно """

        self.__class__.app.processEvents()

    @classmethod
    def getInstance(cls) -> SplashScreen:
        """ Возвращает один и тот же экземпляр класса """

        if cls.instance is None:
            cls.instance = SplashScreen()
        return cls.instance

    @staticmethod
    def addToLog(message: str, logging_level: str):
        """ Дублирование сообщения в лог в зависимости от уровня логирования """

        if logging_level == 'CRITICAL':
            logging.critical(message)
        elif logging_level == 'ERROR':
            logging.error(message)
        elif logging_level == 'WARNING':
            logging.warning(message)
        elif logging_level == 'INFO':
            logging.info(message)
        elif logging_level == 'DEBUG':
            logging.debug(message)
        else:
            pass
