#!env/python3
# coding: utf-8
import os
import json

from core.framework.common import *
from core.framework.postgresql import *




ANALYSIS_DEFAULT_FILTER = ["AND", []]



def analysis_init(self, loading_depth=0):
    """
        Init properties of an analysis :
            - id                : int           : the unique id of the analysis in the database
            - project_id        : int           : the id of the project that owns this analysis
            - name              : str           : the name of the analysis
            - comment           : str           : an optional comment
            - template_id       : int           : null or refer to the template that have been used to init the analysis settings
            - fields            : [str]         : The list of field's id to display
            - filter            : dict          : The last current filter to applied
            - order             : [str]         : The list of field's id to used to order result
            - selection         : [str]         : The list of ids of selected variants
            - create_date       : datetime      : The date when the analysis have been created
            - update_date       : datetime      : The last time that the analysis have been updated
            - total_variants    : int           : The total number of variant in this analysis
            - reference_id      : int           : Refer to the id of the reference used for this analysis
            - computing_progress: float         : Used when the working table is computed to store the current progress
            - status            : enum          : The status of the analysis : 'empty', 'computing', 'ready', 'error'
            - filters_ids       : [int]         : The list of ids of filters saved for this analysis
            - samples_ids       : [int]         : The list of ids of samples used for analysis
            - attributes        : [Attribute]   : The list of attributes defined for this analysis
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - project           : [Job]         : The list of Job owns by the project
            - template          : [Analysis]    : The list of Analysis owns by the project
            - samples           : [File]        : The list of File owns by the project
            - filters           : Project       : The parent Project if defined
    """
    from core.model.attribute import Attribute
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    if not self.filter: self.filter = ANALYSIS_DEFAULT_FILTER
    self.filters_ids = self.get_filters_ids()
    self.samples_ids = AnalysisSample.get_samples_ids(self.id)
    self.attributes = Attribute.get_attributes(self.id)
    self.load_depth(loading_depth)
            

def analysis_load_depth(self, loading_depth):
    from core.model.project import Project
    from core.model.template import Template
    self.project = None
    self.template = None
    self.samples = []
    self.filters = []
    if loading_depth > 0:
        try:
            self.project = Project.from_id(self.project_id, self.loading_depth-1)
            self.template = Template.from_id(self.template_id, self.loading_depth-1)
            self.samples = AnalysisSample.get_samples(self.id, self.loading_depth-1)
            self.filters = self.get_filters(self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("Analysis data corrupted (id={}).".format(self.id), "", ex)



def analysis_from_id(analysis_id, loading_depth=0):
    """
        Retrieve analysis with the provided id in the database
    """
    analysis = session().query(Analysis).filter_by(id=analysis_id).first()
    if analysis:
        analysis.init(loading_depth)
    return analysis



def analysis_to_json(self, fields=None):
    """
        export the analysis into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Analysis.public_fields
    for f in fields:
        if f == "create_date" or f == "update_date":
            result.update({f: eval("self." + f + ".isoformat()")})
        elif f in ["samples", "filters", "attributes"] and self.loading_depth>0:
            result[f] = [o.to_json() for o in eval("self." + f)]
        elif f in ["project", "template"] and self.loading_depth>0:
            result[f] = eval("self." + f + ".to_json()")
        else:
            try:
                result.update({f: eval("self." + f)})
            except Exception as ex:
                err("Analysis.to_json unable to evaluate the value of the field {}. {}".format(f, str(ex)))
    return result


def analysis_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties (project, template, samples, samples_ids, attributes)
        cannot be updated with this method. However, you can update project_id and template_id.
        To update sample and Attributes you must used dedicated models object : AnalysisSample and Attribute
    """
    try:
        if "name"               in data.keys(): self.name               = data['name']
        if "project_id"         in data.keys(): self.project_id         = data['project_id']
        if "template_id"        in data.keys(): self.template_id        = data['template_id']
        if "comment"            in data.keys(): self.comment            = data['comment']
        if "create_date"        in data.keys(): self.create_date        = data['create_date']
        if "update_date"        in data.keys(): self.update_date        = data['update_date']
        if "fields"             in data.keys(): self.fields             = data["fields"]
        if "filter"             in data.keys(): self.filter             = data["filter"]
        if "selection"          in data.keys(): self.selection          = data["selection"]
        if "order"              in data.keys(): self.order              = data["order"]
        if "total_variants"     in data.keys(): self.total_variants     = data["total_variants"]
        if "reference_id"       in data.keys(): self.reference_id       = data["reference_id"]
        if "computing_progress" in data.keys(): self.computing_progress = data["computing_progress"]
        if "status"             in data.keys(): self.status             = data["status"]

        if "samples_ids"        in data.keys():
            # Remove old
            for sid in self.samples_ids:
                if sid not in data["samples_ids"]:
                    AnalysisSample.delete(self.id, sid)
            # Add new samples
            for sid in data["samples_ids"]:
                if sid not in self.samples_ids:
                    AnalysisSample.new(self.id, sid)


        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
        self.save()
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def analysis_delete(analysis_id):
    """
        Delete the Analysis with the provided id in the database
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    session().query(Analysis).filter_by(id=analysis_id).delete(synchronize_session=False)


def analysis_new():
    """
        Create a new Analysis and init/synchronise it with the database
    """
    a = Analysis()
    a.fields=[]
    a.filter=ANALYSIS_DEFAULT_FILTER
    a.selection=[]
    a.order=[]
    a.save()
    a.init()
    return a


def analysis_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(Analysis)



def analysis_get_filters_ids(self):
    """
        Return the list of filters saved for the analysis
    """
    result = []
    filters = session().query(Filter).filter_by(analysis_id=self.id).all()
    for f in filters:
        result.append(f.id)
    return result

def analysis_get_filters(self, loading_depth=0):
    """
        Return the list of filters saved in the analysis
    """
    return session().query(Filter).filter_by(analysis_id=self.id).all()


def analysis_get_attributes_ids(self):
    """
        Return the list of attributes defined for the analysis
    """
    result = []
    attributes = session().query(Attribute).filter_by(analysis_id=self.id).all()
    for a in attributes:
        result.append(a.id)
    return result


def analysis_get_attributes(self, loading_depth=0):
    """
        Return the list of filters saved in the analysis
    """
    result = []
    attributes = session().query(Attribute).filter_by(analysis_id=self.id).order_by("name, sample_id").all()
    current_attribute = None
    for a in attributes:
        if current_attribute is None or current_attribute != a.name:
            current_attribute = a.name
            result.append({"name": a.name, "samples_value": {a.sample_id: a.value}})
        else:
            result[-1]["samples_value"][a.sample_id] = a.value


Analysis = Base.classes.analysis
Analysis.public_fields = ["id", "name", "project_id", "template_id", "samples_ids", "samples", "filters_ids", "filters", "attributes", "comment", "create_date", "update_date", "fields", "filter", "selection", "order", "total_variants", "reference_id", "computing_progress", "status"]
Analysis.init = analysis_init
Analysis.load_depth = analysis_load_depth
Analysis.from_id = analysis_from_id
Analysis.to_json = analysis_to_json
Analysis.load = analysis_load
Analysis.save = generic_save
Analysis.delete = analysis_delete
Analysis.new = analysis_new
Analysis.count = analysis_count
Analysis.get_filters_ids = analysis_get_filters_ids
Analysis.get_filters = analysis_get_filters
Analysis.get_attributes = analysis_get_attributes



# =====================================================================================================================
# FILTER
# =====================================================================================================================
def filter_new(analysis_id, name=None, filter=None, total=0):
    f = Filter(analysis_id=analysis_id, file_id=file_id, name=name, filter=filter, total_variants=total)
    f.save()
    return f


def filter_save(self):
    generic_save(self)


Filter = Base.classes.filter
Filter.new = filter_new
Filter.save = filter_save



# =====================================================================================================================
# ANALYSIS SAMPLE
# =====================================================================================================================
AnalysisSample = Base.classes.analysis_sample


def analysissample_get_samples_ids(analysis_id):
    """
        Return the list of samples ids of an analysis
    """
    return [s.sample_id for s in session().query(AnalysisSample).filter_by(analysis_id=analysis_id).all()]


def analysissample_get_analyses_ids(sample_id):
    """
        Return the list of analyses ids where the sample is used
    """
    return [a.analysis_id for a in session().query(AnalysisSample).filter_by(sample_id=sample_id).all()]


def analysissample_get_samples(analysis_id, loading_depth=0):
    """
        Return the list of samples used in an analysis
    """
    from core.model.sample import Sample
    samples_ids = analysissample_get_samples_ids(analysis_id)
    result = []
    if len(samples_ids) > 0:
        samples = session().query(Sample).filter(Sample.id.in_(samples_ids)).all()
        for s in samples:
            s.init(loading_depth)
            result.append(s)
    return result


def analysissample_get_analyses(sample_id, loading_depth=0):
    """
        Return the list of analyses that used the sample
    """
    analyses_ids = analysissample_get_analyses_ids(sample_id)
    if len(analyses_ids) > 0:
        analyses = session().query(Analysis).filter(Analysis.id.in_(analyses_ids)).all()
    for a in analyses:
        a.init(loading_depth)
        result.append(a)
    return result


def analysissample_new(analysis_id, sample_id, nickname=None):
    """
        Create a new sample-file association and save it in the database
    """
    sf = AnalysisSample(sample_id=sample_id, analysis_id=analysis_id, nickname=nickname)
    sf.save()
    return sf


def analysissample_delete(analysis_id, sample_id):
    """
        Delete the link between an analysis and a sample
    """
    # TODO : delete linked filters, AnalysisSample, Attribute, WorkingTable
    session().query(AnalysisSample).filter_by(analysis_id=analysis_id, sample_id=sample_id).delete(synchronize_session=False)


AnalysisSample = Base.classes.analysis_sample
AnalysisSample.get_samples_ids = analysissample_get_samples_ids
AnalysisSample.get_analyses_ids = analysissample_get_analyses_ids
AnalysisSample.get_samples = analysissample_get_samples
AnalysisSample.get_analyses = analysissample_get_analyses
AnalysisSample.save = generic_save
AnalysisSample.new = analysissample_new
AnalysisSample.delete = analysissample_delete



