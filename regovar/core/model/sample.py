#!env/python3
# coding: utf-8
import os


from core.framework.common import *
from core.framework.postgresql import *













def sample_init(self, loading_depth=0):
    """
        If loading_depth is > 0, children objects will be loaded. Max depth level is 2.
        Children objects of a sample are :
            - subject : set with a Subject object if exists. 
            - files  : a list of File associated to this sample
            - analyses : a list of Analysis where this sample is used
            - default_dbuid : list of annotation's databases used in the vcf from where come the sample
        If loading_depth == 0, children objects are not loaded
    """
    from core.model.analysis import Analysis, AnalysisSample
    # With depth loading, sqlalchemy may return several time the same object. Take care to not erase the good depth level)
    if hasattr(self, "loading_depth"):
        self.loading_depth = max(self.loading_depth, min(2, loading_depth))
    else:
        self.loading_depth = min(2, loading_depth)
    
    self.analyses_ids = AnalysisSample.get_analyses_ids(self.id)
    self.load_depth(loading_depth)
            

def sample_load_depth(self, loading_depth):
    from core.model.subject import Subject
    from core.model.file import File
    from core.model.analysis import Analysis, AnalysisSample
    if loading_depth > 0:
        try:
            self.subject = None
            self.files = None
            self.analyses = None
            self.subject = Subject.from_id(self.subject_id, self.loading_depth-1)
            #self.files = SampleFile.get_files(self.id, self.loading_depth-1)
            self.analyses = AnalysisSample.get_analyses(self.id, self.loading_depth-1)
        except Exception as ex:
            raise RegovarException("sample data corrupted (id={}).".format(self.id), "", ex)



def sample_from_id(sample_id, loading_depth=0):
    """
        Retrieve sample with the provided id in the database
    """
    sample = session().query(Sample).filter_by(id=sample_id).first()
    if sample : sample.init(loading_depth)
    return sample



def sample_to_json(self, fields=None):
    """
        export the sample into json format with only requested fields
    """
    result = {}
    if fields is None:
        fields = Sample.public_fields
    for f in fields:
        result.update({f: eval("self." + f)})
    return result


def sample_load(self, data):
    """
        Helper to update several paramters at the same time. Note that dynamics properties like project and template
        cannot be updated with this method. However, you can update project_id and template_id.
    """
    try:
        if "name"              in data.keys(): self.name              = data['name']
        if "subject_id"        in data.keys(): self.subject_id        = data['subject_id']
        if "file_id"           in data.keys(): self.file_id           = data['file_id']
        if "analyses_ids"      in data.keys(): self.analyses_ids      = data['analyses_ids']
        if "comment"           in data.keys(): self.comment           = data['comment']
        if "is_mosaic"         in data.keys(): self.is_mosaic         = data['is_mosaic']
        if "default_dbuid"     in data.keys(): self.default_dbuid     = data['default_dbuid']
        # check to reload dynamics properties
        if self.loading_depth > 0:
            self.load_depth(self.loading_depth)
        self.save()
    except Exception as err:
        raise RegovarException('Invalid input data to load.', "", err)
    return self



def sample_delete(sample_id):
    """
        Delete the sample with the provided id in the database
    """
    # TODO : delete linked filters, sampleSample, Attribute, WorkingTable
    session().query(Sample).filter_by(id=sample_id).delete(synchronize_session=False)


def sample_new():
    """
        Create a new sample and init/synchronise it with the database
    """
    a = Sample()
    a.save()
    a.init()
    return a


def sample_count():
    """
        Return total of Analyses entries in database
    """
    return generic_count(Sample)



Sample = Base.classes.sample
Sample.public_fields = ["id", "name", "comment", "subject_id", "file_id", "analyses_ids", "is_mosaic", "default_dbuid"]
Sample.init = sample_init
Sample.load_depth = sample_load_depth
Sample.from_id = sample_from_id
Sample.to_json = sample_to_json
Sample.load = sample_load
Sample.save = generic_save
Sample.delete = sample_delete
Sample.new = sample_new
Sample.count = sample_count





# =====================================================================================================================
# SAMPLEFILE associations
# =====================================================================================================================
#def samplefile_get_files_ids(sample_id):
    #"""
        #Return the list of files ids of the sample
    #"""
    #result = []
    #files = session().query(SampleFile).filter_by(sample_id=sample_id).all()
    #for f in files:
        #result.append(f.file_id)
    #return result


#def samplefile_get_files(sample_id, loading_depth=0):
    #"""
        #Return the list of input's files of the job
    #"""
    #files_ids = samplefile_get_files_ids(sample_id)
    #if len(files) > 0:
        #files = session().query(File).filter(File.id.in_(files_ids)).all()
    #for f in files:
        #f.init(loading_depth)
        #result.append(f)
    #return result


#def samplefile_new(sample_id, file_id):
    #"""
        #Create a new sample-file association and save it in the database
    #"""
    #sf = SampleFile(sample_id=sample_id, file_id=file_id)
    #sf.save()
    #return sf


#SampleFile = Base.classes.sample_file
#SampleFile.get_files_ids = samplefile_get_files_ids
#SampleFile.get_files = samplefile_get_files
#SampleFile.save = generic_save
#SampleFile.new = samplefile_new










# =====================================================================================================================
# SAMPLE VARIANT
# =====================================================================================================================

class SampleVariant:
    # TODO : create property dynamicaly according to available reference in the database
    _hg19 = Base.classes.sample_variant_hg19
    
    
    def get_sample(self, variant_id, ref_id=2):
        pass
    
    def get_variants_ids(self, sample_id, ref_id=2):
        pass
    
    
    def get_variants(self, sample_id):
        pass
    
    
    def new(self, sample_id, variant_id):
        pass