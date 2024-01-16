""" Создание документа по данным в форме ввода """

import logging
from datetime import datetime

from STC.database.database import DbDocument
from STC.database.database import DbProduct
from STC.database.database import DbDocumentReal
from STC.database.database import DbHierarchy
from STC.database.database import DbPrimaryApplication
from STC.database.database import DbDocumentTdComplex
from STC.gui.splash_screen import SplashScreen
from STC.gui.windows.document_add_new.window import WindowNewDocument

from STC.product.product import ProductBuilder
from STC.product.product import DocumentBuilder
from STC.product.product import ProductType
from STC.product.product import Product
from STC.product.product import DocumentType
from STC.product.product import User
from STC.product.product import return_document_type


class DocumentFromForm:

    """ Вводит реквизиты документа из формы ввода нового
        документа в БД"""

    def __init__(self, window: WindowNewDocument) -> None:
        self.window = window
        self.products = {}
        self.documents = {}
        self.product_primary = None
        self.document_type = self.setDocumentType()
        self.addProducts()
        self.product_main = self.mainProduct(db_product=self.products['main_deno']['db_product'])
        self.addPrimaryApplication()
        self.addDocuments()
        if self.document_type.subtype_name == 'Спецификация':
            self.addHierarchies()
        elif self.document_type.class_name == 'ТД':
            self.addComplex()
        self.product_main.updDocuments()
        SplashScreen().newMessage(message='Документ внесен',
                                  stage=7,
                                  stages=7,
                                  log=True,
                                  logging_level='INFO')
        SplashScreen().closeWithWindow()

    @staticmethod
    def mainProduct(db_product: DbProduct) -> Product:
        """ Создание/Обновление экземпляра класса Product для
            основного изделия к которому принадлежит вводимый документ """

        builder = ProductBuilder()
        builder.setDbProduct(db_product=db_product)
        return builder.product

    def addProducts(self) -> None:
        """ Создание изделий из данных формы ввода и
            внесение изделий в БД"""

        SplashScreen().newMessage(message='Внесение изделий',
                                  stage=0,
                                  stages=7,
                                  log=True,
                                  logging_level='INFO')
        self.addProductPrimary()
        self.addProductMain()
        self.addProductChildren()
        self.addProductChildrenNoDeno()
        self.products = DbProduct.addDbProducts(products=self.products)

    def addProductPrimary(self) -> None:
        """ Считывание реквизитов изделия, являющегося первичной применяемостью """

        product_primary_deno = self.window.structure.main_data.product_primary_application
        if product_primary_deno:
            SplashScreen().newMessage(
                message=f'Внесение изделия первичной применяемости {product_primary_deno}',
                log=True,
                logging_level='INFO')
            product_primary = {'deno': product_primary_deno}
            self.products['primary_deno'] = product_primary

    def addProductMain(self) -> None:
        """ Считывание реквизитов изделия, к которому относиться документ в форме ввода"""

        SplashScreen().newMessage(message='Внесение основного изделия',
                                  log=True,
                                  logging_level='INFO')
        product_main = {'deno': self.window.structure.main_data.product_deno,
                        'name': self.window.structure.main_data.product_name,
                        'date_check': datetime.now(),
                        'name_check': User.current_user.user_name,
                        'upd': True}
        self.products['main_deno'] = product_main

    def addProductChildren(self) -> None:
        """ Считывание реквизитов изделий, входящих в спецификацию,
            если вводимый документ является спецификацией """

        if self.document_type.subtype_name == 'Спецификация':
            for child_data in self.window.structure.spec_products.getData():
                child_deno = child_data['Обозначение']
                child_name = child_data['Наименование']
                SplashScreen().newMessage(
                    message=f'Внесение дочернего изделия {child_deno} {child_name}',
                    log=True,
                    upd_bar=False,
                    logging_level='INFO')
                product_child = {'deno': child_deno,
                                 'name': child_name}
                self.products[child_deno] = product_child

    def addProductChildrenNoDeno(self) -> None:
        """ Считывание реквизитов изделий, входящих в спецификацию,
            если вводимый документ является спецификацией и изделия
            не имеют децимального номера """

        if self.document_type.subtype_name == 'Спецификация':
            for child_data in self.window.structure.spec_products_no_deno.getData():
                child_name = child_data['Наименование']
                SplashScreen().newMessage(message=f'Внесение дочернего изделия {child_name}',
                                          log=True,
                                          upd_bar=False,
                                          logging_level='INFO')
                product_child = {'deno': child_name,
                                 'name': child_name}
                self.products[child_name] = product_child

    def addPrimaryApplication(self) -> None:
        """ Внесение в БД связи изделия с изделием,
            являющимся первичной применяемостью """

        try:
            SplashScreen().newMessage(message='Привязка первичной применяемости',
                                      log=True,
                                      logging_level='INFO')
            self.product_primary = self.products['primary_deno']['db_product']
            DbPrimaryApplication.addDbPrimaryApplication(parent=self.product_primary,
                                                         child=self.product_main.db_product)
        except KeyError:
            self.product_primary = None

    def addHierarchies(self) -> None:
        """ Внесение в БД связей родительского изделия и
            дочерних изделий в случае если документ
            является спецификацией """

        SplashScreen().newMessage(message='Привязка дочерних изделий',
                                  log=True,
                                  logging_level='INFO')
        hierarchies = {}
        children = []
        for child_data in self.getData():
            child_deno = child_data['Обозначение']
            child = {'product': self.products[child_deno]['db_product'],
                     'id_type': ProductType(child_data['Тип']).id_type,
                     'quantity': child_data['Кол-во'],
                     'unit': child_data['Ед.\nизм.']}
            children.append(child)
        if children:
            hierarchy = {'parent': self.product_main,
                         'products': children}
            hierarchies[self.product_main.db_product] = hierarchy
        DbHierarchy.addDbHierarchies(hierarchies=hierarchies, parent=self.product_main.db_product)

    def getData(self):
        """ Получение данных дочерних изделий """

        children_data = self.window.structure.spec_products.getData() + \
            self.window.structure.spec_products_no_deno.getData()
        result = {}
        for child in children_data:
            result[child['Обозначение']] = child
        return result.values()

    def addComplex(self) -> None:
        """ Внесение данных изделий, также используемых в
            документе, в случае технологических документов
            относящихся сразу к нескольким изделиям """

        SplashScreen().newMessage(message='Привязка совместно изготавливаемых',
                                  log=True,
                                  logging_level='INFO')
        builder = ProductBuilder()
        children = []

        for child_data in self.window.structure.td_complex.getData():
            child_deno = child_data['Обозначение']
            builder.getDbProductByDenotation(deno=child_deno)
            children.append(builder.product)
        document_real = self.documents['document_main']['document_real']
        DbDocumentTdComplex.updDbDocumentsTdComplex(document={'document_real': document_real,
                                                              'sub_products': children})

    def addDocuments(self) -> None:
        """ Внесение документов изделия """

        logging.info('Внесение документов')
        self.addDocumentMain()
        if self.document_type.subtype_name == 'Спецификация':
            self.addDocumentSpec()
        self.documents_real = DbDocumentReal.addDbDocuments(documents=self.documents)
        logging.info('Привязка документов к изделию')
        self.documents = DbDocument.addDbDocuments(documents=self.documents)
        self.delOutdatedSubDocuments()

    def addDocumentMain(self) -> None:
        """ Внесение реквизитов основного документа """

        document_name = self.window.structure.main_data.document_name
        document_deno = self.window.structure.main_data.document_deno
        name_created = self.window.structure.main_data.document_developer
        date_changed = self.window.structure.main_data.document_date_update
        document_stage = self.window.structure.main_data.document_stage
        try:
            date_changed = datetime.strptime(date_changed, '%d.%m.%Y')
        except ValueError:
            try:
                date_changed = datetime.strptime(date_changed, '%d.%m.%Y %H:%M')
            except ValueError:
                date_changed = None
        SplashScreen().newMessage(message='Подготовка основного документа',
                                  log=True,
                                  logging_level='INFO')
        document = {'document_type': self.document_type,
                    'document_deno': document_deno,
                    'document_name': document_name,
                    'product': self.product_main,
                    'name_created': name_created,
                    'date_changed': date_changed,
                    'document_stage': document_stage}
        self.documents['document_main'] = document

    def addDocumentSpec(self) -> None:
        """ Внесение в БД дополнительных документов, в
            случае если вносимый документ является спецификацией """

        SplashScreen().newMessage(message='Внесение документов из спецификации',
                                  log=True,
                                  logging_level='INFO')
        for subtype_name in self.window.structure.spec_documents.getData():
            document_type = return_document_type(class_name='КД', subtype_name=subtype_name)
            document_deno = self.product_main.deno + document_type.sign
            document = {'document_type': document_type,
                        'document_deno': document_deno,
                        'product': self.product_main}
            self.documents[document_deno] = document

    def delOutdatedSubDocuments(self) -> None:
        """ Аннулирование конструкторских документов, привязанных
            к изделию, но отсутствующих в спецификации """

        SplashScreen().newMessage(
            message='Аннулирование документов КД отсутствующих в спецификации',
            log=True,
            logging_level='INFO')
        db_documents = [document['db_document'] for document in self.documents.values()]
        new_documents = []
        for db_document in db_documents:
            builder = DocumentBuilder()
            builder.setDbDocument(db_document)
            new_documents.append(builder.document)

        for document in self.product_main.documents:
            if document not in new_documents and document.document_type.class_name == "КД":
                document.stage = "Аннулирован"

    def setDocumentType(self) -> DocumentType:
        """ Определение типа документа """

        SplashScreen().newMessage(message='Определение типа документа',
                                  log=True,
                                  logging_level='INFO')
        document_type = self.window.structure.main_data.d_type
        return document_type
