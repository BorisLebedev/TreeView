""" Внесение импортированных из Excel иерархических составов в БД """
# pylint: disable=invalid-name

import logging
from STC.database.database import DbDocument
from STC.database.database import DbDocumentReal
from STC.database.database import DbDocumentTdComplex
from STC.database.database import DbExcelProject
from STC.database.database import DbHierarchy
from STC.database.database import DbMkExcel
from STC.database.database import DbMkExcelSentences
from STC.database.database import DbPrimaryApplication
from STC.database.database import DbProduct
from STC.excel.xl_import.hierarchy import ExcelData
from STC.excel.xl_import.document_db import ExcelRawDataFromTdDb
from STC.functions.func import is_complex
from STC.gui.splash_screen import SplashScreen
from STC.product.product import DocumentTypeBuilder
from STC.product.product import return_document_type


class ExcelSync:

    """ Переводит данные об иерархии изделий из
        списков КД и ТД в БД.

        Примеры представления данных:
        ExcelData.documents_td = {'АБВГ.10100.12345': 'Проект 1',
                                  'АБВГ.10100.54321': 'Проект 1',
                                  'АБВГ.55200.12345': 'Проект 2',
                                  'АБВГ.55200.54321': 'Проект 3'}

        ExcelData.products = {'АБВГ.123456.789': ExcelProduct1,
                              'АБВГ.123456.987': ExcelProduct2}

        ExcelProduct.name = "АЦРП"
        ExcelProduct.deno = "АБВГ.123456.789"
        ExcelProduct.index = "1.1"
        ExcelProduct.documents_td = {'АБВГ.552000.00001','АБВГ.552000.00002','АБВГ.552000.00003'}
        ExcelProduct.document_signs = ['СП','СБ','Э4']
        ExcelProduct.subproducts = [ExcelSubProduct1, ExcelSubProduct2, ExcelSubProduct3]"""

    def __init__(self) -> None:
        self.document_type_builder = DocumentTypeBuilder()
        stages = 10
        SplashScreen().newMessage(message='Импорт данных Excel...', stage=0, stages=stages)
        self.excel_data = ExcelData()

        SplashScreen().newMessage(message='Внесение первичных применяемостей как изделий...')
        self.addProductsPrimaryApplication()

        SplashScreen().newMessage(message='Внесение изделий...')
        self.addProducts()

        SplashScreen().newMessage(message='Привязка первичных применяемостей...')
        self.addPrimaryApplication()

        SplashScreen().newMessage(message='Привязка дочерних изделий...')
        self.addChildren()

        SplashScreen().newMessage(message='Внесение документов по спецификациям...')
        self.addDocumentsKD()

        SplashScreen().newMessage(message='Внесение технологических документов...')
        self.addExcelDocumentTdFromProjects()
        self.addExcelMkData()

        SplashScreen().newMessage(message='Внесение проектов...')
        self.addExcelProjects()
        SplashScreen().closeWithWindow()

    def addProductsPrimaryApplication(self) -> None:
        """ Вносит первичную применяемость изделия в таблицу Product в БД
            Добавляет экземпляр product_primary_application как аттрибут ExcelProduct для
            быстрого обращения к нему в последующих методах
            ExcelData.products = {'АБВГ.123456.789': ExcelProduct1,
                                  'АБВГ.123456.987': ExcelProduct2}"""
        products = {}
        for excel_product in self.excel_data.products.values():
            if excel_product.is_new:
                product = {'deno': excel_product.primary_application,
                           'purchased': ''}
                products[excel_product.primary_application] = product
        products = DbProduct.addDbProducts(products=products)
        for excel_product in self.excel_data.products.values():
            if excel_product.is_new:
                excel_product.product_primary_application = \
                    products[excel_product.primary_application]['db_product']

    def addProducts(self) -> None:
        """ Вносит все изделия в таблицу Product в БД.
            Добавляет экземпляр product как аттрибут ExcelProduct для
            быстрого обращения к нему в последующих методах
            ExcelData.products = {'АБВГ.123456.789': ExcelProduct1,
                                  'АБВГ.123456.987': ExcelProduct2}"""
        products = {}
        for excel_product in self.excel_data.products.values():
            product = {'deno': excel_product.deno,
                       'name': excel_product.name,
                       # 'purchased': excel_product.purchased,
                       'id_kind': excel_product.id_kind,
                       'date_check': excel_product.upd_date,
                       'upd': True}
            products[excel_product.deno] = product
        products = DbProduct.addDbProducts(products=products)
        for excel_product in self.excel_data.products.values():
            excel_product.product = products[excel_product.deno]['db_product']

    def addPrimaryApplication(self) -> None:
        """ Вносит данные по первичной применяемости
            для определенного изделия"""
        products = {}
        for excel_product in self.excel_data.products.values():
            if excel_product.is_new:
                product = {'parent': excel_product.product_primary_application,
                           'child': excel_product.product}
                products[excel_product.deno] = product
        DbPrimaryApplication.addDbPrimaryApplications(products=products)

    def addChildren(self) -> None:
        """ Вносит дочерние изделия в таблицу Product и
            вносит запись об их вхождении, типе и количестве в
            родительское изделие в таблицу Hierarchy. """
        hierarchies = {}
        for excel_product in self.excel_data.products.values():
            if excel_product.is_new:
                children = []
                for excel_subproduct in set(excel_product.subproducts):
                    subproduct = self.excel_data.products[excel_subproduct.deno].product
                    child = {'product': subproduct,
                             'id_type': excel_subproduct.product_type.id_type,
                             'quantity': excel_subproduct.quantity}
                    children.append(child)
                if children and excel_product.product.date_check >= excel_product.upd_date:
                    hierarchy = {'parent': excel_product.product,
                                 'products': children}
                    hierarchies[excel_product.product] = hierarchy
        if hierarchies:
            DbHierarchy.addDbHierarchies(hierarchies=hierarchies)

    def addDocumentsKD(self) -> None:
        """ Определяет вид документа по обозначению и вносит документ в БД """
        documents_real = {}
        for excel_product in self.excel_data.products.values():
            if excel_product.is_new:
                for document_sign in excel_product.document_signs:
                    logging.debug(document_sign)
                    self.document_type_builder.getDocumentType(sign=document_sign, class_name='КД')
                    document_type = self.document_type_builder.document_type
                    sign = document_type.sign if document_type.sign else ''
                    document_deno = excel_product.product.deno + sign
                    document = {'document_type': document_type,
                                'document_deno': document_deno,
                                'product': excel_product.product}
                    documents_real[document_deno] = document
        documents_real = DbDocumentReal.addDbDocuments(documents=documents_real)
        DbDocument.addDbDocuments(documents=documents_real)

    def addExcelProjects(self) -> None:
        """ Вносит проекты в БД """
        projects = {}
        for excel_product in self.excel_data.products.values():
            project_name = excel_product.main_project
            if project_name:
                project = {'project_name': project_name,
                           'product': excel_product.product}
                projects[project_name] = project
        DbExcelProject.addDbProjects(projects=projects)

    def addExcelDocumentTdFromProjects(self) -> None:
        """ Вносит документы в БД"""
        documents_real = {}
        for excel_product in self.excel_data.products.values():
            for td_deno in excel_product.documents_td.keys():
                try:
                    self.document_type_builder.getDocumentType(deno=td_deno)
                    document_type = self.document_type_builder.document_type
                    if not is_complex(deno=td_deno):
                        document = {'document_type': document_type,
                                    'document_deno': td_deno,
                                    'product': excel_product.product}
                        key = f'{td_deno}{excel_product.product.deno}'
                        documents_real[key] = document
                except AttributeError:
                    if td_deno != 'Неизвестно':
                        msg = f'Не определить тип ТП: {td_deno}'
                        logging.info(msg)
        documents_real = DbDocumentReal.addDbDocuments(documents=documents_real)
        documents = DbDocument.addDbDocuments(documents=documents_real)
        for excel_product in self.excel_data.products.values():
            excel_product.db_documents = {}
            for td_deno in excel_product.documents_td.keys():
                try:
                    key = f'{td_deno}{excel_product.product.deno}'
                    excel_product.db_documents.update({td_deno: documents[key]['db_document']})
                except KeyError:
                    excel_product.db_documents.update({td_deno: None})

    def addExcelMkData(self) -> None:
        """ Вносит данные маршрутной карты """
        mk_excel_data = {}
        for excel_product in self.excel_data.products.values():
            for document_td in excel_product.documents_td.values():
                if document_td.mk_code:
                    db_document = excel_product.db_documents[document_td.td_deno]
                    key = document_td.td_deno
                    mk_excel_data[key] = {
                        'code': document_td.mk_code,
                        'kind': document_td.td_type,
                        'area': document_td.mk_place,
                        'sentences': document_td.operations,
                        'id_document_real': db_document.document_real.id_document_real}
        mk_excel_data = DbMkExcel.addMkExcelMultiple(data=mk_excel_data)
        self.addExcelMkSentencesData(mk_excel_data=mk_excel_data)

    @staticmethod
    def addExcelMkSentencesData(
            mk_excel_data: dict[str, dict[str, int | DbMkExcel | dict[str, str]]]) -> None:
        """ Вносит измененный текст маршрутной карты """
        mk_excel_sentences_data = {}
        for dict_item in mk_excel_data.values():
            if dict_item['sentences']:
                for number, code_and_text in dict_item['sentences'].items():
                    id_mk_excel = dict_item['db_mk_excel'].id_mk_excel
                    code = code_and_text[0]
                    text = code_and_text[1]
                    key = f'{id_mk_excel}{number}'
                    mk_excel_sentences_data[key] = {'id_mk_excel': id_mk_excel,
                                                    'number': number,
                                                    'code': code,
                                                    'text': text}
        DbMkExcelSentences.addMkExcelSentencesMultiple(data=mk_excel_sentences_data)


class ExcelDataFromTdDb:

    """ Обновляет и вносит данные в БД из
        файла "База ТД.xlsm" """

    def __init__(self) -> None:
        self.complex_documents = {}
        self.documents_real = {}
        self.documents = {}
        DbProduct.updData()
        DbDocument.updData()
        DbDocumentReal.updData()
        self.excel_data = ExcelRawDataFromTdDb()
        self.addExcelProduct()
        self.addDocumentReal()
        self.addDocument()
        self.addDocumentComplex()

    def addExcelProduct(self) -> None:
        """ Внесение изделий в БД """
        products = {}
        for num, excel_document in enumerate(self.excel_data.documents):
            SplashScreen().newMessage(message=f'Подготовка изделий...\n'
                                              f'{excel_document.product.deno}',
                                      upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=num,
                                                stages=len(self.excel_data.documents))
            product = {'deno': excel_document.product.deno,
                       'name': excel_document.product.name}
            products[excel_document.product.deno] = product
        SplashScreen().close()
        products = DbProduct.addDbProducts(products=products)
        for excel_document in self.excel_data.documents:
            excel_document.db_product = products[excel_document.product.deno]['db_product']

    def addDocumentReal(self) -> None:
        """ Внесение документов В БД """
        for num, excel_document in enumerate(self.excel_data.documents):
            SplashScreen().newMessage(message=f'Подготовка документов этап 1 ...\n'
                                              f'{excel_document.document.deno} ',
                                      upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=num,
                                                stages=len(self.excel_data.documents))
            excel_document.document_type = return_document_type(deno=excel_document.document.deno)
            excel_document.document.complex = False
            excel_document.deno_error = False
            if excel_document.document_type is None:
                excel_document.deno_error = True
            else:
                excel_document.document.complex = is_complex(deno=excel_document.document.deno)
                if excel_document.document.complex:
                    parent_deno_td = excel_document.document.deno.replace(' ', '')[len('Всоставе'):]
                    try:
                        self.complex_documents[parent_deno_td].append(excel_document.db_product)
                    except KeyError:
                        self.complex_documents[parent_deno_td] = [excel_document.db_product]
                else:
                    document = {'document_type': excel_document.document_type,
                                'document_deno': excel_document.document.deno,
                                'document_name': excel_document.product.name,
                                'document_stage': excel_document.document.stage,
                                'name_created': excel_document.reg_person.fio}
                    self.documents_real[excel_document.document.deno] = document
        SplashScreen().close()
        self.documents_real = DbDocumentReal.addDbDocuments(documents=self.documents_real)
        for excel_document in self.excel_data.documents:
            try:
                excel_document.db_document_real = \
                    self.documents_real[excel_document.document.deno]['document_real']
            except KeyError:
                pass

    def addDocument(self) -> None:
        """ Внесение связей документов и изделий в БД """
        for num, excel_document in enumerate(self.excel_data.documents):
            SplashScreen().newMessage(message=f'Подготовка документов этап 2 ...\n'
                                              f'{excel_document.document.deno}',
                                      upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=num,
                                                stages=len(self.excel_data.documents))
            if not excel_document.document.complex and not excel_document.deno_error:
                document = {'product': excel_document.db_product,
                            'document_real': excel_document.db_document_real}
                self.documents[excel_document.document.deno] = document
        SplashScreen().close()
        DbDocument.addDbDocuments(documents=self.documents)

    def addDocumentComplex(self) -> None:
        """ Внесение связанных изделий в составном документе """
        complex_documents = {}
        for num, parent_deno_td in \
                enumerate(self.complex_documents.keys()):
            SplashScreen().newMessage(
                message=f'Подготовка составных технологических процессов ...\n'
                        f'{parent_deno_td}',
                upd_bar=False)
            SplashScreen().changeSubProgressBar(stage=num,
                                                stages=len(self.complex_documents))
            sub_products = self.complex_documents[parent_deno_td]
            document_real = self.documents_real[parent_deno_td]['document_real']
            complex_document = {'document_real': document_real,
                                'sub_products': sub_products}
            complex_documents[document_real] = complex_document
        SplashScreen().close()
        DbDocumentTdComplex.clearDocumentTdComplex()
        DbDocumentTdComplex.addDbDocumentsTdComplex(documents=complex_documents)
