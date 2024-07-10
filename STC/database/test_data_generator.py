""" Генерирует тестовые данные для БД """
import random
from random import randint, choice
from datetime import datetime
from STC.database.database import DbProduct
from STC.database.database import DbProductKind
from STC.database.database import DbProductType
from STC.database.database import DbPrimaryApplication
from STC.database.database import DbDocument
from STC.database.database import DbDocumentReal
from STC.database.database import DbDocumentType
from STC.database.database import DbConnection
from STC.database.database import DbExcelProject
from STC.database.database import DbHierarchy
from STC.gui.splash_screen import SplashScreen
from STC.functions.func import benchmark


def generate_test_data() -> None:
    """ Вызывает функции генерации данных """
    product_quantity = 5000
    project_quantity = 3
    max_lvl = 5
    stages = 9
    stage = 0
    stage += 1
    SplashScreen().newMessage(message='Генерация изделий',
                              stage=stage,
                              stages=stages)
    generate_products(product_quantity=product_quantity)

    stage += 1
    SplashScreen().newMessage(message='Генерация проектов',
                              stage=stage,
                              stages=stages)
    generate_projects(project_quantity=project_quantity,
                      max_lvl=max_lvl)

    stage += 1
    SplashScreen().newMessage(message='Внесение изделий в БД',
                              stage=stage,
                              stages=stages)
    db_add_products()

    stage += 1
    SplashScreen().newMessage(message='Внесение проектов в БД',
                              stage=stage,
                              stages=stages)
    db_add_projects()

    stage += 1
    SplashScreen().newMessage(message='Внесение связей изделий в БД',
                              stage=stage,
                              stages=stages)
    db_add_hierarchies()

    stage += 1
    SplashScreen().newMessage(message='Внесение первичных применяемостей в БД',
                              stage=stage,
                              stages=stages)
    db_add_primary_application()

    stage += 1
    SplashScreen().newMessage(message='Внесение документов в БД',
                              stage=stage,
                              stages=stages)
    db_add_documents_real()

    stage += 1
    SplashScreen().newMessage(message='Внесение связей документов с изделиями в БД',
                              stage=stage,
                              stages=stages)
    db_add_documents()
    DbConnection.updAllData()


@benchmark
def generate_products(product_quantity: int) -> None:
    """ Генерация изделий """

    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=product_quantity)
    for i in range(product_quantity):
        SplashScreen().changeSubProgressBar(stage=i,
                                            stages=product_quantity)
        ProductChild.createProduct()
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def generate_projects(project_quantity, max_lvl) -> None:
    """ Генерирует проекты, представляющие собой
        древа изделий """

    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=project_quantity)
    for num in range(project_quantity):
        SplashScreen().changeSubProgressBar(stage=num,
                                            stages=project_quantity)
        Project(name=f'_Проект {num}',
                max_lvl=max_lvl)
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_products():
    """ Вносит изделия в БД """
    stages = 4
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)
    products_dict = {}
    for product in Product.products.values():
        product_dict = {'name': str(product.name),
                        'deno': str(product.deno),
                        'id_kind': product.kind.id_kind,
                        }
        products_dict[product.deno] = product_dict

    SplashScreen().changeSubProgressBar(stage=2,
                                        stages=stages)
    products_dict = DbProduct.addDbProducts(products=products_dict,
                                            in_cache=True)

    SplashScreen().changeSubProgressBar(stage=3,
                                        stages=stages)
    for deno, product_dict in products_dict.items():
        Product.products[deno].db_product = product_dict['db_product']
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_projects():
    """ Вносит проекты в БД """
    stages = 3
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)

    projects_dict = {}
    for project in Project.projects.values():
        project_dict = {'project_name': project.name,
                        'product': project.main_product.db_product}
        projects_dict[project.name] = project_dict

    SplashScreen().changeSubProgressBar(stage=2,
                                        stages=stages)
    DbExcelProject.addDbProjects(projects=projects_dict)
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_hierarchies():
    """ Вносит в БД данные родитель - дети для изделий """
    stages = len(Product.products.values()) + 2
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)
    for num, product in enumerate(Product.products.values()):
        for child in product.children:
            hierarchy = DbHierarchy(
                id_parent=child.parent.db_product.id_product,
                id_child=child.product.db_product.id_product,
                id_type=child.id_type,
                quantity=child.quantity,
                unit='шт')
            DbConnection.session.add(hierarchy)
        SplashScreen().changeSubProgressBar(stage=num,
                                            stages=stages)
    DbConnection.sessionCommit()
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_primary_application():
    """ Вносит первичные применяемости в БД """
    stages = len(Product.products.values()) + 2
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)
    for num, product in enumerate(Product.products.values()):
        if product.primary_parent is not None:
            primary_application = DbPrimaryApplication(
                id_child=product.db_product.id_product,
                id_parent=product.primary_parent.db_product.id_product)
            DbConnection.session.add(primary_application)
        SplashScreen().changeSubProgressBar(stage=num,
                                            stages=stages)
    DbConnection.sessionCommit()
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_documents_real():
    """ Вносит реквизиты документов в БД """
    stages = len(Product.products.values()) + 2
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)
    for num, product in enumerate(Product.products.values()):
        for document in product.documents:
            document.db_document_real = \
                DbDocumentReal(deno=document.deno,
                               id_document_stage=document.id_stage,
                               id_type=document.db_type.id_type,
                               name=document.name,
                               file_name=document.file_name,
                               link=document.link,
                               date_created=document.date_created,
                               name_created=document.name_created,
                               date_changed=document.date_changed,
                               name_changed=document.name_changed)
            DbConnection.session.add(document.db_document_real)
        SplashScreen().changeSubProgressBar(stage=num,
                                            stages=stages)
    DbConnection.sessionCommit()
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


@benchmark
def db_add_documents():
    """ Вносит в БД связи изделие - документ"""
    stages = len(Product.products.values()) + 2
    SplashScreen().changeSubProgressBar(stage=1,
                                        stages=stages)
    for num, product in enumerate(Product.products.values()):
        for document in product.documents:
            document.db_document = \
                DbDocument(id_product=document.product.db_product.id_product,
                           id_document_real=document.db_document_real.id_document_real)
            DbConnection.session.add(document.db_document)
        SplashScreen().changeSubProgressBar(stage=num,
                                            stages=stages)
    DbConnection.sessionCommit()
    SplashScreen().changeSubProgressBar(stage=0,
                                        stages=0)


class Project:
    """ Проект, содержащий изделия и их иерархию """
    projects = {}

    def __init__(self, name, max_lvl=5):
        self.name = name
        self.max_lvl = max_lvl
        self.main_product = self.mainProduct()
        self.grandparents = set()
        self.createChildren(product=self.main_product)
        self.__class__.projects[self.name] = self

    @staticmethod
    def mainProduct():
        """ Возвращает изделие, которое будет
            корнем древа иерархии проекта """
        return Product(name=None,
                       deno='generate',
                       kind='комплекс',
                       is_project=True)

    def createChildren(self, product, hier_lvl=0):
        """ Генерирует связи родитель - дети для этого проекта """
        if hier_lvl < self.max_lvl:
            children_quantity = random.randint(3, 10)
            for _ in range(children_quantity):
                child = ProductChild(parent=product,
                                     grandparents=self.grandparents)
                if child.product is not None:
                    product.children.add(child)
                    self.grandparents.add(child.product)
                    if child.product.primary_parent is None\
                            and not child.product.is_project:
                        child.product.primary_parent = product
                        self.createChildren(product=child.product,
                                            hier_lvl=hier_lvl + 1)


class Product:
    """ Изделие генерируемое по типу,
        содержащее документы """
    # pylint: disable=too-many-instance-attributes
    products = {}
    names = {}
    product_names = ('Изделие',)
    cable_names = ('Кабель',)
    templates = {'АРМ': ('АРМ',),
                 'деталь': ('Деталь',),
                 'ЗИП': ('ЗИП',),
                 'КМЧ': ('КМЧ',),
                 'комплекс': ('Комплекс',),
                 'комплект': ('Комплект',),
                 'комплект кабелей': ('Комплект кабелей',),
                 'кабель (внутриблочный)': cable_names,
                 'кабель (межблочный)': cable_names,
                 'ПКИ': ('ПКИ',),
                 'материал': ('Материал',),
                 'неизвестно': product_names,
                 'прочее изделие': ('Прочее изделие',),
                 'сборочная единица': ('Сборочная единица',),
                 'стандартное изделие': ('Стандартное изделие',),
                 'СПО': ('СПО',),
                 'крепеж': ('Крепеж',),
                 'мех. сборка': product_names,
                 'мех. узел': product_names,
                 'эл. сборка': product_names,
                 'эл. узел': product_names,
                 'кабель': ('Кабель',),
                 'плата': ('Плата',),
                 'упаковка': ('Упаковка',),
                 'чехол': ('Чехол',)}
    document_template = {'АРМ': (0, 7, 15, 17),
                         'деталь': (6,),
                         'ЗИП': (0, 15, 17, 37),
                         'КМЧ': (1, 15, 17),
                         'комплекс': (0, 15, 17, 25, 29, 79, 140, 159),
                         'комплект': (0, 15, 17),
                         'комплект кабелей': (0,),
                         'кабель (внутриблочный)': (0, 7, 78, 158),
                         'кабель (межблочный)': (0, 7, 78, 158),
                         'ПКИ': (),
                         'материал': (),
                         'неизвестно': (),
                         'прочее изделие': (),
                         'сборочная единица': (0, 7, 15, 17),
                         'стандартное изделие': (),
                         'СПО': (0, 15, 17),
                         'крепеж': (),
                         'мех. сборка': (0, 7, 15, 17),
                         'мех. узел': (),
                         'эл. сборка': (0, 7, 10, 15, 17, 79, 159, 239),
                         'эл. узел': (),
                         'кабель': (0, 7, 79, 159),
                         'плата': (0, 15, 17, 78, 82, 158, 162),
                         'упаковка': (0, 7, 15, 17),
                         'чехол': (6,)}

    def __init__(self, deno: str, kind: str, name: str | None = None,
                 is_project: bool = False):
        self.is_project = is_project
        self.kind = DbProductKind.getData(kind)
        self.name_type = self.getName() if name is None else name
        num = self.updProducts()
        self.name = f'{self.name_type} {num}'
        self.deno = deno
        self.db_product = None
        self.primary_parent = None
        self.children = set()
        if self.deno == 'generate':
            product_deno = ProductDeno(self.name, self.kind)
            self.deno = product_deno
        self.documents = self.getDocuments()
        self.__class__.products[self.deno] = self

    def getName(self):
        """ Выбор наименования изделия в зависимости от вида """

        return choice(self.__class__.templates[self.kind.name_short])

    def updProducts(self):
        """ Возвращает порядковый номер изделия в зависимости от наименования """
        num = self.__class__.names.get(self.name_type, 1)
        self.__class__.names[self.name_type] = num + 1
        return num

    def getDocuments(self):
        """ Добавление документов к изделию в зависимости от вида изделия """
        document_type_ids = \
            self.__class__.document_template[self.kind.name_short]
        documents = []
        for id_type in document_type_ids:
            document = Document(product=self,
                                id_type=id_type)
            documents.append(document)
        return documents


class ProductDeno:
    """ Децимальный номер изделия """
    denos = {}
    errors = 0
    templates = {'АРМ': '46',
                 'деталь': '7',
                 'ЗИП': '46',
                 'КМЧ': '46',
                 'комплекс': '46',
                 'комплект': '46',
                 'комплект кабелей': '46',
                 'кабель (внутриблочный)': '46',
                 'кабель (межблочный)': '46',
                 'ПКИ': 'наименование',
                 'материал': 'наименование',
                 'неизвестно': '',
                 'прочее изделие': 'наименование',
                 'сборочная единица': '',
                 'стандартное изделие': 'наименование',
                 'СПО': 'СПО',
                 'крепеж': 'наименование',
                 'мех. сборка': '43',
                 'мех. узел': '30',
                 'эл. сборка': '43',
                 'эл. узел': '43',
                 'кабель': '68',
                 'плата': '46',
                 'упаковка': '46',
                 'чехол': '32'}

    def __repr__(self):
        return self._deno

    def __init__(self, name: str, kind: DbProductKind):
        self._kind = kind
        self.name = name
        self._deno = self.genDeno()
        self.__class__.denos[self._deno] = self

    def genDeno(self) -> str:
        """ Генерирует свободный децимальный номер
            исходя из типа изделия """
        template = self.__class__.templates[self._kind.name_short]
        manufacturer = self.genDenoManufacturer(template)
        product_type = self.genDenoProductType(template)
        main_number = self.genDenoMainNumber(template)
        deno = self.combineDeno(manufacturer,
                                product_type,
                                main_number,
                                template)
        if deno in self.__class__.denos:
            self.__class__.errors += 1
            print(f'deno error = {self.__class__.errors}')
            deno = self.genDeno()
        return deno

    def combineDeno(self, manufacturer: str,
                    product_type: str,
                    main_number: str,
                    template: str) -> str:
        """ Возвращает децимальный номер изделия """
        if template == 'наименование':
            return self.name
        match self._kind.name_short:
            case 'СПО':
                return f'{manufacturer}.{product_type}-{main_number}'
            case _:
                return '.'.join([manufacturer,
                                 product_type,
                                 main_number])

    @staticmethod
    def genDenoManufacturer(template: str) -> str:
        """ Возвращает код производителя для децимального номера """
        match template:
            case 'наименование':
                return ''
            case _:
                return 'АБВГ'

    @staticmethod
    def genDenoProductType(template: str) -> str:
        """ Возвращает код вида изделия для децимального номера """
        match template:
            case 'СПО':
                return ''.join([str(randint(0, 9))
                                for _ in range(5)])
            case 'наименование':
                return ''
            case _:
                nums = ''.join([str(randint(0, 9))
                                for _ in range(6 - len(template))])
                return ''.join([template, nums])

    @staticmethod
    def genDenoMainNumber(template: str) -> str:
        """ Возвращает порядковый номер для децимального номера """
        match template:
            case 'СПО':
                return ''.join([str(randint(0, 9))
                                for _ in range(2)])
            case 'наименование':
                return ''
            case _:
                return ''.join([str(randint(0, 9))
                                for _ in range(3)])


class ProductChild:
    """ Дочернее изделие с количеством и
        разделом спецификации """
    products_without_children = ('материал',
                                 'прочее изделие',
                                 'стандартное изделие',
                                 'крепеж',
                                 'ПКИ',
                                 'деталь',
                                 'кабель (внутриблочный)',
                                 'кабель (межблочный)',
                                 'СПО',
                                 'мех. узел',
                                 'кабель',
                                 'плата',
                                 'чехол')

    templates = {'АРМ': 'сборочная единица',
                 'деталь': 'деталь',
                 'ЗИП': 'комплект',
                 'КМЧ': 'комплект',
                 'комплекс': 'комплекс',
                 'комплект': 'комплект',
                 'комплект кабелей': 'комплект',
                 'кабель (внутриблочный)': 'сборочная единица',
                 'кабель (межблочный)': 'сборочная единица',
                 'ПКИ': 'прочее изделие',
                 'материал': 'материал',
                 'неизвестно': 'неизвестно',
                 'прочее изделие': 'прочее изделие',
                 'сборочная единица': 'сборочная единица',
                 'стандартное изделие': 'стандартное изделие',
                 'СПО': 'комплект',
                 'крепеж': 'стандартное изделие',
                 'мех. сборка': 'сборочная единица',
                 'мех. узел': 'сборочная единица',
                 'эл. сборка': 'сборочная единица',
                 'эл. узел': 'сборочная единица',
                 'кабель': 'сборочная единица',
                 'плата': 'сборочная единица',
                 'упаковка': 'сборочная единица',
                 'чехол': 'сборочная единица'}

    def __init__(self, parent: Product, grandparents: set[Product]):
        self.parent = parent
        self.product = None
        if self.parent.kind.name_short not in \
                self.__class__.products_without_children:
            self.product = self.randomProduct(used_products=grandparents)
            if self.product is not None:
                product_type = self.__class__.templates[self.product.kind.name_short]
                self.id_type = DbProductType.getData(
                    product_type=product_type).id_type
            self.quantity = randint(1, 10)

    @staticmethod
    def createProduct():
        """ Создает изделие случайного вида """
        kinds = list(ProductDeno.templates.keys())
        kinds.remove('неизвестно')
        kind = random.choice(kinds)
        return Product(name=None,
                       deno='generate',
                       kind=kind)

    def randomProduct(self, used_products: set[Product]) -> Product | None:
        """ Выбирает случайное изделие из списка изделий, но не
            используемое в ветке иерархического древа,
            чтобы избежать бесконечной рекурсии """
        used_products.add(self.parent)
        products = set(Product.products.values()).difference(used_products)
        product = None
        if products:
            product = random.choice(tuple(products))
        return product


class Document:
    """ Отображает реквизиты реальных документов
        и связывает документы с определенным изделием"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, product: Product, id_type: int):
        self.product = product
        self.db_type = DbDocumentType.data.get(id_type, None)
        self.deno = self.getDeno()
        self.name = self.getName()
        self.id_stage = 1
        self.db_document_real = None
        self.db_document = None
        self.file_name = ''
        self.link = ''
        self.date_created = datetime.now()
        self.name_created = ''
        self.date_changed = datetime.now()
        self.name_changed = ''

    def getDeno(self):
        """ Возвращает децимальный номер документа """
        if self.db_type.sign is None:
            return f'{self.product.deno}'
        return f'{self.product.deno}{self.db_type.sign}'

    def getName(self):
        """ Возвращает наименование документа """
        if self.db_type.subtype_name == 'Спецификация':
            return self.product.name
        return ''
