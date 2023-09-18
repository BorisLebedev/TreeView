""" Вносит в БД данные из xlm выгрузок PLM системы """

from STC.database.database import DbDocument
from STC.database.database import DbDocumentReal
from STC.database.database import DbProduct
from STC.gui.splash_screen import SplashScreen
from STC.plm.plm import DataFromPLM
from STC.product.product import DocumentType
from STC.product.product import return_document_type


class PLMSync:
    """ Обновляет и вносит новые данные в БД
        из xlm выгрузок из PLM"""

    def __init__(self) -> None:
        self.plm_data = DataFromPLM()
        self.plm_products = self.plm_data.products
        self.plm_stages = self.plm_data.doc_stages
        DbProduct.updData()
        DbDocument.updData()
        DbDocumentReal.updData()
        SplashScreen().closeWithWindow()
        self.addProduct()
        self.addDocument()

    def addProduct(self) -> None:
        """ Внесение в БД данных об изделиях """

        products = {}
        for plm_product in self.plm_products.values():
            product = {'deno': plm_product.deno,
                       'name': plm_product.name,
                       'upd': False,
                       'generated_name': True}
            products[plm_product.deno] = product
        products = DbProduct.addDbProducts(products=products, in_cache=True)
        for plm_product in self.plm_products.values():
            plm_product.product = products[plm_product.deno]['db_product']

    def addDocument(self) -> None:
        """ Внесение в БД реквизитов документов """

        documents_real = {}
        for plm_product in self.plm_products.values():
            for plm_document in plm_product.documents.values():
                document_type = self.documentType(plm_document=plm_document)
                document = {'document_type': document_type,
                            'document_deno': plm_document.deno,
                            'product': plm_product.product,
                            'document_stage': plm_document.lifecycle.stage,
                            'file_name': plm_document.file_name,
                            'date_created': plm_document.lifecycle.date_created,
                            'name_created': plm_document.lifecycle.name_created,
                            'date_changed': plm_document.lifecycle.date_changed,
                            'name_changed': plm_document.lifecycle.name_changed}
                documents_real[plm_document.deno] = document
        documents_real = DbDocumentReal.addDbDocuments(documents=documents_real, in_cache=True)
        DbDocument.addDbDocuments(documents=documents_real, in_cache=True)

    @staticmethod
    def documentType(plm_document) -> DocumentType:
        """ Возвращает тип документа по децимальному номеру """

        document_type = return_document_type(deno=plm_document.deno)
        if document_type is None:  # Случай КД
            try:
                document_type = return_document_type(class_name='КД',
                                                     subtype_name=plm_document.d_type)
            except KeyError:
                document_type = return_document_type(class_name='КД',
                                                     subtype_name='Документы PLM')
            plm_document.deno = f'{plm_document.deno}{document_type.sign}'
        return document_type
