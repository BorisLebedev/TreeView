""" Генерация иерархического древа из данных, полученных из БД """
from dataclasses import dataclass
from STC.database.database import DbHierarchy
from STC.database.database import DbDocument
from STC.functions.func import product_quantity
from STC.product.product import ProductBuilder
from STC.product.product import DocumentBuilder
from STC.product.product import Product
from STC.product.product import ProductKind
from STC.product.product import Document
from STC.product.product import return_document_type
from STC.gui.splash_screen import SplashScreen


@dataclass
class HTreeChild:
    """ Параметры дочернего изделия по отношению к родительскому """

    child_type: str | None
    child_unit: str | None
    child_quantity: int | float | None


@dataclass
class HTreeBranch:
    """ Параметры ветви иерархического древа """

    def __lt__(self, other):
        return self.level < other.level

    name: str
    deno: str
    level: int
    product: Product
    unique_id: int
    parent_id: int
    child_data: HTreeChild


class HierarchicalTree:
    """ Хранит данные иерархического древа для определенного изделия """

    kttp = {}
    kttp_deno_only = {}
    product_kinds = {}

    def __init__(self, product_denotation: str, reverse: bool = False) -> None:
        self.product_builder = ProductBuilder()
        self.document_builder = DocumentBuilder()
        self.product_builder.getDbProductByDenotation(deno=product_denotation)
        self.product = self.product_builder.product
        self.products = {}
        self.document_types = {}  # все типы документов этой иерархии
        self.tree_dicts = [HTreeBranch(unique_id=self.product.id_product,
                                       parent_id=0,
                                       level=0,
                                       product=self.product,
                                       name=self.product.name,
                                       deno=self.product.deno,
                                       child_data=HTreeChild(
                                           child_type=None,
                                           child_quantity=None,
                                           child_unit=None)
                                       )]
        hierarchy = DbHierarchy.getHierarchy(self.product.db_product, reverse)
        self.treeData(hierarchy=hierarchy,
                      reverse=reverse)
        self.initClassVars()

    def addDocuments(self, db_documents: list[DbDocument],
                     product: Product) -> None:
        """ Инициализация экземпляров Document, отражающих
            документы изделий, входящих в древо.
            Создания словаря, хранящего все типы документов
            для данного древа """
        for db_document in db_documents:
            self.document_builder.setDbDocument(db_document)
            document = self.document_builder.document
            product.documents.add(document)
            doc_type = document.document_type
            self.document_types[f'{doc_type.sign} {doc_type.subtype_name}'] = doc_type

    def treeData(self, hierarchy: list[dict], reverse: bool) -> None:
        """ Создание списка словарей, хранящего данные древа иерархии. """
        amount = len(hierarchy)
        SplashScreen().newMessage(message='Генерация иерархии...',
                                  log=True,
                                  logging_level='DEBUG')
        for count, hierarchy_dict in enumerate(hierarchy):
            SplashScreen().changeSubProgressBar(stage=count,
                                                stages=amount)
            if hierarchy_dict['root']:
                self.addDocuments(db_documents=hierarchy_dict['db_documents'],
                                  product=self.product)
            else:
                sub_data = self.treeSubData(level=hierarchy_dict['level'],
                                            unique_id=hierarchy_dict['db_hierarchy'].id_child,
                                            parent_id=hierarchy_dict['db_hierarchy'].id_parent,
                                            db_hierarchy=hierarchy_dict['db_hierarchy'],
                                            db_documents=hierarchy_dict['db_documents'],
                                            reverse=reverse)
                self.tree_dicts.append(sub_data)
        self.tree_dicts.sort()
        SplashScreen().changeSubProgressBar(stage=0, stages=0)

    # pylint: disable=too-many-arguments
    def treeSubData(self, level: int,
                    unique_id: int,
                    parent_id: int,
                    reverse: bool,
                    db_hierarchy: DbHierarchy,
                    db_documents: list[DbDocument]) -> HTreeBranch:

        """ Создание экземпляров класса Product из данных БД и
            словаря связей между ними"""
        db_product = db_hierarchy.child
        if reverse:
            unique_id, parent_id = parent_id, unique_id
            db_product = db_hierarchy.parent

        self.product_builder.setDbProduct(db_product=db_product)
        product = self.product_builder.product

        self.addDocuments(db_documents=db_documents, product=product)
        return HTreeBranch(unique_id=unique_id,
                           parent_id=parent_id,
                           level=level,
                           product=product,
                           name=product.name,
                           deno=product.deno,
                           child_data=HTreeChild(
                               child_type=db_hierarchy.product_type.type_name,
                               child_quantity=product_quantity(
                                   str_num=db_hierarchy.quantity),
                               child_unit=db_hierarchy.unit)
                           )

    @classmethod
    def initClassVars(cls):
        """ Изменяет переменные класса
            (Списки видов изделий и типовых ТП
            для делегатов в таблице) """
        document_type = return_document_type(
            class_name='ТД',
            subtype_name='Карта типового (группового) технологического процесса',
            organization_code='2')
        if not cls.kttp:
            cls.kttp = Document.getAllDocuments(document_type=document_type)
        if not cls.kttp_deno_only:
            cls.kttp_deno_only = Document.getAllDocuments(
                document_type=document_type, only_deno=True)
        if not cls.product_kinds:
            cls.product_kinds = ProductKind.allDbKinds()
