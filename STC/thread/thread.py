""" Не используется """

from PyQt5.QtCore import QThread
from STC.product.document_from_form import DocumentFromForm
from STC.product.product import Connection


class ThreadDocumentFromForm(QThread):

    def __init__(self, window):
        super(ThreadDocumentFromForm, self).__init__()
        self.window = window

    def run(self):
        connection = Connection()
        connection.close()
        connection.connect()
        DocumentFromForm(self.window)
        connection.close()
