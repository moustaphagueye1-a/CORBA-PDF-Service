# PDFService.py — Stubs CORBA Python
# Généré par : omniidl -bpython -Wbpackage=corba_stubs PDFService.idl
# Ce fichier est PRÉ-GÉNÉRÉ pour référence.
# Dans Docker, omniidl régénère automatiquement ces stubs depuis l'IDL.

import omniORB
from omniORB import CORBA, PortableServer

# ── Constantes et TypeCodes ────────────────────────────────────────
_0_PDFService = omniORB.openModule("PDFService")
_0_PDFService__POA = omniORB.openModule("PDFService__POA")

# ── Séquences ─────────────────────────────────────────────────────
_0_PDFService.ByteArray   = CORBA.TypeCode("IDL:PDFService/ByteArray:1.0")
_0_PDFService.StringList  = CORBA.TypeCode("IDL:PDFService/StringList:1.0")
_0_PDFService.LongList    = CORBA.TypeCode("IDL:PDFService/LongList:1.0")

# ── Exception PDFException ─────────────────────────────────────────
class PDFException(CORBA.UserException):
    _NP_RepositoryId = "IDL:PDFService/PDFException:1.0"
    def __init__(self, message=''):
        CORBA.UserException.__init__(self, message)
        self.message = message

_0_PDFService.PDFException = PDFException
omniORB.registerType(PDFException._NP_RepositoryId,
    PDFException, CORBA.TypeCode("IDL:PDFService/PDFException:1.0"))

# ── Structure PDFInfo ──────────────────────────────────────────────
class PDFInfo(omniORB.StructBase):
    _NP_RepositoryId = "IDL:PDFService/PDFInfo:1.0"
    def __init__(self, pageCount=0, wordCount=0, fileSize=0,
                 title='', author='', subject='', creator='', creationDate=''):
        self.pageCount    = pageCount
        self.wordCount    = wordCount
        self.fileSize     = fileSize
        self.title        = title
        self.author       = author
        self.subject      = subject
        self.creator      = creator
        self.creationDate = creationDate

_0_PDFService.PDFInfo = PDFInfo
omniORB.registerType(PDFInfo._NP_RepositoryId, PDFInfo,
    CORBA.TypeCode("IDL:PDFService/PDFInfo:1.0"))

# ── Interface PDFManager ───────────────────────────────────────────
class PDFManager(CORBA.Object):
    _NP_RepositoryId = "IDL:PDFService/PDFManager:1.0"

    def __init__(self): raise RuntimeError("Stub only — ne pas instancier directement")

    # ── Méthodes stub (signatures) ─────────────────────────────────
    def mergePDFs(self, pdf1, pdf2):         raise CORBA.NO_IMPLEMENT()
    def splitPDF(self, pdf, fromPage, toPage): raise CORBA.NO_IMPLEMENT()
    def extractPages(self, pdf, pageNumbers): raise CORBA.NO_IMPLEMENT()
    def deletePages(self, pdf, pageNumbers):  raise CORBA.NO_IMPLEMENT()
    def extractText(self, pdf):               raise CORBA.NO_IMPLEMENT()
    def createPDF(self, content, title):      raise CORBA.NO_IMPLEMENT()
    def addPassword(self, pdf, userPwd, ownerPwd): raise CORBA.NO_IMPLEMENT()
    def convertToImage(self, pdf, pageNum, dpi):   raise CORBA.NO_IMPLEMENT()
    def searchText(self, pdf, keyword):       raise CORBA.NO_IMPLEMENT()
    def addWatermark(self, pdf, text):        raise CORBA.NO_IMPLEMENT()
    def getPDFInfo(self, pdf):                raise CORBA.NO_IMPLEMENT()
    def compressPDF(self, pdf):               raise CORBA.NO_IMPLEMENT()
    def rotatePage(self, pdf, pageNum, deg):  raise CORBA.NO_IMPLEMENT()
    def reorderPages(self, pdf, newOrder):    raise CORBA.NO_IMPLEMENT()

    @staticmethod
    def _narrow(obj):
        return omniORB.CORBA.Object._narrow(obj, PDFManager)

    _NP_RepositoryIds = (
        "IDL:PDFService/PDFManager:1.0",
        "IDL:omg.org/CORBA/Object:1.0",
    )

_0_PDFService.PDFManager = PDFManager
omniORB.registerObjref(PDFManager._NP_RepositoryId, PDFManager)

# ── Skeleton POA ───────────────────────────────────────────────────
class PDFManager(PortableServer.Servant):
    _NP_RepositoryId = "IDL:PDFService/PDFManager:1.0"
    _omni_op_d = {}

_0_PDFService__POA.PDFManager = PDFManager
