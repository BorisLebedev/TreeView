"""  """

from __future__ import annotations
import logging
import re
from datetime import datetime
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QFontMetrics

from STC.config.config import CONFIG
from STC.config.config import CFG_DB
from STC.database.database import DbArea
from STC.database.database import DbConnection
from STC.database.database import DbDocDef
from STC.database.database import DbDocDoc
from STC.database.database import DbDocument
from STC.database.database import DbDocumentReal
from STC.database.database import DbDocumentStage
from STC.database.database import DbDocumentSignature
from STC.database.database import DbDocumentType
from STC.database.database import DbEquipment
from STC.database.database import DbEquipmentDef
from STC.database.database import DbEquipmentDoc
from STC.database.database import DbExcelProject
from STC.database.database import DbHierarchy
from STC.database.database import DbIOT
from STC.database.database import DbIOTDef
from STC.database.database import DbIOTDoc
from STC.database.database import DbMaterial
from STC.database.database import DbMaterialDef
from STC.database.database import DbMaterialDoc
from STC.database.database import DbOperation
from STC.database.database import DbOperationDef
from STC.database.database import DbOperationDoc
from STC.database.database import DbProduct
from STC.database.database import DbProductKind
from STC.database.database import DbProductType
from STC.database.database import DbProfession
from STC.database.database import DbPrimaryApplication
from STC.database.database import DbRig
from STC.database.database import DbRigDef
from STC.database.database import DbRigDoc
from STC.database.database import DbSentence
from STC.database.database import DbSentenceDoc
from STC.database.database import DbSetting
from STC.database.database import DbSettingDef
from STC.database.database import DbUsers
from STC.database.database import DbWorkplace
from STC.functions.func import add_missing_keys
from STC.functions.func import date_format
from STC.functions.func import sort_un
from STC.gui.splash_screen import SplashScreen


def updDataFromDb() -> None:
    """  """

    DbConnection.updAllData()


def return_document_type(class_name: str = None,
                         subtype_name: str = None,
                         method_code: str = None,
                         organization_code: str = None,
                         sign: str = None,
                         deno: str = None,
                         db_document_type: DbDocumentType = None) -> DocumentType | None:
    """ Возвращает тип документа """

    if subtype_name == 'Карта типового технологического процесса':
        subtype_name = 'Карта типового (группового) технологического процесса'
        organization_code = '2'
    if subtype_name == 'Карта группового технологического процесса':
        subtype_name = 'Карта типового (группового) технологического процесса'
        organization_code = '3'
    builder = DocumentTypeBuilder()
    try:
        builder.getDocumentType(class_name=class_name,
                                subtype_name=subtype_name,
                                method_code=method_code,
                                organization_code=organization_code,
                                sign=sign,
                                deno=deno,
                                db_document_type=db_document_type)
        return builder.document_type
    except AttributeError as err:
        msg = f'Не определить тип документации ' \
              f'class_name: {class_name},' \
              f'subtype_name: {subtype_name},' \
              f'method_code: {method_code},' \
              f'organization_code: {organization_code},' \
              f'sign: {sign},' \
              f'deno: {deno},' \
              f'db_document_type: {db_document_type}'
        logging.error(msg)
        return None


class Connection:
    """ Управление подключением к БД """

    def __init__(self) -> None:
        self.path = CFG_DB.main.folder
        self.name = CFG_DB.main.file_name
        self.connect()
        DbConnection.updAllData()

    def close(self) -> None:
        """ Закрытие соединения с БД """

        DbConnection.session.close()

    def update(self) -> None:
        """ Обновление подключения к БД.
            Загрузка актуальных данных """

        self.resetBuilders()
        self.close()
        DbConnection.initSession(self.path, self.name)
        DbConnection.updAllData()

    def connect(self) -> None:
        """ Подключение к БД """

        SplashScreen().newMessage(message=f'Подключение к базе данных {self.path}\{self.name}',
                                  log=True,
                                  logging_level='INFO')
        DbConnection.initSession(self.path, self.name)

    def resetBuilders(self) -> None:
        """ Сброс хранимых в конструкторах
            экземпляров классов """

        ProductBuilder.products = {}
        DocumentBuilder.documents = {}
        OperationBuilder.operations = {}
        DocumentTypeBuilder.document_types = {}
        IotBuilder.iots = {}
        RigBuilder.rigs = {}
        EquipmentBuilder.equipments = {}
        MatBuilder.mats = {}
        AreaBuilder.areas = {}
        WorkplaceBuilder.workplaces = {}
        ProfessionBuilder.professions = {}


class ProductBuilder:
    """ Конструктор для класса Product
        Создает уникальные экземпляры Product по:
        1) децимальному номеру изделия
        2) экземпляру ORM класса DbProduct """

    products = {}

    def __init__(self) -> None:
        self._product = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Product без привязки
            к экземпляру ORM класса (реальному изделию в БД) """

        self._product = Product()

    @property
    def product(self) -> Product:
        """ Возвращает экземпляр Product,
            сохраняет его как используемый и
            создает новый экземпляр Product
            без привязки к определенному изделию из БД """

        product = self._product
        self.__class__.products.update({product.db_product.id_product: product})
        self.reset()
        return product

    def ifExists(self, db_product: DbProduct):
        """ Создавался ли экземпляр Product c id_product
            Если нет, то записывает экземпляр ORM класса
            в качестве аттрибута экземпляра Product """

        try:
            self._product = self.__class__.products[db_product.id_product]
        except KeyError:
            self._product.db_product = db_product

    def getDbProductByDenotation(self, deno: str) -> None:
        """ Ищет ORM класс с определенным децимальным номером.
            Вызывает метод, проверяющий создавался ли Product
            для этого изделия """

        db_product = DbProduct.getData(deno=deno)
        self.ifExists(db_product)

    def setDbProduct(self, db_product: DbProduct) -> None:
        """ Сразу вызывает метод, проверяющий создавался ли
            экземпляр Product для определенного изделия из БД
            Для получения экземпляра Product если
            экземпляр ORM класса уже известен """

        self.ifExists(db_product)


class DocumentBuilder:
    """ Конструктор для класса Document
        Создает уникальные экземпляры Document по:
        1) экземпляру ORM класса DbDocument """

    documents = {}

    def __init__(self) -> None:
        self._document = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Document без привязки
            к экземпляру ORM класса """

        self._document = Document()

    @property
    def document(self) -> Document:
        """ Возвращает экземпляр Document,
            сохраняет его как используемый и
            создает новый экземпляр Document
            без привязки к определенному документу из БД """

        document = self._document
        self.__class__.documents.update({document.db_document.id_document: document})
        self.reset()
        return document

    def ifExists(self, db_document: DbDocument) -> None:
        """ Создавался ли экземпляр Document c id_document
            Если нет, то записывает экземпляр ORM класса
            в качестве аттрибута экземпляра Document """

        try:
            self._document = self.__class__.documents[db_document.id_document]
        except KeyError:
            self._document.db_document = db_document

    def setDbDocument(self, db_document: DbDocument) -> None:
        """ Сразу вызывает метод, проверяющий создавался ли
            экземпляр Document для этого документа из БД.
            (Для получения экземпляра Document если
            экземпляр ORM класса уже известен) """

        self.ifExists(db_document)


class OperationBuilder:
    """ Конструктор для класса Operation
        Создает уникальные экземпляры Operation по:
        1) экземпляр Document + порядковый № """

    operations = {}

    def __init__(self) -> None:
        self._area_builder = AreaBuilder()
        self._workplace_builder = WorkplaceBuilder()
        self._profession_builder = ProfessionBuilder()
        self._operation = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Operation
            без привязки к данным БД """

        self._operation = Operation()

    @property
    def operation(self) -> Operation:
        """ Возвращает экземпляр Operation,
            сохраняет его как используемый и
            создает новый экземпляр Operation
            без привязки к данным из БД """

        operation = self._operation
        key = (operation.document_main,
               operation.order)
        self.__class__.operations.update({key: operation})
        self.reset()
        return operation

    @classmethod
    def cleanOperationByDocument(cls, document: Document) -> None:
        """ Удаляет из словаря экземпляров Operation
            операции в определенном документе """

        keys_for_del = []
        for key in OperationBuilder.operations.keys():
            if key[0] == document:
                keys_for_del.append(key)
        for key in keys_for_del:
            del OperationBuilder.operations[key]

    def ifExists(self, document: Document,
                 name: str,
                 order: int,
                 new: bool) -> None:
        """ Проверяет наличие или создает операцию с
            наименованием и порядковым номером для
            определенного документа """

        key = (document, order)
        if key in self.__class__.operations:
            self._operation = self.__class__.operations[key]
        else:
            self.initOperation(document=document,
                               name=name,
                               order=order,
                               new=new)

    def createOperation(self, document: Document,
                        name: str,
                        order: int,
                        new: bool = False) -> None:
        """ Проверяет наличие или создает операцию с
            наименованием и порядковым номером для
            определенного документа """

        self.ifExists(document, name, order, new)

    def initOperation(self, document: Document,
                      name: str,
                      order: int,
                      new: bool) -> None:
        """ Создает операцию с наименованием и
            порядковым номером для определенного документа """

        # DbOperationDoc.updData()
        DbOperationDoc.updCheck()
        DbOperation.updCheck()
        self.initOperationDocument(document)
        self.initOperationDefData(name)
        self.initOperationDocData(order=order, new=new)

    def initOperationDocument(self, document: Document) -> None:
        """ Привязывает операцию к определенному документу"""

        self._operation._document_main = document

    def initOperationDefData(self, name: str) -> None:
        """ Задает данные по умолчанию для операции по
            ее наименованию """

        key = name
        if key in DbOperation.data:
            self._operation._def_operation = DbOperation.data[key]
            try:
                self._operation._def_area = self._operation.possibleAreas()[0]
            except IndexError:
                pass
            try:
                self._operation._def_workplace = self._operation.possibleWorkplaces()[0]
            except IndexError:
                pass
            try:
                self._operation._def_profession = self._operation.possibleProfessions()[0]
            except IndexError:
                pass
            self._operation._def_settings = self._operation.settings
            self._operation._sentences = self._operation.sentences
        else:
            logging.warning(f'Базовая операция с наименованием {name} не найдена')

    def initOperationDocData(self, order: int, new: bool) -> None:
        """ Если операция не является намеренно новой или созданной
            взамен другой операции, то определяются дополнительные параметры
            определенной операции """

        self._operation._order = order
        # if self._operation.db_operation_doc is not None:
        if not new:
            self._operation._db_operation_doc = self.dbOperationDoc(operation=self._operation)
            if self._operation._db_operation_doc is not None:
                self.initArea()
                self.initWorkplace()
                self.initProfession()
            else:
                msg = f'Операция с наименованием {self._operation.name} ' \
                      f'и порядковым номером {self._operation.order} ' \
                      f'отсутствует в документе {self._operation.document_main.deno}'
                logging.warning(msg)

    def initArea(self) -> None:
        """ Участок для операции не по умолчанию """

        self._area_builder.createArea(self._operation.db_operation_doc.area.name)
        self._operation._doc_area = self._area_builder.area

    def initWorkplace(self) -> None:
        """ Рабочее место для операции не по умолчанию """

        self._workplace_builder.createWorkplace(self._operation.db_operation_doc.workplace.name)
        self._operation._doc_workplace = self._workplace_builder.workplace

    def initProfession(self) -> None:
        """ Профессия исполнителя для операции не по умолчанию """

        self._profession_builder.createProfession(self._operation.db_operation_doc.profession.name)
        self._operation._doc_profession = self._profession_builder.profession

    def delOperation(self, operation: Operation) -> None:
        """ Удаление операции """

        key = (operation.document_main,
               operation.order)
        del OperationBuilder().operations[key]
        if operation.db_operation_doc:
            DbOperationDoc().delData(item=operation.db_operation_doc)

    def dbOperationDoc(self, operation: Operation):
        """ Поиск экземпляра ORM класса DbOperationDoc
            для данных операции в определенном документе
            под определенным порядковым номером """

        try:
            key = (operation.document_main.id_document_real,
                   operation.default_operation.id_operation,
                   operation.order)
            return DbOperationDoc.data.get(key, None)
        except AttributeError:
            return None


class DocumentTypeBuilder:
    """ Конструктор для класса DocumentType
        Создает уникальные экземпляры DocumentType по:
        1) Децимальный номер
        2) КД/ТД + наименование вида документа
        3) Экземпляр DbDocumentType """

    document_types = {}
    _exceptions = {'Структурная схема изделия': 'Схема деления структурная',
                   'Таблица соединений': 'Таблица',
                   'Схема электрокинематическая расположения': 'Схема комбинированная расположения',
                   'Конструкторский документ': 'Документы PLM'}
    _type_codes = {}
    _type_codes_inv = {}
    _method_codes = {}
    _method_codes_inv = {}
    _organization_codes = {}
    _organization_codes_inv = {}
    _config = CONFIG

    def __init__(self) -> None:
        self._document_type = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр DocumentType
            без привязки к данным БД """

        self._document_type = DocumentType()

    @property
    def document_type(self) -> DocumentType:
        """ Возвращает экземпляр DocumentType,
            сохраняет его как используемый и
            создает новый экземпляр DocumentType
            без привязки к данным из БД """

        document_type = self._document_type
        key = (document_type.document_type,
               document_type.method_code,
               document_type.organization_code)
        self.__class__.document_types.update({key: document_type})
        self.reset()
        return document_type

    def ifExists(self, db_document_type: DbDocumentType,
                 method_code: str,
                 organization_code: str) -> None:
        """ Проверяет наличие или создает экземпляр
            класса DocumentType (тип документа) """

        key = (db_document_type, method_code, organization_code)
        if key in self.__class__.document_types:
            self._document_type = self.__class__.document_types[key]
        else:
            self.initDocumentType(db_document_type=db_document_type,
                                  method_code=method_code,
                                  organization_code=organization_code)

    def getDocumentType(self, class_name: str = None,
                        subtype_name: str = None,
                        method_code: str = None,
                        organization_code=None,
                        sign: str = None,
                        deno: str = None,
                        db_document_type: DbDocumentType = None) -> None:
        """ Определяет экземпляр класса DbDocumentType
            (ORM представление типа документа из БД) и
            вызывает метод, который проверяет наличие
            или создает экземпляр класса DocumentType """

        if deno:
            db_document_type, organization_code, method_code = self.typeByDeno(deno)
        if db_document_type is None:
            if class_name and subtype_name:
                if class_name in self.__class__._exceptions:
                    class_name = self.__class__._exceptions[class_name]
                db_document_type = DbDocumentType.data[(class_name, subtype_name)]
            elif class_name and sign:
                sign = sign.upper()
                try:
                    db_document_type = DbDocumentType.data[(class_name, sign)]  # Точное соответствие только для КД
                except KeyError:
                    db_document_type = DbDocumentType.data[('КД', 'Спецификация')]
            elif class_name == 'КД' and sign is None:
                db_document_type = DbDocumentType.data[('КД', 'Спецификация')]
        if db_document_type is not None:
            self.ifExists(db_document_type, method_code, organization_code)
        else:
            raise AttributeError('Тип документа не определен.')

    def initDocumentType(self, db_document_type: DbDocumentType,
                         method_code: str,
                         organization_code: str) -> None:
        """ Инициализация параметров экземпляра DocumentType """

        if db_document_type.class_name == 'ТД':
            type_code = self.type_codes[db_document_type.subtype_name]
            self._document_type._type_code = type_code
            self._document_type._subtype_name = self.type_codes_inv.get(type_code, None)
        else:
            self._document_type._type_code = None
        self._document_type._method_code = method_code
        self._document_type._organization_code = organization_code
        self._document_type._method_name = self.method_codes_inv.get(method_code, None)
        self._document_type._organization_name = self.organization_codes_inv.get(organization_code, None)
        self._document_type._db_document_type = db_document_type

    def typeByDeno(self, deno: str) -> tuple[DbDocumentType | None, str | None, str | None]:
        """ Определение типа документа по децимальному номеру """

        deno = deno.replace(' ', '')
        if re.fullmatch('Всоставе' + r'\w{4}.\d{5}.\d{5}', deno):
            deno = deno[len('Всоставе'):]
            db_document_type, organization_code, method_code = self.typeByDenoTd(deno)
        elif re.fullmatch(r'\w{4}.\d{5}.\d{5}', deno):
            db_document_type, organization_code, method_code = self.typeByDenoTd(deno)
        else:
            db_document_type, organization_code, method_code = None, None, None
        return db_document_type, organization_code, method_code

    def typeByDenoTd(self, deno: str) -> tuple[DbDocumentType | None, str | None, str | None]:
        """ Определение типа документа по децимальному номеру
            (Для технологической документации) """

        #       0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17
        # (ТД)  У  И  Е  С  .  1  2  3  4  5  .  1  2  3  4  5
        type_code = deno[5:7]
        organization_code = deno[7]
        method_code = deno[8:10]
        subtype_name = self.type_codes_inv.get(type_code, None)
        db_document_type = DbDocumentType.data.get(('ТД', subtype_name), None)
        if db_document_type is not None:
            return db_document_type, organization_code, method_code
        return None, None, None

    @property
    def type_codes(self) -> dict[str, str]:
        """ Создает:
            1) _type_codes: {Наименование типа ТД : код типа ТД}
            2) _type_codes_inv: {код типа ТД : Наименование типа ТД}
            Возвращает _type_codes """

        if not self.__class__._type_codes:
            for type_name, code in self.__class__._config.data['document_td_type_code'].items():
                self.__class__._type_codes[type_name.capitalize()] = code
                self.__class__._type_codes_inv[code] = type_name.capitalize()
        return self.__class__._type_codes

    @property
    def type_codes_inv(self) -> dict[str, str]:
        """ Создает:
            1) _type_codes: {Наименование типа ТД : код типа ТД}
            2) _type_codes_inv: {код типа ТД : Наименование типа ТД}
            Возвращает _type_codes_inv """

        if not self.__class__._type_codes_inv:
            for type_name, code in self.__class__._config.data['document_td_type_code'].items():
                self.__class__._type_codes[type_name.capitalize()] = code
                self.__class__._type_codes_inv[code] = type_name.capitalize()
        return self.__class__._type_codes_inv

    @property
    def method_codes(self) -> dict[str, str]:
        """ Создает:
            1) _method_codes: {Метод изготовления: код типа ТД}
            2) _method_codes_inv: {код типа ТД : Метод изготовления}
            Возвращает _method_codes """

        if not self.__class__._method_codes:
            for method_name, code in self.__class__._config.data['document_method'].items():
                self.__class__._method_codes[method_name] = code
                self.__class__._method_codes_inv[code] = method_name
        return self.__class__._method_codes

    @property
    def method_codes_inv(self) -> dict[str, str]:
        """ Создает:
            1) _method_codes: {Метод изготовления: код типа ТД}
            2) _method_codes_inv: {код типа ТД : Метод изготовления}
            Возвращает _method_codes_inv """

        if not self.__class__._method_codes_inv:
            for method_name, code in self.__class__._config.data['document_method'].items():
                self.__class__._method_codes[method_name] = code
                self.__class__._method_codes_inv[code] = method_name
        return self.__class__._method_codes_inv

    @property
    def organization_codes(self) -> dict[str, str]:
        """ Создает:
            1) _organization_codes: {Метод организации: код типа ТД}
            Возвращает _organization_codes """

        if not self.__class__._organization_codes:
            for organization_type, code in self.__class__._config.data['document_organization'].items():
                self.__class__._organization_codes[organization_type] = code
        return self.__class__._organization_codes

    @property
    def organization_codes_inv(self) -> dict[str, str]:
        """ Создает:
            1) _organization_codes_inv: {код типа ТД: Метод организации}
            Возвращает _organization_codes_inv """

        if not self.__class__._organization_codes_inv:
            for organization_type, code in self.__class__._config.data['document_organization'].items():
                self.__class__._organization_codes_inv[code] = organization_type
        return self.__class__._organization_codes_inv


class IotBuilder:
    """ Конструктор для класса IOT
        (инструкции по охране труда)
        Создает уникальные экземпляры IOT по:
        1) Номер инструкции  """

    iots = {}

    def __init__(self) -> None:
        self._iot = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр IOT
            без привязки к данным БД """

        self._iot = IOT()

    @property
    def iot(self) -> IOT:
        """ Возвращает экземпляр IOT,
            сохраняет его как используемый и
            создает новый экземпляр IOT
            без привязки к данным из БД """

        iot = self._iot
        self.__class__.iots.update({iot.deno: iot})
        self.reset()
        return iot

    def ifExists(self, deno: str) -> None:
        """ Проверяет наличие или создает экземпляр
            IOT c определенным номером """

        if deno in self.__class__.iots:
            self._iot = self.__class__.iots[deno]
        else:
            self.initIot(deno=deno)

    def createIot(self, deno: str) -> None:
        """ Проверяет наличие или создает экземпляр
            IOT c определенным номером """

        self.ifExists(deno=deno)

    def initIot(self, deno: str) -> None:
        """ Создает экземпляр IOT c
            определенным номером """

        DbIOT.updCheck()
        if deno in DbIOT.data:
            self._iot.db_iot = DbIOT.data[deno]
        else:
            logging.warning(f'Не найдена инструкция {deno}')


class RigBuilder:
    """ Конструктор для класса Rig (оснастка)
        Создает уникальные экземпляры Rig по:
        1) Наименованию """

    rigs = {}

    def __init__(self) -> None:
        self._rig = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Rig
            без привязки к данным БД """

        self._rig = Rig()

    @property
    def rig(self) -> Rig:
        """ Возвращает экземпляр Rig,
            сохраняет его как используемый и
            создает новый экземпляр Rig
            без привязки к данным из БД """

        rig = self._rig
        self.__class__.rigs.update({rig.name: rig})
        self.reset()
        return rig

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Rig с определенным наименованием """

        if name in self.__class__.rigs:
            self._rig = self.__class__.rigs[name]
        else:
            self.initRig(name=name)

    def createRig(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Rig с определенным наименованием """

        self.ifExists(name=name)

    def initRig(self, name: str) -> None:
        """ Создает экземпляр Rig с
            определенным наименованием """

        DbRig.updCheck()
        if name in DbRig.data:
            self._rig.db_rig = DbRig.data[name]
        else:
            logging.warning(f'Не найдена оснастка {name}')


class EquipmentBuilder:
    """ Конструктор для класса Equipment (оборудование)
        Создает уникальные экземпляры Equipment по:
        1) Наименованию """

    equipments = {}

    def __init__(self) -> None:
        self._equipment = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Equipment
            без привязки к данным БД """

        self._equipment = Equipment()

    @property
    def equipment(self) -> Equipment:
        """ Возвращает экземпляр Equipment,
            сохраняет его как используемый и
            создает новый экземпляр Equipment
            без привязки к данным из БД """

        equipment = self._equipment
        self.__class__.equipments.update({equipment.name: equipment})
        self.reset()
        return equipment

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Equipment c определенным наименованием """

        if name in self.__class__.equipments:
            self._equipment = self.__class__.equipments[name]
        else:
            self.initEquipment(name=name)

    def createEquipment(self, name: str) -> None:
        """ Создает экземпляр Equipment с
            определенным наименованием """

        self.ifExists(name=name)

    def initEquipment(self, name: str) -> None:
        """ Создает экземпляр Equipment с
            определенным наименованием """

        DbEquipment.updCheck()
        if name in DbEquipment.data:
            self._equipment.db_equipment = DbEquipment.data[name]
        else:
            logging.warning(f'Не найдено оборудование {name}')


class MatBuilder:
    """ Конструктор для класса Material
        Создает уникальные экземпляры Material по:
        1) Наименованию """

    mats = {}

    def __init__(self) -> None:
        self._mat = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Material
            без привязки к данным БД """

        self._mat = Mat()

    @property
    def mat(self) -> None:
        """ Возвращает экземпляр Material,
            сохраняет его как используемый и
            создает новый экземпляр Material
            без привязки к данным из БД """

        mat = self._mat
        self.__class__.mats.update({mat.name: mat})
        self.reset()
        return mat

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Material с определенным наименованием """

        if name in self.__class__.mats:
            self._mat = self.__class__.mats[name]
        else:
            self.initMat(name=name)

    def createMat(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Material с определенным наименованием """

        self.ifExists(name=name)

    def initMat(self, name: str) -> None:
        """ Создает экземпляр Material с
            определенным наименованием """

        DbMaterial.updCheck()
        if name in DbMaterial.data:
            self._mat.db_mat = DbMaterial.data[name]
        else:
            logging.warning(f'Не найден материал {name}')


class AreaBuilder:
    """ Конструктор для класса Area
        Создает уникальные экземпляры Area по:
        1) Наименованию """

    areas = {}

    def __init__(self) -> None:
        self._area = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Rig
            без привязки к данным БД """

        self._area = Area()

    @property
    def area(self) -> Area:
        """ Возвращает экземпляр Area,
            сохраняет его как используемый и
            создает новый экземпляр Area
            без привязки к данным из БД """

        area = self._area
        self.__class__.areas.update({area.name: area})
        self.reset()
        return area

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Area с определенным наименованием """

        if name in self.__class__.areas:
            self._area = self.__class__.areas[name]
        else:
            self.initArea(name=name)

    def createArea(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Area с определенным наименованием """

        self.ifExists(name=name)

    def initArea(self, name: str) -> None:
        """ Создает экземпляр Area с
            определенным наименованием """

        DbArea.updCheck()
        if name in DbArea.data:
            self._area.db_area = DbArea.data[name]
        else:
            logging.warning(f'Не найден участок {name}')


class WorkplaceBuilder:
    """ Конструктор для класса Workplace
        Создает уникальные экземпляры Workplace по:
        1) Наименованию """

    workplaces = {}

    def __init__(self) -> None:
        self._workplace = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Workplace
            без привязки к данным БД """

        self._workplace = Workplace()

    @property
    def workplace(self) -> Workplace:
        """ Возвращает экземпляр Workplace,
            сохраняет его как используемый и
            создает новый экземпляр Workplace
            без привязки к данным из БД """

        workplace = self._workplace
        self.__class__.workplaces.update({workplace.name: workplace})
        self.reset()
        return workplace

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Workplace с определенным наименованием """

        if name in self.__class__.workplaces:
            self._workplace = self.__class__.workplaces[name]
        else:
            self.initWorkplace(name=name)

    def createWorkplace(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Workplace с определенным наименованием """

        self.ifExists(name=name)

    def initWorkplace(self, name: str) -> None:
        """ Создает экземпляр Workplace с
            определенным наименованием """

        DbWorkplace.updCheck()
        if name in DbWorkplace.data:
            self._workplace.db_workplace = DbWorkplace.data[name]
        else:
            logging.warning(f'Не найдено рабочее место {name}')


class ProfessionBuilder:
    """ Конструктор для класса Profession
        Создает уникальные экземпляры Profession по:
        1) Наименованию """

    professions = {}

    def __init__(self) -> None:
        self._profession = None
        self.reset()

    def reset(self) -> None:
        """ Создает экземпляр Profession
            без привязки к данным БД """

        self._profession = Profession()

    @property
    def profession(self) -> None:
        """ Возвращает экземпляр Profession,
            сохраняет его как используемый и
            создает новый экземпляр Profession
            без привязки к данным из БД """

        profession = self._profession
        self.__class__.professions.update({profession.name: profession})
        self.reset()
        return profession

    def ifExists(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Profession с определенным наименованием """

        if name in self.__class__.professions:
            self._profession = self.__class__.professions[name]
        else:
            self.initProfession(name=name)

    def createProfession(self, name: str) -> None:
        """ Проверяет наличие или создает экземпляр
            Profession с определенным наименованием """

        self.ifExists(name=name)

    def initProfession(self, name: str) -> None:
        """ Создает экземпляр Profession с
            определенным наименованием """

        DbProfession.updCheck()
        if name in DbProfession.data:
            self._profession.db_profession = DbProfession.data[name]
        else:
            logging.warning(f'Не найдена профессия {name}')


class Product:
    """ Cодержит данные об изделии и оформленных к нему документов """

    def __init__(self) -> None:
        self.db_product = None
        self.projects = None
        self.documents = set()

    def getData(self, data: dict[str, str | None]):
        """ Возвращает как значения аттрибутов изделия, так и
            значения аттрибутов документов этого изделия """

        if data['type'] == 'document':
            data = add_missing_keys(dictionary=data, keys=['class_name',
                                                           'name',
                                                           'setting',
                                                           'only_relevant',
                                                           'first'])
            text = self.getDocumentByType(
                class_name=data.get('class_name', None),
                subtype_name=data.get('subtype_name', None),
                org_code=data.get('organization_code', None),
                meth_code=data.get('method_code', None),
                setting=data.get('setting', None),
                only_relevant=data.get('only_relevant', None),
                first=data.get('first', None),
                only_text=data.get('only_text', True))
        elif data['type'] == 'product':
            text = getattr(self, data.get('setting', None))
        else:
            text = None
        return text

    def getDocumentByType(self, class_name: str,
                          subtype_name: str,
                          setting: str | None = None,
                          org_code: str | None = None,
                          meth_code: str | None = None,
                          only_relevant: bool | None = None,
                          first: bool | None = None,
                          only_text: bool = True) -> list | str | None:
        """ Метод для запроса аттрибутов документов определенного изделия.
            Может возвращать результат как текст или список """

        result = []
        # only_relevant и first определены как None, т.к. add_missing_keys в getData восстанавливает ключи с None
        only_relevant = not only_relevant is None
        first = not first is None
        document_type = return_document_type(
            class_name=class_name,
            subtype_name=subtype_name,
            organization_code=org_code,
            method_code=meth_code)
        for document in self.documents:
            if document.document_type == document_type:
                outdated = document.db_document.document_real.stage.stage == 'Аннулирован'
                if not (only_relevant and outdated):
                    if setting:
                        result.append(document.getAttrValueByName(attr_name=setting, only_text=only_text))
                    else:
                        result.append(document)
        if only_text:
            if first:
                return '' if not result else result[0]
            return '' if not result else chr(10).join(result)
        else:
            if first:
                return None if not result else result[0]
            return result

    def addDocument(self, document: DbDocumentReal) -> None:
        """ Добавление документа """

        db_document = DbDocument.addDbDocument(product=self,
                                               document_real=document)
        builder = DocumentBuilder()
        builder.setDbDocument(db_document)
        self.documents.add(builder.document)

    def delDocument(self, document: DbDocumentReal) -> None:
        """ Удаление документа """

        builder = DocumentBuilder()
        builder.setDbDocument(DbDocument.getData(document_real=document,
                                                 product=self))
        self.documents.remove(builder.document)
        DbDocument.delDbDocument(product=self,
                                 document_real=document)

    def getProjects(self, with_documents: bool) -> str:
        """ Возвращает список каким технологическим документом
            закрыто изделие в различных проектах Excel
            * НЕ ИСПОЛЬЗУЕТСЯ """

        result = []
        self.projects = self.db_product.projects
        for db_project in self.projects:
            if with_documents:
                if db_project.id_document is not None:
                    deno = db_project.document.document_real.deno
                else:
                    deno = 'Нет записи о ТД  '
                record = f'{deno}: {db_project.project.project_name}'
            else:
                record = db_project.project.project_name
            result.append(record)
        return '\n'.join(result)

    def setChildren(self, children: list[DbProduct]) -> None:
        """ Устанавливает дочерние изделия """
        msg = f'установить дочерние изделия: {children}'
        logging.info(msg)
        DbHierarchy.setChildren(parent=self.db_product,
                                products=children)

    def getChildren(self) -> list[DbHierarchy]:
        """ Возвращает дочерние изделия ввиде
            списка экземпляров DbHierarchy """

        return DbHierarchy.getByParent(self.db_product)

    def children(self) -> list[dict[str, Product | int]]:
        """ Возвращает дочерние изделия ввиде
            списка словарей:
            {'product' : экземпляр Product(),
             'quantity': количество в родительском изделии}"""

        children = []
        builder = ProductBuilder()
        for db_hierarchy in self.getChildren():
            builder.setDbProduct(db_product=db_hierarchy.child)
            product = builder.product
            children.append({'product': product,
                             'quantity': db_hierarchy.quantity})
        return children

    def updDocuments(self) -> None:
        """ Обновить список документов изделия,
            подгрузив данные из БД """

        self.documents = set()
        builder = DocumentBuilder()
        documents = self.db_product.getDbDocuments()
        for db_document in documents:
            builder.setDbDocument(db_document=db_document)
            self.documents.add(builder.document)

    def updKttp(self, documents: list[DbDocumentReal]) -> None:
        """ Обновить список типовых технологических процессов
            (относящихся ко многим изделиям) которые относятся
            к данному изделию """

        old_documents = self.getDocumentByType(
            class_name='ТД',
            subtype_name='Карта типового (группового) технологического процесса',
            org_code='2', only_text=False)
        new_db_documents_real = documents
        old_db_documents_real = [document.db_document.document_real
                                 for document in old_documents]
        intersections = set(new_db_documents_real).intersection(old_db_documents_real)
        for db_document_real in intersections:
            new_db_documents_real.remove(db_document_real)
            old_db_documents_real.remove(db_document_real)
        documents = {}
        for document in old_documents:
            if document.db_document.document_real in old_db_documents_real:
                key = document.db_document.document_real.deno
                document_data = {'product': self,
                                 'document_real': document.db_document.document_real,
                                 'delete': True}
                documents[key] = document_data
                self.documents.remove(document)
        for db_document_real in new_db_documents_real:
            key = db_document_real.deno
            document_data = {'product': self,
                             'document_real': db_document_real,
                             'delete': False}
            documents[key] = document_data
        documents = DbDocument.addDbDocuments(documents)
        for item in documents.values():
            if item['db_document'] is not None:
                builder = DocumentBuilder()
                builder.setDbDocument(item['db_document'])
                self.documents.add(builder.document)

    @staticmethod
    def newTdDocumentNum(code: str) -> str:
        #TODO Стоит вынести из Product
        """ Возвращает первый незанятый номер технологического документа """

        return Document.getLastNum(code)

    @staticmethod
    def getAllProductsInDict(upd=False) -> list[dict[str, int | str | DbProduct]]:
        """ Возвращает список словарей всех изделий
            {'id_product': id изделия в БД,
             'name': наименование изделия или проекта,
             'denotation': децимальный номер изделия,
             'db_product': экземпляр ORM класса изделия} """

        if upd:
            DbProduct.updData()
        product_data = []
        for item in DbProduct.uniqueData():
            product_data.append({
                'id_product': item.id_product,
                'name': str(item.name),
                'denotation': str(item.deno),
                'db_product': item})
        project_data = []
        for item in DbExcelProject.uniqueData():
            if item.id_product is not None:
                project_data.append({
                    'id_product': item.product.id_product,
                    'name': str(item.project_name),
                    'denotation': str(item.product.deno),
                    'db_product': item})
        return product_data + project_data

    @property
    def id_product(self) -> int:
        """ id в БД """

        return int(self.db_product.id_product)

    # @id_product.setter
    # def id_product(self, value: int) -> None:
    #     self.db_product.id_product = value

    @property
    def name(self) -> str:
        """ Наименование """

        return str(self.db_product.name)

    @name.setter
    def name(self, value: str) -> None:
        """ Наименование """

        self.db_product.name = value

    @property
    def deno(self) -> str:
        """ Децимальный номер """

        if self.db_product.name == self.db_product.deno:
            return ''
        return str(self.db_product.deno)

    @deno.setter
    def deno(self, value: str) -> None:
        """ Децимальный номер """

        self.db_product.deno = str(value)

    @property
    def purchased(self):
        """ Изготавливается ли по кооперации """

        return self.db_product.purchased if self.db_product.purchased is not None else ''

    @property
    def primary_parent(self) -> DbProduct | None:
        """ Изделие, которое является первичной применяемостью """

        db_primary_application = DbPrimaryApplication.getData(self.db_product)
        if db_primary_application is not None:
            return db_primary_application.parent

    @property
    def primary_product(self) -> str:
        """  """

        primary_denos = [primary_application.parent.deno for primary_application
                         in self.db_product.primary_parent]
        return '\n'.join(primary_denos)

    @property
    def primary_project(self) -> str:
        """ Последнее изделие при проходе цепочки первичных применяемостей """

        if self.db_product.primary_parent:
            parent_product = self.db_product.primary_parent[0].parent
            while parent_product.primary_parent:
                if parent_product == parent_product.primary_parent[0].parent:
                    break
                parent_product = parent_product.primary_parent[0].parent
            projects = parent_product.projects
            project_names = [project.project.project_name for project in projects]
            return f'{parent_product.deno} {parent_product.name}' + '\n' + '\n'.join(project_names)
        else:
            return ''

    @property
    def all_projects(self) -> str:
        """ Все проекты Excel в которых было это изделие
            *НЕ ИСПОЛЬЗУЕТСЯ """

        return self.getProjects(with_documents=False)

    @property
    def all_projects_with_doc(self) -> str:
        """ Все проекты Excel в которых было это изделие
            + документы которыми оно закрыто
            *НЕ ИСПОЛЬЗУЕТСЯ """

        return self.getProjects(with_documents=True)

    @property
    def upd_date(self) -> datetime | None:
        """ Дата последнего обновления """

        if self.db_product.date_check != datetime.min:
            return self.db_product.date_check

    @property
    def upd_date_f(self) -> str:
        """ Дата последнего обновления как текст """

        return date_format(self.upd_date)

    @property
    def hierarchy_relevance(self) -> str:
        """ Актуальность данных родитель - дети """

        upd_date = self.db_product.date_check
        plm_date = None
        for document in self.documents:
            type_name = document.db_document.document_real.document_type.subtype_name
            names = ['Спецификация', 'Чертеж детали']
            if type_name in names:
                plm_date = document.db_document.document_real.date_changed
                break
        if plm_date and upd_date:
            if plm_date > upd_date:
                status = f'Устарело'
            else:
                status = 'Актуально'
        elif not plm_date:
            status = 'Нет даты\nспецификации'
        elif not upd_date:
            status = 'Нет даты\nобновления изделия'
        else:
            status = 'ОШИБКА'
        return status

    @property
    def hierarchy_relevance_days(self) -> int | None:
        """ Актуальность данных родитель - дети с отсчетом дней
            *НЕ ИСПОЛЬЗУЕТСЯ"""

        upd_date = self.db_product.date_check
        plm_date = None
        for document in self.documents:
            if document.db_document.document_real.document_type.subtype_name == 'Спецификация':
                plm_date = document.db_document.document_real.date_changed
                break
        if plm_date and upd_date:
            if plm_date > upd_date:
                time = plm_date - upd_date
                status = time.days
            else:
                status = 0
        else:
            status = None
        return status

    @property
    def product_type(self) -> ProductType:
        """ Тип изделия по разделу спецификации """

        product_types = [parent.product_type for parent in self.db_product.parents]
        if product_types:
            return product_types[0]
        return ProductType(product_type='неизвестно')

    @property
    def product_type_name(self) -> str:
        """ Название типа изделия по разделу спецификации """

        return self.product_type.type_name

    @property
    def product_kind_imenitelnyy(self) -> str:
        """ Вид изделия (именительный) """

        return self.product_kind.imenitelnyy

    @property
    def product_kind_tvoritelnyy(self) -> str:
        """ Вид изделия (творительный) """

        return self.product_kind.tvoritelnyy

    @property
    def product_kind_predlozhnyy(self) -> str:
        """ Вид изделия (предложный) """

        return self.product_kind.predlozhnyy

    @property
    def product_kind_roditelnyy(self) -> str:
        """ Вид изделия (родительный) """

        return self.product_kind.roditelnyy

    @property
    def product_kind_datelnyy(self) -> str:
        """ Вид изделия (винительный) """

        return self.product_kind.datelnyy

    @property
    def product_kind(self) -> ProductKind:
        """ Вид изделия """

        if self.db_product.kind:
            return ProductKind(self.db_product.kind)
        return ProductKind(DbProductKind.data[self.product_type.type_name])

    @product_kind.setter
    def product_kind(self, kind: ProductKind) -> None:
        """ Изменить вид изделия """

        SplashScreen().newMessage(message=f'Изменение вида изделия',
                                  stage=0,
                                  stages=8,
                                  log=True,
                                  logging_level='INFO')
        DbProduct.addDbProduct(deno=self.deno,
                               name=self.name,
                               id_kind=kind.id_kind)
        SplashScreen().newMessage(message=f'Вид изделия изменен',
                                  log=True,
                                  logging_level='INFO')
        SplashScreen().closeWithWindow()

    @property
    def product_kind_name(self) -> str:
        """ Вид изделия (Наименование) """

        return self.product_kind.name

    @property
    def product_kind_name_short(self) -> str:
        """ Вид изделия (Наименование сокращенное) """

        return self.product_kind.name_short

    @property
    def project_name(self) -> str:
        """ Наименование проекта """

        projects = self.db_product.project
        project_name = [project.project_name for project in projects]
        return '\n'.join(project_name)

    @property
    def has_real_deno(self) -> bool:
        """ Являются ли данные децимального номера
            децимальным номером.
            Материалы и изделия без децимального номера
            имеют копию названия в качестве децимального номера """

        return self.db_product.name != self.db_product.deno


class ProductType:
    """ Тип изделия согласно спецификации
        инициализируется по названию или id """

    def __init__(self, product_type: str) -> None:
        self.product_type = DbProductType.getData(product_type=product_type)

    @staticmethod
    def getAllTypes() -> list[DbProductType]:
        """ Возвращает список типов изделий """

        return list(set([prod_type for prod_type in DbProductType.data.values()]))

    @property
    def id_type(self) -> int:
        """ id типа изделия """

        return self.product_type.id_type

    @property
    def type_name(self) -> str:
        """ Наименования типа изделия """

        return self.product_type.type_name


class ProductKind:
    """ Вид изделия согласно произвольной
        таблице видов изделий """

    def __init__(self, product_kind: DbProductKind) -> None:
        DbProductKind.updCheck()
        self.db_product_kind = product_kind

    @property
    def db_product_kind(self) -> DbProductKind:
        """ ORM класс представления вида изделия в БД """

        return self._db_product_kind

    @db_product_kind.setter
    def db_product_kind(self, product_kind: DbProductKind) -> None:
        """ ORM класс представления вида изделия в БД """

        if isinstance(product_kind, DbProductKind):
            self._db_product_kind = product_kind
        else:
            self._db_product_kind = DbProductKind.getData(product_kind)
            if self._db_product_kind is None:
                self._db_product_kind = DbProductKind.data[0]

    @classmethod
    def all_db_kinds(cls) -> dict[str, DbProductKind]:
        """ Словарь из всех видов изделий в БД
            {Наименование вида: экземпляр DbProductKind}"""

        kind_dict = {}
        for kind in DbProductKind.data.values():
            kind_dict[kind.name_short] = kind
        return kind_dict

    @classmethod
    def all_db_kinds_names_short(cls) -> list[str]:
        """ Сортированный список сокращенных
            наименований видов документов """

        return sorted([db_kind.name_short for db_kind in DbProductKind.uniqueData()])

    @property
    def id_kind(self) -> int:
        """ id вида изделия """

        return self._db_product_kind.id_kind

    @property
    def name(self) -> str:
        """ Наименование вида изделия """

        return self._db_product_kind.name

    @property
    def name_short(self) -> str:
        """ Сокращенное наименование изделия """

        return self._db_product_kind.name_short

    @property
    def imenitelnyy(self) -> str:
        """ Наименование вида изделия (именительный) """

        return self._db_product_kind.imenitelnyy

    @property
    def tvoritelnyy(self) -> str:
        """ Наименование вида изделия (творительный) """

        return self._db_product_kind.tvoritelnyy

    @property
    def predlozhnyy(self) -> str:
        """ Наименование вида изделия (предложный) """

        return self._db_product_kind.predlozhnyy

    @property
    def roditelnyy(self) -> str:
        """ Наименование вида изделия (родительный) """

        return self._db_product_kind.roditelnyy

    @property
    def datelnyy(self) -> str:
        """ Наименование вида изделия (дательный) """

        return self._db_product_kind.datelnyy


class Document:
    """ Класс содержит базовые данные о документе.
        Базовыми являются реквизиты, одинаковые
        для конструкторских и технологических документов """
    _config = CONFIG

    def __init__(self) -> None:
        self._config = self.__class__._config
        self.db_document = None
        self._document_type = None
        self._litera = ''
        self._operations = {}

    def getAttrValueByName(self, attr_name, only_text=True):
        """ Возвращает значение аттрибута по его наименованию """

        attr_value = getattr(self, attr_name)
        if only_text:
            attr_value = '' if attr_value is None else attr_value
        return attr_value

    def getSignatureSurname(self, position: str) -> str:
        """ Возвращает ФИО для определенной должности.
            Если ФИО не определено, то возвращает ФИО
            по умолчанию для данной должности """

        signature_position = self._config.data['document_settings'][f'{position}']
        key = (self.id_document_real, signature_position)
        if position == 'developer':
            default = self.name_created
        else:
            default = self._config.data['document_settings'][f'name_{position}']
        return DbDocumentSignature.data[key].signature_surname if key in DbDocumentSignature.data else default

    def updSignatureSurname(self, position: str, surname: str) -> None:
        """ Изменить ФИО для определенной должности """

        signature_position = self._config.data['document_settings'][f'{position}']
        DbDocumentSignature.updDocumentSignature(id_document_real=self.id_document_real,
                                                 signature_position=signature_position,
                                                 signature_surname=surname,
                                                 signature_signdate=None,
                                                 commit_later=True)

    def dbOperations(self) -> dict[int, Operation]:
        # TODO Вынести метод в класс технологических документов
        """ Возвращает словарь операций для данного документа
            (исходя их данных в БД)
            {Порядковый номер операции: экземпляр Operation} """

        _operations = {}
        builder = OperationBuilder()
        for db_document_doc in DbOperationDoc.uniqueData():
            if db_document_doc.document_real == self.db_document.document_real:
                builder.createOperation(document=self,
                                        name=db_document_doc.operation.name,
                                        order=db_document_doc.operation_order)
                operation = builder.operation
                _operations[operation.order] = operation
        return _operations

    # Для ТД
    def addOperation(self, operation: Operation) -> None:
        # TODO Вынести метод в класс технологических документов
        """ Добавить операцию в документ """

        self._operations[operation.order] = operation

    def createMk(self) -> None:
        # TODO Вынести метод в класс технологических документов
        """ Сохранить данные маршрутной карты в БД """

        DbOperationDoc.delOutdatedOperations(operations=self.operations)
        SplashScreen().newMessage(message=f'Cохранение документа...',
                                  stage=0,
                                  stages=len(self.operations) + 2,
                                  log=True,
                                  logging_level='INFO')

        for operation in self.operations.values():
            SplashScreen().newMessage(message=f'Сохранение операции {operation.num} {operation.name}',
                                      log=True,
                                      logging_level='INFO')
            DbOperationDoc.addOperation(operation=operation)
            DbSentenceDoc.delSentences(sentences=operation.sentences_for_del)
            operation.sentences_for_del = []
            DbSentenceDoc.addSentences(sentences=operation.sentences)
            DbDocDoc.updDocs(sentences=operation.sentences)
            DbIOTDoc.updIots(sentences=operation.sentences)
            DbRigDoc.updRigs(sentences=operation.sentences)
            DbEquipmentDoc.updEquipments(sentences=operation.sentences)
            DbMaterialDoc.updMats(sentences=operation.sentences)
        self.changeStageOfMk()
        logging.info('Документ сохранен')
        SplashScreen().newMessage(message=f'Документ сохранен',
                                  log=True,
                                  logging_level='INFO')
        SplashScreen().closeWithWindow(msg=f'Документ {self.name} {self.deno} сохранен', m_type='info')

    # Для ТД
    def generateCommonProperties(self) -> list[str]:
        # TODO Вынести метод в класс технологических документов
        """ Создание списка строк с текстом общих данных для МК """

        self.config = CONFIG
        self.config_type = 'excel_document'
        iots = self.config.data[self.config_type]['first_page_text_iots']
        prof = self.config.data[self.config_type]['first_page_text_prof']
        wkpl = self.config.data[self.config_type]['first_page_text_wkpl']
        mat1 = self.config.data[self.config_type]['first_page_text_mat1']
        mat2 = self.config.data[self.config_type]['first_page_text_mat2']
        met1 = self.config.data[self.config_type]['first_page_text_met1']
        inst = self.config.data[self.config_type]['first_page_text_inst']
        stat = self.config.data[self.config_type]['first_page_text_stat']
        abbr_tu = self.config.data[self.config_type]['first_page_text_abbr_tu']
        abbr_po = self.config.data[self.config_type]['first_page_text_abbr_po']
        abbr_spo = self.config.data[self.config_type]['first_page_text_abbr_spo']
        abbr_nku = self.config.data[self.config_type]['first_page_text_abbr_nku']
        abbr_tu_find = self.config.data[self.config_type]['first_page_text_abbr_tu_find'][1:][:-1]
        abbr_po_find = self.config.data[self.config_type]['first_page_text_abbr_po_find'][1:][:-1]
        abbr_spo_find = self.config.data[self.config_type]['first_page_text_abbr_spo_find'][1:][:-1]
        abbr_nku_find = self.config.data[self.config_type]['first_page_text_abbr_nku_find'][1:][:-1]
        abbr_start = self.config.data[self.config_type]['first_page_text_abbrlist']
        result = [iots, prof, wkpl, inst]
        abbreviations = set()
        for num, operation in self.operations.items():
            if operation.mat:
                if mat1 not in result:
                    result.append(mat1)
                if mat2 not in result:
                    result.append(mat2)
            # if operation.name == 'Настройка, регулировка':
            if 'Контрольно-измерительная' in operation.rig:
                if met1 not in result:
                    result.append(met1)
            # if 'контрольно-измерительная аппаратура' in operation.rig:
            #     if inst not in result:
            #         result.append(inst)
            if operation.workplace.name == 'Рабочее место сборщика':
                if stat not in result:
                    result.append(stat)
            for sentence in operation.sentences.values():
                if 'работоспособ' in sentence.text:
                    if met1 not in result:
                        result.append(met1)
                if abbr_tu_find in sentence.text:
                    abbreviations.update([abbr_tu])
                if abbr_po_find in sentence.text:
                    abbreviations.update([abbr_po])
                if abbr_spo_find in sentence.text:
                    abbreviations.update([abbr_spo])
                if abbr_nku_find in sentence.text:
                    abbreviations.update([abbr_nku])
        if abbreviations:
            abbr_text = ';\n'.join(list(abbreviations))
            result.append(f'{abbr_start}\n{abbr_text}.')
        product_abbreviation = f'{self.product.name} далее по тексту - {self.product.product_kind_imenitelnyy}.'
        result.append(product_abbreviation)
        return result

    def changeStageOfMk(self):
        # TODO Вынести метод в класс технологических документов
        """ Изменение статуса маршрутных карт """

        if self.operations and self.stage == 'Зарегистрирован':
            self.stage = 'В разработке'

    @staticmethod
    def getLastNum(code: str) -> str:
        # TODO Вынести метод в класс технологических документов
        """ Возвращает следующий свободный
            порядковый номер маршрутной карты """

        documents = []
        data = DbDocumentReal.getDbDocumentRealByCode(code=code)
        # for deno, id_type in DbDocumentReal.data.keys():
        #     if re.fullmatch(r'\w{4}' + f'.{code}' + r'\d{4}', deno):
        #         documents.append(deno)
        documents = [db_document[0].deno for db_document in data]
        try:
            last_document = sorted(documents, reverse=True)[0]
            last_num = last_document[last_document.rfind('.') + 2:]
            last_num = int(last_num)
            last_num += 1
            last_num = str(last_num)
            last_num = '0' * (4 - len(last_num)) + last_num
            return last_num
        except IndexError:
            return '0001'

    # # Для ТД (возвращает db_product)
    # @property
    # def sub_products(self) -> list[DbProduct]:
    #     return [db_document_complex.product for db_document_complex in
    #             self.db_document.document_real.products_in_complex_documents]

    # Для ТД (возвращает product)

    @property
    def sub_products_new(self) -> list[Product]:
        """ Возвращает список изделий,
            изготавливаемых совместно
            по данному документу """

        builder = ProductBuilder()
        result = []
        for db_document_complex in self.db_document.document_real.products_in_complex_documents:
            builder.setDbProduct(db_product=db_document_complex.product)
            product = builder.product
            result.append((product, self))
        return result

    @staticmethod
    def getAllDocuments(document_type, only_deno=False) -> dict[str, DbDocumentReal]:
        """ Словарь из всех документов вида
            {Децимальный номер Наименование: Экземпляр DbDocumentReal} """

        result = {}
        db_documents_real = DbDocumentReal.getAllDocumentsRealByType(id_type=document_type.id_type)
        for db_document_real in db_documents_real:
            document_type_of_db_document_real = return_document_type(deno=db_document_real.deno)
            if document_type_of_db_document_real == document_type:
                if only_deno:
                    result.update({f'{db_document_real.deno}': db_document_real})
                else:
                    result.update({f'{db_document_real.deno} {db_document_real.name}': db_document_real})
        return result

    @property
    def id_document(self) -> int:
        """ id записи связи документа и изделия """

        return self.db_document.id_document

    # @id_document.setter
    # def id_document(self, value: int) -> None:
    #     self.db_document.id_document = value

    @property
    def id_document_real(self) -> int:
        """ id документа """

        return self.db_document.document_real.id_document_real

    @property
    def id_product(self) -> int:
        """ id основного изделия к
            которому относится документ"""

        return self.db_document.id_product

    # @id_product.setter
    # def id_product(self, value):
    #     self.db_document.id_product = value

    @property
    def id_type(self) -> int:
        """ id типа документа по спецификации """

        return self.db_document.document_real.id_type

    @property
    def name(self) -> str:
        """ Наименование документа """

        if self.db_document.document_real.name is not None:
            return self.db_document.document_real.name
        else:
            return self.product.name

    @property
    def deno(self) -> str:
        """ Децимальный номер изделия """

        return self.db_document.document_real.deno

    @property
    def file_name(self) -> str:
        """ Наименование файла изделия """

        return self.db_document.document_real.file_name

    @property
    def link(self) -> str:
        """  """

        return self.db_document.document_real.link

    @property
    def date_created(self) -> datetime:
        """ Дата создания """

        return self.db_document.document_real.date_created

    @property
    def date_changed(self) -> datetime:
        """ Дата изменения """

        return self.db_document.document_real.date_changed

    @property
    def date_changed_str(self) -> str:
        """ Дата изменения как текст """

        return date_format(self.date_changed)

    @property
    def date_created_str(self) -> str:
        """ Дата создания как текст """

        return date_format(self.date_created)

    @property
    def name_created(self) -> str:
        """ ФИО создателя документа """

        return self.db_document.document_real.name_created

    @property
    def name_changed(self) -> str:
        """ ФИО последнего изменившего документ """

        return self.db_document.document_real.name_changed

    @property
    def name_developer(self) -> str:
        """ ФИО разработчика документа """

        return self.getSignatureSurname('developer')

    @name_developer.setter
    def name_developer(self, surname):
        """ ФИО разработчика документа """

        self.updSignatureSurname(position='developer', surname=surname)

    @property
    def name_checker(self) -> str:
        """ ФИО проверяющего """

        return self.getSignatureSurname('checker')

    @name_checker.setter
    def name_checker(self, surname):
        """ ФИО проверяющего """

        self.updSignatureSurname(position='checker', surname=surname)

    @property
    def name_approver(self) -> str:
        """ ФИО утверждающего """

        return self.getSignatureSurname('approver')

    @name_approver.setter
    def name_approver(self, surname):
        """ ФИО утверждающего """

        self.updSignatureSurname(position='approver', surname=surname)

    @property
    def name_n_contr(self) -> str:
        """ ФИО нормоконтролера """

        return self.getSignatureSurname('n_contr')

    @name_n_contr.setter
    def name_n_contr(self, surname):
        """ ФИО нормоконтролера """

        self.updSignatureSurname(position='n_contr', surname=surname)

    @property
    def name_m_contr(self) -> str:
        """ ФИО метролога """

        return self.getSignatureSurname('m_contr')

    @name_m_contr.setter
    def name_m_contr(self, surname):
        """ ФИО метролога """

        self.updSignatureSurname(position='m_contr', surname=surname)

    @property
    def sign(self) -> str:
        """ Буквенный код вида документа """

        if self.db_document.document_real.document_type.sign is None:
            return ''
        else:
            return self.db_document.document_real.document_type.sign

    @property
    def sign_with_exceptions(self) -> str:
        """ Буквенный код вида документа
            с учетом, что у спецификации и
            детали код вида документа отсутствует """

        return self.document_type.sign_with_exceptions

    @property
    def class_name(self) -> str:
        """ Класс документа (КД/ТД/ЭД) """

        return self.db_document.document_real.document_type.class_name

    @property
    def subtype_name(self) -> str:
        """ Подтип документа """

        return self.db_document.document_real.document_type.subtype_name

    @property
    def stage(self) -> str:
        """ Этап разработки """

        return self.db_document.document_real.stage.stage

    @stage.setter
    def stage(self, stage_name: str) -> None:
        """ Этап разработки """

        stage = DbDocumentStage.addDbDocumentStage(stage_name)
        self.db_document.document_real.updDocumentReal(db_document_stage=stage)
        # self.db_document.document_real.id_document_stage = stage.id_document_stage

    @property
    def db_type(self) -> DbDocumentType:
        """ Экземпляр DbDocumentType
            (типа документа по спецификации) """

        return self.db_document.document_real.document_type

    @property
    def product(self) -> Product:
        """ Основное изделие к которому относиться документ """

        builder = ProductBuilder()
        builder.setDbProduct(db_product=self.db_document.product)
        return builder.product

    @property
    def operations_db(self) -> dict[int, Operation]:
        # TODO Вынести метод в класс технологических документов
        """ Возвращает словарь операций для данного документа
            сохраненных в БД на данный момент
            {Порядковый номер операции: экземпляр Operation} """

        return self.dbOperations()

    @property
    def operations(self) -> dict[int, Operation]:
        # TODO Вынести метод в класс технологических документов
        """ Возвращает словарь операций для данного документа
            {Порядковый номер операции: экземпляр Operation} """

        return self._operations

    @operations.setter
    def operations(self, new_operations: dict[int, Operation]):
        # TODO Вынести метод в класс технологических документов
        """ Перезаписывает словарь операций для данного документа
            {Порядковый номер операции: экземпляр Operation} """

        self._operations = new_operations

    @property
    def litera(self) -> str:
        """ Возвращает литеру документа """

        return self._litera

    @litera.setter
    def litera(self, value: str) -> None:
        """ Изменяет значение литеры документа """

        self._litera = value

    @property
    def document_type(self) -> DocumentType:
        """ Возвращает тип документа """

        if self._document_type is None:
            document_real = self.db_document.document_real
            document_type = document_real.document_type
            self._document_type = \
                return_document_type(class_name=document_type.class_name,
                                     subtype_name=document_type.subtype_name,
                                     deno=self.deno,
                                     db_document_type=document_type)
        return self._document_type


class DocumentType:
    """ Вид документа
        инициализируется по сокращению или id """
    sign_exceptions = {'Спецификация': 'СП',
                       'Чертеж детали': 'ЧД',
                       'Ведомость': 'Вед',
                       'Чертежи ремонтные ': 'ЧР',
                       'Техническая документация на средства оснащения ремонта ': 'ТхД',
                       'Текст программы': 'ТПр',
                       'Выгрузка': 'Выг',
                       'Данные о результатах проектирования печатных плат': 'ДППП',
                       'STEP 3D': 'S3D'}

    def __init__(self) -> None:
        self._id_type = None
        self._class_name = None
        self._subclass_name = None
        self._type_name = None
        self._subtype_name = None
        self._sign = None
        self._description = None
        self._type_code = None
        self._method_code = None
        self._method_name = None
        self._organization_code = None
        self._organization_name = None
        self._db_document_type = None

    def __eq__(self, other: DocumentType) -> bool:
        """  """

        type_eq = False
        meth_eq = False
        org_eq = False
        if self.document_type == other.document_type:
            type_eq = True
        if self.method_code == other.method_code \
                or self.method_code is None \
                or other.method_code is None:
            meth_eq = True
        if self.organization_code == other.organization_code \
                or self.organization_code is None \
                or other.organization_code is None:
            org_eq = True
        return type_eq and meth_eq and org_eq

    @staticmethod
    def getAllTypes(class_name: tuple = ('КД',)) -> list[DocumentType]:
        """  """

        result = []
        for db_document_type in DbDocumentType.data.values():
            builder = DocumentTypeBuilder()
            builder.getDocumentType(class_name=db_document_type.class_name,
                                    subtype_name=db_document_type.subtype_name)
            document_type = builder.document_type
            if document_type.class_name in class_name:
                result.append(document_type)
        return result

    @staticmethod
    def documentTypes() -> list[DbDocumentType]:
        """  """

        return DbDocumentType.uniqueData()

    @property
    def document_type(self) -> DbDocumentType:
        """  """

        return self._db_document_type

    @property
    def id_type(self) -> int:
        """  """

        return self._db_document_type.id_type

    @property
    def class_name(self) -> str:
        """  """

        return self._db_document_type.class_name

    @property
    def subclass_name(self) -> str:
        """  """

        return self._db_document_type.subclass_name

    @property
    def type_name(self) -> str:
        """  """

        return self._db_document_type.type_name

    @property
    def subtype_name(self) -> str:
        """  """

        if self._db_document_type.sign == 'КТТП':
            if self.organization_code == '2':
                return 'Карта типового технологического процесса'
            return 'Карта группового технологического процесса'
        return self._db_document_type.subtype_name

    @property
    def sign(self) -> str:
        """  """

        if self._db_document_type.sign is None:
            return ''
        if self._db_document_type.sign == 'КТТП':
            if self.organization_code == '2':
                return 'КТТП'
            return 'КГТП'
        return self._db_document_type.sign

    @property
    def sign_with_exceptions(self):
        """  """

        return self.__class__.sign_exceptions.get(self.subtype_name, self.sign)

    @property
    def type_code(self) -> int:
        """  """

        return self._type_code

    @property
    def method_code(self) -> int:
        """  """

        return self._method_code

    @property
    def method_name(self) -> str:
        """  """

        return self._method_name

    @property
    def organization_code(self) -> str:
        """  """

        return self._organization_code

    @property
    def organization_name(self) -> str:
        """  """

        return self._organization_name

    @property
    def description(self) -> int:
        """  """

        return self._db_document_type.description


class DocumentStage:

    def __init__(self, stage: str) -> None:
        db_stages = DbDocumentStage.data
        try:
            self.db_stage = db_stages[str(stage).lower()]
        except KeyError:
            self.db_stage = db_stages[0]

    @staticmethod
    def getAllStages() -> list[DbDocumentStage]:
        """  """

        return DbDocumentStage.uniqueData()

    @property
    def id_stage(self) -> int:
        """  """

        return self.db_stage.id_document_stage

    @property
    def stage_name(self) -> str:
        """  """

        return self.db_stage.stage


class Operation:

    def __init__(self) -> None:
        DbOperationDef.updCheck()
        self._db_operation_doc = None
        self._document_main = None
        self._def_operation = None
        self._def_area = None
        self._possible_areas = set()
        self._doc_area = None
        self._def_workplace = None
        self._possible_workplaces = []
        self._doc_workplace = None
        self._def_profession = None
        self._possible_professions = []
        self._doc_profession = None
        self._order = None
        self._def_settings = {}
        self._cur_settings = []
        self._documents = {}
        self._sentences = {}
        self._sentences_for_del = []
        self._area_builder = AreaBuilder()
        self._workplace_builder = WorkplaceBuilder()
        self._profession_builder = ProfessionBuilder()

    def addSentence(self, order: int, sentence: Sentence):
        """  """

        if order not in self._sentences.keys():
            self._sentences[order] = sentence
        else:
            temp_sentences = {order: sentence}
            for old_order, sentence in self._sentences.items():
                if old_order < order:
                    temp_sentences[old_order] = sentence
                else:
                    temp_sentences[old_order + 1] = sentence
            self._sentences = temp_sentences

    def delSentence(self, order: num):
        """  """

        self._sentences_for_del.append(self._sentences[order])
        del self._sentences[order]

    def restoreSentenceOrder(self) -> None:
        """  """

        temp_sentences = {}
        orders = sorted(self._sentences.keys())
        for new_order, order in enumerate(orders):
            temp_sentences[new_order] = self._sentences[order]
        self._sentences = temp_sentences

    def initSentences(self) -> None:
        """  """

        self._sentences = {}
        DbSentenceDoc.updCheck()
        DbSettingDef.updCheck()
        operation_order = 0
        if self.id_operation_doc:
            key = (self.id_operation_doc, operation_order)
            while key in DbSentenceDoc.data:
                db_sentence_doc = DbSentenceDoc.data[key]
                if db_sentence_doc.id_sentence is not None:
                    db_default_sentence = db_sentence_doc.sentence
                    db_setting = db_sentence_doc.setting
                    setting = self._def_settings[db_setting]
                    setting.activated = True
                    sentence = setting.sentenceById(id_sentence=db_default_sentence.id_sentence)
                    sentence.db_sentence_doc = db_sentence_doc
                else:
                    sentence = Sentence(operation=self,
                                        custom_text=db_sentence_doc.custom_text,
                                        db_sentence_doc=db_sentence_doc)
                self.addSentence(order=operation_order,
                                 sentence=sentence)
                operation_order += 1
                key = (self.id_operation_doc, operation_order)

    def possibleAreas(self) -> list[Area]:
        """  """

        self._possible_areas = set()
        product_kind = self._document_main.product.product_kind
        if product_kind.id_kind in DbOperationDef.data:
            for db_operation_def_data in DbOperationDef.data[product_kind.id_kind]:
                if db_operation_def_data.id_operation == self.id_operation_def:
                    self._area_builder.createArea(name=db_operation_def_data.area.name)
                    self._possible_areas.add(self._area_builder.area)
            self._possible_areas = list(self._possible_areas)
        else:
            for db_area in DbArea.uniqueData():
                self._area_builder.createArea(name=db_area.name)
                self._possible_areas.add(self._area_builder.area)
            self._possible_areas = list(self._possible_areas)
        return self._possible_areas

    def possibleWorkplaces(self) -> list[Workplace]:
        """  """

        self._possible_workplaces = set()
        product_kind = self._document_main.product.product_kind
        if product_kind.id_kind in DbOperationDef.data:
            for db_operation_def_data in DbOperationDef.data[product_kind.id_kind]:
                if db_operation_def_data.id_operation == self.id_operation_def:
                    if db_operation_def_data.id_area == self.area.id:
                        self._workplace_builder.createWorkplace(name=db_operation_def_data.workplace.name)
                        self._possible_workplaces.add(self._workplace_builder.workplace)
            self._possible_workplaces = list(self._possible_workplaces)
        else:
            for db_workplace in DbWorkplace.uniqueData():
                self._workplace_builder.createWorkplace(name=db_workplace.name)
                self._possible_workplaces.add(self._workplace_builder.workplace)
            self._possible_workplaces = list(self._possible_workplaces)
        return self._possible_workplaces

    def possibleProfessions(self) -> list[Profession]:
        """  """

        self._possible_professions = set()
        product_kind = self._document_main.product.product_kind
        if product_kind.id_kind in DbOperationDef.data:
            for db_operation_def_data in DbOperationDef.data[product_kind.id_kind]:
                if db_operation_def_data.id_operation == self.id_operation_def:
                    if db_operation_def_data.id_area == self.area.id:
                        if db_operation_def_data.id_workplace == self.workplace.id:
                            self._profession_builder.createProfession(name=db_operation_def_data.profession.name)
                            self._possible_professions.add(self._profession_builder.profession)
            self._possible_professions = list(self._possible_professions)
        else:
            for db_profession in DbProfession.uniqueData():
                self._profession_builder.createProfession(name=db_profession.name)
                self._possible_professions.add(self._profession_builder.profession)
            self._possible_professions = list(self._possible_professions)
        return self._possible_professions

    @staticmethod
    def defaultOperationsName(product: Product | None = None) -> list[str]:
        """  """

        if product:
            id_kind = product.product_kind.id_kind
            if id_kind in DbOperationDef.data:
                return sort_un([item.operation.name for item in DbOperationDef.data[id_kind]])
        return sort_un([operation.name for operation in DbOperation.uniqueData()])

    @staticmethod
    def dbOperationByName(name: str) -> list[DbOperation]:
        """  """

        return [operation for operation in DbOperation.uniqueData() if operation.name == name]

    @property
    def settings(self) -> dict[DbSetting, Setting]:
        """  """

        if not self._def_settings:
            for db_setting in DbSetting.uniqueData():
                if db_setting.id_operation == self.id_operation_def:
                    new_setting = Setting(db_setting=db_setting, operation=self)
                    self._def_settings[db_setting] = new_setting
        return self._def_settings

    @property
    def documents(self) -> dict[Document]:
        """  """

        self._documents = {}
        for sentence in self._sentences.values():
            self._documents.update(sentence.doc)
        return self._documents

    @property
    def documents_from_text(self) -> set[str]:
        """  """

        denos = set()
        for sentence in self._sentences.values():
            denos.update(sentence.doc_from_text)
        return denos

    @property
    def documents_text(self) -> str:
        """  """

        denos = set()
        if self.documents:
            denos.update(self.documents.keys())
        if self.documents_from_text:
            denos.update(self.documents_from_text)
        return ', '.join(sorted(denos))

    @property
    def default_operation(self) -> DbOperation:
        """  """

        return self._def_operation

    @default_operation.setter
    def default_operation(self, operation: DbOperation) -> None:
        """  """

        self._def_operation = operation

    @property
    def id(self) -> int:
        """  """

        return self._def_operation.id_operation

    @property
    def name(self) -> str:
        """  """

        return self._def_operation.name

    @name.setter
    def name(self, value: str) -> None:
        """  """

        self.name = value

    @property
    def area(self) -> Area:
        """  """

        if self._doc_area is None:
            return self.default_area
        else:
            return self._doc_area

    @area.setter
    def area(self, name: str) -> None:
        """  """

        self._area_builder.createArea(name=name)
        self._doc_area = self._area_builder.area
        self.possibleWorkplaces()
        self.workplace = self._possible_workplaces[0].name

    @property
    def default_area(self) -> Area:
        """  """

        return self._def_area

    @property
    def possible_areas_names(self) -> list[str]:
        """  """

        return [area.name for area in self._possible_areas]

    @property
    def default_workplace(self) -> Workplace:
        """  """

        return self._def_workplace

    @property
    def possible_workplaces_names(self) -> list[Workplace]:
        """  """

        return [workplace.name for workplace in self._possible_workplaces]

    @property
    def workplace(self) -> Workplace:
        """  """

        if self._doc_workplace is None:
            return self.default_workplace
        else:
            return self._doc_workplace

    @workplace.setter
    def workplace(self, name: str) -> None:
        """  """

        self._workplace_builder.createWorkplace(name=name)
        self._doc_workplace = self._workplace_builder.workplace
        self.possibleProfessions()
        self.profession = self._possible_professions[0].name

    @property
    def profession(self) -> Profession:
        """  """

        if self._doc_profession is None:
            return self.default_profession
        else:
            return self._doc_profession

    @profession.setter
    def profession(self, name: str) -> None:
        """  """

        self._profession_builder.createProfession(name=name)
        self._doc_profession = self._profession_builder.profession

    @property
    def default_profession(self) -> Profession:
        """  """

        return self._def_profession

    @property
    def possible_professions_names(self) -> list[str]:
        """  """

        return [profession.name for profession in self._possible_professions]

    @property
    def num(self) -> str:
        """  """

        return '0' * (3 - len(str((self.order + 1) * 5))) + str((self.order + 1) * 5)

    @property
    def order(self) -> int:
        """  """

        return self._order

    @order.setter
    def order(self, value: int) -> None:
        """  """

        if self._order != value:
            del self.order
            self._order = value
            key = (self.document_main,
                   self._order)
            # OperationBuilder().updOperation(operation=self)
            OperationBuilder().operations.update({key: self})

    @order.deleter
    def order(self) -> None:
        """  """

        key = (self.document_main,
               self._order)
        try:
            if OperationBuilder().operations[key] == self:
                del OperationBuilder().operations[key]
        except KeyError:
            pass
        # OperationBuilder().delOperation(operation=self)

    @property
    def documents_and_iot(self) -> str:
        """  """

        return ', '.join([text for text in [self.documents_text, self.iot] if text != ''])

    @property
    def document_main(self) -> Document:
        """  """

        return self._document_main

    @document_main.setter
    def document_main(self, document: Document) -> None:
        """  """

        self._document_main = document

    @property
    def id_operation_def(self) -> int:
        """  """

        if self.default_operation is not None:
            return self.default_operation.id_operation

    @property
    def db_operation_doc(self) -> DbOperationDoc:
        """  """

        return self._db_operation_doc
        # try:
        #     key = (self.document_main.id_document_real,
        #            self.default_operation.id_operation,
        #            self.order)
        #     return DbOperationDoc.data.get(key, None)
        # except AttributeError:
        #     return None

    @db_operation_doc.setter
    def db_operation_doc(self, value: DbOperationDoc) -> None:
        """  """

        self._db_operation_doc = value

    @property
    def id_operation_doc(self) -> int:
        """  """

        if self.db_operation_doc is not None:
            return self.db_operation_doc.id_operation_doc

    @property
    def sentences(self) -> dict[num, Sentence]:
        """  """

        return self._sentences

    @sentences.setter
    def sentences(self, value: dict[num, Sentence]) -> None:
        """  """

        self._sentences = value

    @property
    def sentences_for_del(self) -> list[Sentence]:
        """  """

        return self._sentences_for_del

    @sentences_for_del.setter
    def sentences_for_del(self, value: dict[num, Sentence]) -> None:
        """  """

        self._sentences_for_del = value

    @property
    def iot(self) -> str:
        """  """

        _iot = set()
        for sentence in self._sentences.values():
            _iot.update(sentence.iot)
        if _iot:
            _iot = sorted(list(_iot))
            return ', '.join(_iot)
        else:
            return ''

    @property
    def rig(self) -> str:
        """  """

        _rig = set()
        for sentence in self._sentences.values():
            _rig.update(sentence.rig)
        if _rig:
            _rig = sorted(list(_rig))
            text = ', '.join(_rig)
            return ''.join([text[0].upper(), text[1:]])
        else:
            return ''

    @property
    def equipment(self) -> str:
        """  """

        _equipment = set()
        for sentence in self._sentences.values():
            _equipment.update(sentence.equipment)
        if _equipment:
            _equipment = sorted(list(_equipment))
            text = ', '.join(_equipment)
            return ''.join([text[0].upper(), text[1:]])
        else:
            return ''

    @property
    def mat(self) -> str:
        """  """

        _mat = set()
        for sentence in self._sentences.values():
            _mat.update(sentence.mat)
        if _mat:
            _mat = sorted(list(_mat))
            text = ', '.join(_mat)
            return ''.join([text[0].upper(), text[1:]])
        else:
            return ''


class Area:
    """  """

    def __init__(self) -> None:
        self.db_area = None

    @staticmethod
    def defaultAreaNames(product_kind: ProductKind, operation: Operation) -> list[str]:
        """  """

        DbOperationDef.updCheck()
        if product_kind.id_kind in DbOperationDef.data:
            if operation is not None:
                default_areas = []
                for item in DbOperationDef.data[product_kind.id_kind]:
                    if item.id_operation == operation.id_operation_def:
                        default_areas.append(item.area.name)
                return sort_un(default_areas)
        return list(set([area.name for area in DbArea.uniqueData()]))

    @staticmethod
    def defaultAreaShortNames() -> list[str]:
        """  """

        return list(set([area.name_short for area in DbArea.uniqueData()]))

    @property
    def name(self) -> str:
        """  """

        return self.db_area.name

    @property
    def name_short(self) -> str:
        """  """

        return self.db_area.name_short

    @property
    def id(self) -> int:
        """  """

        return self.db_area.id_area


class Workplace:
    """  """

    def __init__(self) -> None:
        self.db_workplace = None

    @staticmethod
    def defaultWorkplaceNames() -> list[str]:
        """  """

        return list(set([workplace.name for workplace in DbWorkplace.uniqueData()]))

    @property
    def name(self) -> str:
        """  """

        return self.db_workplace.name

    @property
    def id(self) -> int:
        """  """

        return self.db_workplace.id_workplace


class Setting:
    """  """

    def __init__(self, db_setting: DbSetting, operation: Operation) -> None:
        self._db_setting = db_setting
        self._operation = operation
        self._activated = False
        self._db_setting_doc = None
        self._def_sentences = self.initDefaultSentences()

    def initDefaultSentences(self) -> dict[int, Sentence]:
        """  """

        DbSentence.updCheck()
        DbSettingDef.updCheck()
        self._def_sentences = {}
        for db_setting_def in DbSettingDef.data.values():
            if db_setting_def.id_setting == self.default_setting_id:
                sentence = Sentence(operation=self.operation,
                                    text=db_setting_def.sentence.text,
                                    def_db_sentence=db_setting_def.sentence,
                                    setting=self)
                self._def_sentences[db_setting_def.sentence_order] = sentence
        return self._def_sentences

    def addSentences(self) -> None:
        """  """

        total_sentences = len(self._operation.sentences)
        for order, sentence in self.default_sentences.items():
            self.operation.addSentence(order=order + total_sentences,
                                       sentence=sentence)

    def delSentences(self) -> None:
        """  """

        order_for_delete = []
        for order, sentence in self._operation.sentences.items():
            if sentence.setting == self:
                order_for_delete.append(order)
        for order in order_for_delete:
            self._operation.delSentence(order=order)
        self._operation.restoreSentenceOrder()

    def sentenceById(self, id_sentence: int) -> Sentence | None:
        for sentence in self.default_sentences.values():
            if sentence.id_def_sentence == id_sentence:
                return sentence
        return None

    @property
    def default_setting_id(self) -> int:
        """  """

        return self._db_setting.id_setting

    @property
    def name(self) -> str:
        """  """

        return self._db_setting.text

    @property
    def activated(self) -> bool:
        """  """

        return self._activated

    @activated.setter
    def activated(self, value: bool) -> None:
        """  """

        self._activated = value

    @property
    def operation(self) -> Operation:
        """  """

        return self._operation

    @property
    def default_sentences(self) -> dict[int, Sentence]:
        """  """

        return self._def_sentences

    @property
    def db_setting(self):
        """  """

        return self._db_setting

    @property
    def db_setting_doc(self):
        """  """

        return self._db_setting_doc


class Sentence:
    """  """

    related_documents = {}

    def __init__(self, operation: Operation,
                 text: str = '',
                 custom_text: str | None = None,
                 setting: Setting | None = None,
                 def_db_sentence: DbSentence | None = None,
                 db_sentence_doc: DbSentenceDoc | None = None) -> None:
        self.getRelatedDocuments()
        self._operation = operation
        self._def_db_sentence = def_db_sentence
        self._text = text
        self._custom_text = custom_text
        self._setting = setting
        self._db_sentence_doc = db_sentence_doc
        self._product = self._operation.document_main.product
        self._iot = {}
        self._rig = {}
        self._mat = {}
        self._doc = {}
        self._doc_from_text = set()
        self._equipment = {}
        self.initIot()
        self.initDoc()
        self.initRig()
        self.initEquipment()
        self.initMat()

    def initIot(self) -> None:
        """  """

        self.iot_builder = IotBuilder()
        if self._def_db_sentence is not None:
            self.initDefaultIot()
        elif self.id_sentence_doc is not None:
            self.initDocumentIot()
        else:
            self._iot = {}

    def initDefaultIot(self) -> dict[str, IOT]:
        """  """

        DbIOTDef.updCheck()
        self._iot = {}
        if self.id_def_sentence in DbIOTDef.data:
            for db_iot in DbIOTDef.data[self.id_def_sentence]:
                self.createIot(db_iot=db_iot.iot)
        return self._iot

    def initDocumentIot(self) -> dict[str, IOT]:
        """  """

        self._iot = {}
        DbIOTDoc.updCheck()
        if self.id_sentence_doc in DbIOTDoc.data:
            for db_iot in DbIOTDoc.data[self.id_sentence_doc]:
                self.createIot(db_iot=db_iot.iot)
        return self._iot

    def createIot(self, db_iot: DbIOT) -> IOT:
        """  """

        self.iot_builder.createIot(deno=db_iot.deno)
        iot = self.iot_builder.iot
        self._iot[iot.deno] = iot
        return iot

    def initDoc(self) -> None:
        """  """

        self.doc_builder = DocumentBuilder()
        if self._def_db_sentence is not None:
            self.initDefaultDoc()
        elif self.id_sentence_doc is not None:
            self.initDocumentDoc()
        else:
            self._doc = {}

    def initDefaultDoc(self) -> dict[str, Document]:
        """  """

        DbDocDef.updCheck()
        self._doc = {}
        if self.id_def_sentence in DbDocDef.data:
            for db_doc_def in DbDocDef.data[self.id_def_sentence]:
                document = self.product.getDocumentByType(class_name=db_doc_def.document_type.class_name,
                                                          subtype_name=db_doc_def.document_type.subtype_name,
                                                          only_text=False,
                                                          only_relevant=True)
                if document:
                    self.createDoc(document=document[0])
        return self._doc

    def initDocumentDoc(self) -> dict[str, Document]:
        """  """

        self._doc = {}
        DbDocDoc.updCheck()
        if self.id_sentence_doc in DbDocDoc.data:
            for db_doc in DbDocDoc.data[self.id_sentence_doc]:
                document = self.product.getDocumentByType(class_name=db_doc.document_real.document_type.class_name,
                                                          subtype_name=db_doc.document_real.document_type.subtype_name,
                                                          only_text=False,
                                                          only_relevant=True)
                if document:
                    self.createDoc(document=document[0])
        return self._doc

    def createDoc(self, document: Document) -> None:
        """  """

        self._doc[document.deno] = document

    def initRig(self) -> None:
        """  """

        self.rig_builder = RigBuilder()
        if self._def_db_sentence is not None:
            self.initDefaultRig()
        elif self.id_sentence_doc is not None:
            self.initDocumentRig()
        else:
            self._rig = {}

    def initDefaultRig(self) -> dict[str, Rig]:
        """  """

        DbRigDef.updCheck()
        self._rig = {}
        if self.id_def_sentence in DbRigDef.data:
            for db_rig in DbRigDef.data[self.id_def_sentence]:
                self.createRig(db_rig=db_rig.rig)
        return self._rig

    def initDocumentRig(self) -> dict[str, Rig]:
        """  """

        self._rig = {}
        DbRigDoc.updCheck()
        if self.id_sentence_doc in DbRigDoc.data:
            for db_rig in DbRigDoc.data[self.id_sentence_doc]:
                self.createRig(db_rig=db_rig.rig)
        return self._rig

    def createRig(self, db_rig: DbRig) -> Rig:
        """  """

        self.rig_builder.createRig(name=db_rig.name)
        rig = self.rig_builder.rig
        self._rig[rig.name] = rig
        return rig

    def initMat(self) -> None:
        """  """

        self.mat_builder = MatBuilder()
        if self._def_db_sentence is not None:
            self.initDefaultMat()
        elif self.id_sentence_doc is not None:
            self.initDocumentMat()
        else:
            self._mat = {}

    def initDefaultMat(self) -> dict[str, Mat]:
        """  """

        DbMaterialDef.updCheck()
        self._mat = {}
        if self.id_def_sentence in DbMaterialDef.data:
            for db_mat in DbMaterialDef.data[self.id_def_sentence]:
                self.createMat(db_mat=db_mat.material)
        return self._mat

    def initDocumentMat(self) -> dict[str, Mat]:
        """  """

        self._mat = {}
        DbMaterialDoc.updCheck()
        if self.id_sentence_doc in DbMaterialDoc.data:
            for db_mat in DbMaterialDoc.data[self.id_sentence_doc]:
                self.createMat(db_mat=db_mat.material)
        return self._mat

    def createMat(self, db_mat: DbMaterial) -> Mat:
        """  """

        self.mat_builder.createMat(name=db_mat.name)
        mat = self.mat_builder.mat
        self._mat[mat.name] = mat
        return mat

    def initEquipment(self) -> None:
        """  """

        self.equipment_builder = EquipmentBuilder()
        if self._def_db_sentence is not None:
            self.initDefaultEquipment()
        elif self.id_sentence_doc is not None:
            self.initDocumentEquipment()
        else:
            self._equipment = {}

    def initDefaultEquipment(self) -> dict[str, Equipment]:
        """  """

        DbEquipmentDef.updCheck()
        self._equipment = {}
        if self.id_def_sentence in DbEquipmentDef.data:
            for db_equipment in DbEquipmentDef.data[self.id_def_sentence]:
                self.createEquipment(db_equipment=db_equipment.equipment)
        return self._equipment

    def initDocumentEquipment(self) -> dict[str, Equipment]:
        """  """

        self._equipment = {}
        DbEquipmentDoc.updCheck()
        if self.id_sentence_doc in DbEquipmentDoc.data:
            for db_equipment in DbEquipmentDoc.data[self.id_sentence_doc]:
                self.createEquipment(db_equipment=db_equipment.equipment)
        return self._equipment

    def getRelatedDocuments(self):
        """  """

        if self.related_documents == {}:
            config = CONFIG
            config_type = 'excel_document'
            related_documents_str = config.data[config_type]['related_documents'].replace(" ", "")
            related_documents_list = related_documents_str.split(",")
            for string in related_documents_list:
                string_list = string.split("+")
                self.related_documents[string_list[0]] = string_list[1]

    def createEquipment(self, db_equipment: DbEquipment) -> Equipment:
        """  """

        self.equipment_builder.createEquipment(name=db_equipment.name)
        equipment = self.equipment_builder.equipment
        self._equipment[equipment.name] = equipment
        return equipment

    def convertToCustom(self, text: str | None = None):
        """  """

        if text is not None:
            self._custom_text = text
            self.findDocInText(text=text)
        else:
            self._custom_text = self.text
        self.setting = None
        self.def_db_sentence = None

    def findDocInText(self, text: str):
        """  """

        developer = r'[А-Я]{4}'
        kd = r'[0-9]{6}\.[0-9]{3}'
        variation = r'-[0-9]{2,3}'
        doc_type = r'[А-Я]{1,2}[0-9]{0,2}'
        deno_kd = f'{kd}(?:{variation}|)(?:{doc_type}|)'
        deno_spo = r'[0-9]{5}-[0-9]{2}'
        deno_td = r'[0-9]{5}\.[0-9]{5}'
        deno = f'{developer}\.(?:{deno_spo}|{deno_kd}|{deno_td})'
        self._doc_from_text = set(re.findall(deno, text))
        temp_set = set()
        for deno in self._doc_from_text:
            spec_deno = f'{developer}\.{kd}(?:{variation}|)'
            spec_list = re.findall(spec_deno, deno)
            if spec_list:
                spec = spec_list[0]
                temp_set.add(spec)
                doc_type_current = deno.replace(spec, "")
                related_document = self.related_documents.get(doc_type_current, None)
                if related_document is not None:
                    temp_set.add(f"{spec}{related_document}")
        self._doc_from_text.update(temp_set)
        # self.findDocInTextShort(text=text)

    def findDocInTextShort(self, text: str):
        """  """

        doc_type = r'[А-Я]{1,2}[0-9]{0,2}'
        symb = '[*]'
        deno = f'{symb}{doc_type}'
        temp_set = set(re.findall(deno, text))
        self._doc_from_text.update(temp_set)

    @property
    def size_pixel_excel(self):
        """  """

        font = QFont("Times", 10)
        fm = QFontMetrics(font)
        return fm.width(self.text)

    @property
    def id_operation(self) -> int:
        """  """

        return self._operation.db_operation_doc.id_operation_doc

    @property
    def text(self) -> str:
        """  """

        if self._custom_text is not None:
            return self._custom_text
        return self._text \
            .replace('ИЗДЕЛИЯ', self._product.product_kind_roditelnyy) \
            .replace('ИЗДЕЛИЕ', self._product.product_kind_imenitelnyy) \
            .replace('ИЗДЕЛИЮ', self._product.product_kind_datelnyy) \
            .replace('ИЗДЕЛИЕМ', self._product.product_kind_tvoritelnyy) \
            .replace('ИЗДЕЛИИ', self._product.product_kind_predlozhnyy)

    @text.setter
    def text(self, value: str) -> None:
        """  """

        self._text = value

    @property
    def custom_text(self) -> str:
        """  """

        return self._custom_text

    @custom_text.setter
    def custom_text(self, value: str) -> None:
        """  """

        self._custom_text = value

    @property
    def setting(self) -> Setting:
        """  """

        return self._setting

    @setting.setter
    def setting(self, value: Setting) -> None:
        """  """

        self._setting = value

    @property
    def source(self) -> str:
        """  """

        if self._setting is None:
            return 'Определено пользователем'
        return self._setting.name

    @property
    def db_sentence_doc(self) -> DbSentenceDoc:
        """  """

        return self._db_sentence_doc

    @db_sentence_doc.setter
    def db_sentence_doc(self, value: DbSentenceDoc) -> None:
        """  """

        self._db_sentence_doc = value

    @property
    def id_sentence_doc(self) -> int:
        """  """

        if self._db_sentence_doc is not None:
            return self._db_sentence_doc.id_sentence_doc

    @property
    def def_db_sentence(self) -> DbSentence:
        """  """

        return self._def_db_sentence

    @def_db_sentence.setter
    def def_db_sentence(self, value: DbSentence) -> None:
        """  """

        self._def_db_sentence = value

    @property
    def id_def_sentence(self) -> int | None:
        """  """

        if self._def_db_sentence is not None:
            return self._def_db_sentence.id_sentence

    @property
    def iot(self) -> dict[str, IOT]:
        """  """

        return self._iot

    @iot.setter
    def iot(self, value: dict[str, IOT]) -> None:
        """  """

        self._iot = value

    @property
    def doc(self) -> dict[str, Document]:
        """  """

        return self._doc

    @doc.setter
    def doc(self, value: dict[str, Document]) -> None:
        """  """

        self._doc = value

    @property
    def doc_ids(self) -> list[int]:
        """  """

        return [document.id_document_real for document in self._doc.values()]

    @property
    def doc_from_text(self) -> set[str]:
        """  """

        self.findDocInText(text=self.text)
        return self._doc_from_text

    @property
    def rig(self) -> dict[str, Rig]:
        """  """

        return self._rig

    @rig.setter
    def rig(self, value: dict[str, Rig]) -> None:
        """  """

        self._rig = value

    @property
    def equipment(self) -> dict[str, Equipment]:
        """  """

        return self._equipment

    @equipment.setter
    def equipment(self, value: dict[str, Equipment]) -> None:
        """  """

        self._equipment = value

    @property
    def mat(self) -> dict[str, Mat]:
        """  """

        return self._mat

    @mat.setter
    def mat(self, value: dict[str, Mat]) -> None:
        """  """

        self._mat = value

    @property
    def product(self) -> Product:
        """  """

        return self._operation.document_main.product


class IOT:
    """  """

    def __init__(self) -> None:
        self._db_iot = None

    @property
    def db_iot(self) -> DbIOT:
        """  """

        return self._db_iot

    @db_iot.setter
    def db_iot(self, value: DbIOT) -> None:
        """  """

        self._db_iot = value

    @property
    def deno(self) -> str:
        """  """

        if self._db_iot is not None:
            return self._db_iot.deno

    @property
    def name(self) -> str:
        """  """

        if self._db_iot is not None:
            return self._db_iot.name

    @property
    def name_short(self) -> str:
        """  """

        if self._db_iot is not None:
            return self._db_iot.name_short

    @property
    def type_short(self) -> str:
        """  """

        if self._db_iot is not None:
            return self._db_iot.type_short

    @staticmethod
    def allIot() -> list[DbIOT]:
        """  """

        return DbIOT.uniqueData()

    @staticmethod
    def allIotTypes() -> set[str]:
        """  """

        return DbIOT.allTypeShort()


class Rig:
    """  """

    def __init__(self) -> None:
        self._db_rig = None

    @property
    def db_rig(self) -> DbRig:
        """  """

        return self._db_rig

    @db_rig.setter
    def db_rig(self, value: DbRig) -> None:
        """  """

        self._db_rig = value

    @property
    def name(self) -> str | None:
        """  """

        if self._db_rig is not None:
            return self._db_rig.name

    @property
    def name_short(self) -> str | None:
        """  """

        if self._db_rig is not None:
            return self._db_rig.name_short

    @property
    def rig_type(self) -> str | None:
        """  """

        if self._db_rig is not None:
            return self._db_rig.rig_type

    @property
    def document(self) -> str | None:
        """  """

        if self._db_rig is not None:
            return self._db_rig.document

    @property
    def kind(self) -> str | None:
        """  """

        if self._db_rig is not None:
            return self._db_rig.kind

    @staticmethod
    def allRig():
        """  """

        return DbRig.uniqueData()

    @staticmethod
    def allRigShortNames() -> list[DbRig]:
        """  """

        DbRig.updCheck()
        return DbRig.all_name_short

    @staticmethod
    def allRigTypes() -> set[str]:
        """  """

        return DbRig.allTypes()


class Mat:
    """  """

    def __init__(self) -> None:
        self._db_mat = None

    @property
    def db_mat(self) -> DbMaterial:
        """  """

        return self._db_mat

    @db_mat.setter
    def db_mat(self, value: DbMaterial) -> None:
        """  """

        self._db_mat = value

    @property
    def name(self):
        """  """

        if self._db_mat is not None:
            return self._db_mat.name

    @property
    def name_short(self) -> str | None:
        """  """

        if self._db_mat is not None:
            return self._db_mat.name_short

    @property
    def mat_type(self) -> str | None:
        """  """

        if self._db_mat is not None:
            return self._db_mat.mat_type

    @property
    def document(self) -> str | None:
        """  """

        if self._db_mat is not None:
            return self._db_mat.document

    @property
    def kind(self) -> str | None:
        """  """

        if self._db_mat is not None:
            return self._db_mat.kind

    @staticmethod
    def allMat() -> list[DbMaterial]:
        """  """

        return DbMaterial.uniqueData()

    @staticmethod
    def allMatTypes() -> set[str]:
        """  """

        return DbMaterial.allTypes()

    @staticmethod
    def allMatKinds() -> set[str]:
        """  """

        return DbMaterial.allKinds()


class Equipment:
    """  """

    def __init__(self) -> None:
        self._db_equipment = None

    @property
    def db_equipment(self) -> DbEquipment:
        """  """

        return self._db_equipment

    @db_equipment.setter
    def db_equipment(self, value: DbEquipment) -> None:
        """  """

        self._db_equipment = value

    @property
    def name(self) -> str | None:
        """  """

        if self._db_equipment is not None:
            return self._db_equipment.name

    @property
    def name_short(self) -> str | None:
        """  """

        if self._db_equipment is not None:
            return self._db_equipment.name_short

    @property
    def equipment_type(self) -> str | None:
        """  """

        if self._db_equipment is not None:
            return self._db_equipment.type

    @staticmethod
    def allEquipment() -> list[DbEquipment]:
        """  """

        return DbEquipment.uniqueData()

    @staticmethod
    def allEquipmentShortNames() -> set[str]:
        """  """

        return DbEquipment.allShortNames()


class Profession:
    """  """

    def __init__(self) -> None:
        self.db_profession = None

    @staticmethod
    def defaultProfessionCodes() -> list[str]:
        """  """

        return sorted(list(set([db_profession.code for db_profession in DbProfession.uniqueData()])))

    @staticmethod
    def defaultProfessionNames() -> list[str]:
        """  """

        return sorted(list(set([db_profession.profession for db_profession in DbProfession.uniqueData()])))

    @property
    def id(self) -> int:
        """  """

        return self.db_profession.id_profession

    @property
    def name(self) -> str:
        """  """

        return self.db_profession.name

    @property
    def code(self) -> str:
        """  """

        return self.db_profession.code


class User:
    """  """

    def __init__(self, user_name) -> None:
        self.db_user = None
        self.getDbUser(user_name)

    def getDbUser(self, user_name):
        """  """

        self.db_user = DbUsers.getData(user_name)
        if self.db_user is None:
            self.db_user = DbUsers.addNewUser(user_name)

    @property
    def id_user(self) -> int:
        """  """

        return self.db_user.id_user

    @property
    def name(self) -> str:
        """  """

        return self.db_user.name

    @name.setter
    def name(self, value: str):
        """  """

        DbUsers.updUser(user_name=self.user_name, name=value)

    @property
    def surname(self) -> str:
        """  """

        return self.db_user.surname

    @property
    def patronymic(self) -> str:
        """  """

        return self.db_user.patronymic

    @property
    def user_name(self) -> str:
        """  """

        return self.db_user.user_name

    @property
    def password(self) -> str:
        """  """

        return self.db_user.password

    @property
    def id_product_last(self) -> int:
        """  """

        return self.db_user.id_product_last

    @property
    def product(self) -> Product | None:
        """  """

        if self.db_user.id_product_last is not None:
            builder = ProductBuilder()
            builder.setDbProduct(db_product=self.db_user.product)
            return builder.product

    @product.setter
    def product(self, value: Product):
        """  """

        DbUsers.updUser(user_name=self.user_name,
                        id_product_last=value.id_product)