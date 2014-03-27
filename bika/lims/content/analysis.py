from AccessControl import ClassSecurityInfo
from DateTime import DateTime
from Products.ATContentTypes.content import schemata
from Products.ATExtensions.ateapi import DateTimeField, DateTimeWidget, RecordsField
from Products.Archetypes import atapi
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.public import *
from Products.Archetypes.references import HoldingReference
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from Products.CMFEditions.ArchivistTool import ArchivistRetrieveError
from bika.lims import bikaMessageFactory as _
from bika.lims import logger
from bika.lims.browser.fields import DurationField
from bika.lims.browser.fields import HistoryAwareReferenceField
from bika.lims.browser.fields import InterimFieldsField
from bika.lims.permissions import Unassign
from bika.lims.browser.widgets import DurationWidget
from bika.lims.browser.widgets import RecordsWidget as BikaRecordsWidget
from bika.lims.config import PROJECTNAME
from bika.lims.content.bikaschema import BikaSchema
from bika.lims.interfaces import IAnalysis
from decimal import Decimal
from zope.interface import implements
import datetime
import math

schema = BikaSchema.copy() + Schema((
    HistoryAwareReferenceField('Service',
        required=1,
        allowed_types=('AnalysisService',),
        relationship='AnalysisAnalysisService',
        referenceClass=HoldingReference,
        widget=ReferenceWidget(
            label=_("Analysis Service"),
        )
    ),
    HistoryAwareReferenceField('Calculation',
        allowed_types=('Calculation',),
        relationship='AnalysisCalculation',
        referenceClass=HoldingReference,
    ),
    ReferenceField('Attachment',
        multiValued=1,
        allowed_types=('Attachment',),
        referenceClass = HoldingReference,
        relationship = 'AnalysisAttachment',
    ),
    InterimFieldsField('InterimFields',
        widget = BikaRecordsWidget(
            label=_("Calculation Interim Fields"),
        )
    ),
    StringField('Result',
    ),
    DateTimeField('ResultCaptureDate',
        widget = ComputedWidget(
            visible=False,
        ),
    ),
    StringField('ResultDM',
    ),
    BooleanField('Retested',
        default = False,
    ),
    DurationField('MaxTimeAllowed',
        widget = DurationWidget(
            label=_("Maximum turn-around time"),
            description=_("Maximum time allowed for completion of the analysis. "
                            "A late analysis alert is raised when this period elapses"),
        ),
    ),
    DateTimeField('DateAnalysisPublished',
        widget = DateTimeWidget(
            label=_("Date Published"),
        ),
    ),
    DateTimeField('DueDate',
        widget = DateTimeWidget(
            label=_("Due Date"),
        ),
    ),
    IntegerField('Duration',
        widget = IntegerWidget(
            label=_("Duration"),
        )
    ),
    IntegerField('Earliness',
        widget = IntegerWidget(
            label=_("Earliness"),
        )
    ),
    BooleanField('ReportDryMatter',
        default = False,
    ),
    StringField('Analyst',
    ),
    TextField('Remarks',
    ),
    ReferenceField('Instrument',
        required = 0,
        allowed_types = ('Instrument',),
        relationship = 'AnalysisInstrument',
        referenceClass = HoldingReference,
    ),
    ReferenceField('Method',
        required = 0,
        allowed_types = ('Method',),
        relationship = 'AnalysisMethod',
        referenceClass = HoldingReference,
    ),
    ReferenceField('SamplePartition',
        required = 0,
        allowed_types = ('SamplePartition',),
        relationship = 'AnalysisSamplePartition',
        referenceClass = HoldingReference,
    ),
    ComputedField('ClientUID',
        expression = 'context.aq_parent.aq_parent.UID()',
    ),
    ComputedField('ClientTitle',
        expression = 'context.aq_parent.aq_parent.Title()',
    ),
    ComputedField('RequestID',
        expression = 'context.aq_parent.getRequestID()',
    ),
    ComputedField('ClientOrderNumber',
        expression = 'context.aq_parent.getClientOrderNumber()',
    ),
    ComputedField('Keyword',
        expression = 'context.getService().getKeyword()',
    ),
    ComputedField('ServiceTitle',
        expression = 'context.getService().Title()',
    ),
    ComputedField('ServiceUID',
        expression = 'context.getService().UID()',
    ),
    ComputedField('SampleTypeUID',
        expression = 'context.aq_parent.getSample().getSampleType().UID()',
    ),
    ComputedField('SamplePointUID',
        expression = 'context.aq_parent.getSample().getSamplePoint().UID() if context.aq_parent.getSample().getSamplePoint() else None',
    ),
    ComputedField('CategoryUID',
        expression = 'context.getService().getCategoryUID()',
    ),
    ComputedField('CategoryTitle',
        expression = 'context.getService().getCategoryTitle()',
    ),
    ComputedField('PointOfCapture',
        expression = 'context.getService().getPointOfCapture()',
    ),
    ComputedField('DateReceived',
        expression = 'context.aq_parent.getDateReceived()',
    ),
    ComputedField('DateSampled',
        expression = 'context.aq_parent.getSample().getDateSampled()',
    ),
    ComputedField('InstrumentValid',
        expression = 'context.isInstrumentInvalid()'
    ),
),
)


class Analysis(BaseContent):
    implements(IAnalysis)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    def _getCatalogTool(self):
        from bika.lims.catalog import getCatalog
        return getCatalog(self)

    def Title(self):
        """ Return the service title as title.
        Some silliness here, for premature indexing, when the service
        is not yet configured.
        """
        try:
            s = self.getService()
            if s:
                s = s.Title()
            if not s:
                s = ''
        except ArchivistRetrieveError:
            s = ''
        return safe_unicode(s).encode('utf-8')

    def updateDueDate(self):
        # set the max hours allowed

        service = self.getService()
        maxtime = service.getMaxTimeAllowed()
        if not maxtime:
            maxtime = {'days': 0, 'hours': 0, 'minutes': 0}
        self.setMaxTimeAllowed(maxtime)
        # set the due date
        # default to old calc in case no calendars
        max_days = float(maxtime.get('days', 0)) + \
                 (
                     (float(maxtime.get('hours', 0)) * 3600 +
                      float(maxtime.get('minutes', 0)) * 60)
                     / 86400
                 )
        part = self.getSamplePartition()
        if part:
            starttime = part.getDateReceived()
            if starttime:
                duetime = starttime + max_days
            else:
                duetime = ''
            self.setDueDate(duetime)

    def getUncertainty(self, result=None):
        """ Calls self.Service.getUncertainty with either the provided
            result value or self.Result
        """
        return self.getService().getUncertainty(result and result or self.getResult())

    def getDependents(self):
        """ Return a list of analyses who depend on us
            to calculate their result
        """
        rc = getToolByName(self, REFERENCE_CATALOG)
        dependents = []
        service = self.getService()
        ar = self.aq_parent
        for sibling in ar.getAnalyses(full_objects=True):
            if sibling == self:
                continue
            service = rc.lookupObject(sibling.getServiceUID())
            calculation = service.getCalculation()
            if not calculation:
                continue
            depservices = calculation.getDependentServices()
            dep_keywords = [x.getKeyword() for x in depservices]
            if self.getService().getKeyword() in dep_keywords:
                dependents.append(sibling)
        return dependents

    def getDependencies(self):
        """ Return a list of analyses who we depend on
            to calculate our result.
        """
        siblings = self.aq_parent.getAnalyses(full_objects=True)
        calculation = self.getService().getCalculation()
        if not calculation:
            return []
        dep_services = [d.UID() for d in calculation.getDependentServices()]
        dep_analyses = [a for a in siblings if a.getServiceUID() in dep_services]
        return dep_analyses

    def setResult(self, value, **kw):
        # Always update ResultCapture date when this field is modified
        self.setResultCaptureDate(DateTime())
        self.getField('Result').set(self, value, **kw)

    def getSample(self):
        return self.aq_parent.getSample()

    def getAnalysisSpecs(self, specification=None):
        """ Retrieves the analysis specs to be applied to this analysis.
            Allowed values for specification= 'client', 'lab', None
            If specification is None, client specification gets priority from
            lab specification.
            If no specification available for this analysis, returns None
        """
        sampletype = self.getSample().getSampleType()
        sampletype_uid = sampletype and sampletype.UID() or ''
        bsc = getToolByName(self, 'bika_setup_catalog')

        # retrieves the desired specs if None specs defined
        if not specification:
            proxies = bsc(portal_type='AnalysisSpec',
                          getClientUID=self.getClientUID(),
                          getSampleTypeUID=sampletype_uid)

            if len(proxies) == 0:
                # No client specs available, retrieve lab specs
                labspecsuid = self.bika_setup.bika_analysisspecs.UID()
                proxies = bsc(portal_type='AnalysisSpec',
                              getSampleTypeUID=sampletype_uid,
                              getClientUID=labspecsuid)
        else:
            specuid = specification == "client" and self.getClientUID() or \
                    self.bika_setup.bika_analysisspecs.UID()
            proxies = bsc(portal_type='AnalysisSpec',
                              getSampleTypeUID=sampletype_uid,
                              getClientUID=specuid)

        return (proxies and len(proxies) > 0) and proxies[0].getObject() or None

    def calculateResult(self, override=False, cascade=False):
        """ Calculates the result for the current analysis if it depends of
            other analysis/interim fields. Otherwise, do nothing
        """

        if self.getResult() and override == False:
            return False

        calculation = self.getService().getCalculation()
        if not calculation:
            return False

        mapping = {}

        # Add interims to mapping
        for interimdata in self.getInterimFields():
            for i in interimdata:
                try:
                    ivalue = float(i['value'])
                    mapping[i['keyword']] = ivalue
                except:
                    # Interim not float, abort
                    return False

        # Add calculation's hidden interim fields to mapping
        for field in calculation.getInterimFields():
            if field['keyword'] not in mapping.keys():
                if field.get('hidden', False):
                    try:
                        ivalue = float(field['value'])
                        mapping[field['keyword']] = ivalue
                    except:
                        return False

        # Add Analysis Service interim defaults to mapping
        service = self.getService()
        for field in service.getInterimFields():
            if field['keyword'] not in mapping.keys():
                if field.get('hidden', False):
                    try:
                        ivalue = float(field['value'])
                        mapping[field['keyword']] = ivalue
                    except:
                        return False

        # Add dependencies results to mapping
        dependencies = self.getDependencies()
        for dependency in dependencies:
            result = dependency.getResult()
            if not result:
                # Dependency without results found
                if cascade:
                    # Try to calculate the dependency result
                    dependency.calculateResult(override, cascade)
                    result = dependency.getResult()
                    if result:
                        try:
                            result = float(str(result))
                            mapping[dependency.getKeyword()] = result
                        except:
                            return False
                else:
                    return False
            else:
                # Result must be float
                try:
                    result = float(str(result))
                    mapping[dependency.getKeyword()] = result
                except:
                    return False

        # Calculate
        formula = calculation.getFormula()
        formula = formula.replace('[', '%(').replace(']', ')f')
        try:
            formula = eval("'%s'%%mapping" % formula,
                               {"__builtins__": None,
                                'math': math,
                                'context': self},
                               {'mapping': mapping})
            result = eval(formula)
        except TypeError:
            self.setResult("NA")
            return True
        except ZeroDivisionError:
            self.setResult('0/0')
            return True
        except KeyError as e:
            self.setResult("NA")
            return True

        precision = service.getPrecision()
        result = (precision and result) \
            and str("%%.%sf" % precision) % result \
            or result
        self.setResult(result)
        return True


    def get_default_specification(self):
        bsc = getToolByName(self, "bika_setup_catalog")
        spec = None
        sampletype = self.getSample().getSampleType()
        keyword = self.getKeyword()
        client_folder_uid = self.aq_parent.aq_parent.UID()
        client_specs = bsc(
            portal_type="AnalysisSpec",
            getSampleTypeUID=sampletype.UID(),
            getClientUID=client_folder_uid
        )
        for client_spec in client_specs:
            rr = client_spec.getObject().getResultsRange()
            kw_list = [r for r in rr if r['keyword'] == keyword]
            if kw_list:
                    spec = kw_list[0]
            break
        if not spec:
            lab_folder_uid = self.bika_setup.bika_analysisspecs.UID()
            lab_specs = bsc(
                portal_type="AnalysisSpec",
                getSampleTypeUID=sampletype.UID(),
                getClientUID=lab_folder_uid
            )
            for lab_spec in lab_specs:
                rr = lab_spec.getObject().getResultsRange()
                kw_list = [r for r in rr if r['keyword'] == keyword]
                if kw_list:
                    spec = kw_list[0]
                    break
        if not spec:
            return {"min": 0, "max": 0, "error": 0}
        return spec

    def guard_unassign_transition(self):
        """ Check permission against parent worksheet
        """
        wf = getToolByName(self, 'portal_workflow')
        mtool = getToolByName(self, 'portal_membership')
        ws = self.getBackReferences('WorksheetAnalysis')
        if not ws:
            return False
        ws = ws[0]
        if wf.getInfoFor(ws, 'cancellation_state', '') == "cancelled":
            return False
        if mtool.checkPermission(Unassign, ws):
            return True
        return False

    def guard_assign_transition(self):
        """
        """
        return True

    def getPriority(self):
        """ get priority from AR
        """
        # this analysis could be in a worksheet or instrument, careful
        return self.aq_parent.getPriority() \
            if hasattr(self.aq_parent, 'getPriority') else None

    def getPrice(self):
        price = self.getService().getPrice()
        priority = self.getPriority()
        if priority and priority.getPricePremium() > 0:
            price = Decimal(price) + (
                      Decimal(price) * Decimal(priority.getPricePremium()) \
                      / 100)
        return price

    def getVATAmount(self):
        vat = self.getService().getVAT()
        price = self.getPrice()
        return float(price) * float(vat) / 100

    def getTotalPrice(self):
        return float(self.getPrice()) + float(self.getVATAmount())

    def isInstrumentValid(self):
        """ Checks if the instrument selected for this analysis service
            is valid. Returns false if an out-of-date or uncalibrated
            instrument is assigned. Returns true if the Analysis has
            no instrument assigned or is valid.
        """
        # TODO : Remove when analysis - instrument being assigned directly
        if not self.getInstrument():
            instr = self.getService().getInstrument() \
                    if self.getService().getInstrumentEntryOfResults() \
                    else None
            if instr:
                self.setInstrument(instr)
        # ---8<--------

        return self.getInstrument().isValid() \
                if self.getInstrument() else True

    def isInstrumentAllowed(self, instrument):
        """ Checks if the specified instrument can be set for this
            analysis, according to the Method and Analysis Service.
            If the Analysis Service hasn't set 'Allows instrument entry'
            of results, returns always False. Otherwise, checks if the
            method assigned is supported by the instrument specified.
            Returns false, If the analysis hasn't any method assigned.
            NP: The methods allowed for selection are defined at
            Analysis Service level.
            instrument param can be either an uid or an object
        """
        if isinstance(instrument, str):
            uid = instrument
        else:
            uid = instrument.UID()

        service = self.getService()
        if service.getInstrumentEntryOfResults() == False:
            return False

        if not self.getMethod():
            return False

        method = self.getMethod()
        return uid in method.getInstrumentUIDs()

    def isMethodAllowed(self, method):
        """ Checks if the analysis can follow the method specified.
            Looks for manually selected methods when AllowManualEntry
            is set and instruments methods when AllowInstrumentResultsEntry
            is set.
            method param can be either an uid or an object
        """
        if isinstance(method, str):
            uid = method
        else:
            uid = method.UID()

        service = self.getService()
        if service.getManualEntryOfResults() == True \
            and uid in service.getRawMethods():
            return True

        if service.getInstrumentEntryOfResults() == True:
            for ins in service.getInstruments():
                if uid == ins.getRawMethod():
                    return True

        return False

    def getFormattedResult(self):
        """Formatted result:
        1. Print ResultText of matching ResultOptions
        2. If the result is not floatable, return it without being formatted
        3. If the analysis specs has hidemin or hidemax enabled and the
           result is out of range, render result as '<min' or '>max'
        4. If the result is floatable, render it to the correct precision
        """
        result = self.getResult()
        service = self.getService()
        choices = service.getResultOptions()

        # 1. Print ResultText of mathching ResulOptions
        match = [x['ResultText'] for x in choices
                 if str(x['ResultValue']) == str(result)]
        if match:
            return match[0]

        # 2. If the result is not floatable, return it without being formatted
        try:
            result = float(result)
        except:
            return result

        # 3. If the analysis specs has enabled hidemin or hidemax and the
        #    result is out of range, render result as '<min' or '>max'
        belowmin = False
        abovemax = False
        specs = self.getAnalysisSpecs()
        specs = specs.getResultsRangeDict() if specs is not None else {}
        specs = specs.get(self.getKeyword(), {})
        hidemin = specs.get('hidemin', '')
        hidemax = specs.get('hidemax', '')
        try:
            belowmin = hidemin and result < float(hidemin) or False
        except:
            belowmin = False
            pass
        try:
            abovemax = hidemax and result > float(hidemax) or False
        except:
            abovemax = False
            pass

        # 3.1. If result is below min and hidemin enabled, return '<min'
        if belowmin:
            return '< %s' % hidemin

        # 3.2. If result is above max and hidemax enabled, return '>max'
        if abovemax:
            return '> %s' % hidemax

        # 4. If the result is floatable, render it to the correct precision
        precision = service.getPrecision()
        if not precision:
            precision = ''
        return str("%%.%sf" % precision) % result

atapi.registerType(Analysis, PROJECTNAME)
