#!env/python3
# coding: utf-8
import os
import json


from core.framework.common import *
from core.framework.postgresql import *





# =====================================================================================================================
# Monitoring log wrapper
# =====================================================================================================================
class MonitoringLog:
    """
        Class to wrap log file and provide usefull related information and method to parse logs
    """
    def __init__(self, path):
        self.path = path
        self.name = os.path.basename(path)
        self.size = os.path.getsize(path)
        self.creation = datetime.datetime.fromtimestamp(os.path.getctime(path))
        self.update = datetime.datetime.fromtimestamp(os.path.getmtime(path))


    def tail(self, lines_number=100):
        """
            Return the N last lines of the log
        """
        try: 
            log_tail = subprocess.check_output(["tail", self.path, "-n", str(lines_number)]).decode()
        except Exception as ex:
            err("Error occured when getting tail of log {}".format(self.path), ex)
            log_tail = "No stdout log of the run."
        return log_tail

        
    def head(self, lines_number=100):
        """
            Return the N first lines of the log
        """
        try: 
            log_head = subprocess.check_output(["head", self.path, "-n", str(lines_number)]).decode()
        except Exception as ex:
            err("Error occured when getting head of log {}".format(self.path), ex)
            log_head = "No stderr log of the run."
        return log_head


    def snip(self, from_line, to_line):
        """
            Return a snippet of the log, from the line N to the line N2
        """
        # TODO
        pass

    def lines_count(self):
        # TODO
        pass





# =====================================================================================================================
# JOB
# =====================================================================================================================
def job_init(self, loading_depth=0, force=False):
    """
        Init properties of a job :
            - id            : int               : the unique id of the job in the database
            - pipeline_id   : int               : refer to the pipeline used for this job
            - name          : str               : the name of the job
            - comment       : str               : user can add free comment about the job
            - config        : dict              : dict with parameter's value set by the user that run this job
            - status        : enum              : status of the job : 'waiting', 'initializing', 'running', 'pause', 'finalizing', 'done', 'canceled', 'error'
            - progress_value: float             : progress of the job from 0 to 1 (1=100%)
            - progress_label: str               : custom label displayed with the progress value
            - inputs_ids    : [int]             : the list of ids of files used as inputs of this job
            - outputs_ids   : [int]             : the list of ids of files generated by the job
            - path          : str               : path on the root directory of the job on the server
            - logs          : [MonitoringLog]   : logs generated by the execution of the job
            - update_date   : datetime          : the last time that the object have been updated
            - create_date   : datetime          : the date when the object have been created
           
        If loading_depth is > 0, Following properties fill be loaded : (Max depth level is 2)
            - pipeline      : Pipeline          : The Pipeline use to create the job
            - inputs        : [File]            : The list of file used as inputs for the job
            - outputs       : [File]            : The list of file generated by the job
    """
    from core.model.file import File
    from core.model.pipeline import Pipeline
    # Avoid recursion infinit loop
    if hasattr(self, "loading_depth")and not force:
        return
    else:
        self.loading_depth = min(2, loading_depth)
    try:
        self.inputs_ids = []
        self.outputs_ids = []
        self.logs = []
        self.inputs = []
        self.outputs = []
        self.pipeline = None 
        
        files = Session().query(JobFile).filter_by(job_id=self.id).all()
        job_logs_path = os.path.join(str(self.path), "logs")
        if os.path.exists(job_logs_path) :
            self.logs = [MonitoringLog(os.path.join(job_logs_path, logname)) for logname in os.listdir(job_logs_path) if os.path.isfile(os.path.join(job_logs_path, logname))]
        for f in files:
            if f.as_input:
                self.inputs_ids.append(f.file_id)
            else:
                self.outputs_ids.append(f.file_id)

        if self.loading_depth > 0:
            self.pipeline = Pipeline.from_id(self.pipeline_id, self.loading_depth-1)
        
            if len(self.inputs_ids) > 0:
                files = Session().query(File).filter(File.id.in_(self.inputs_ids)).all()
                for f in files:
                    f.init(self.loading_depth-1)
                    self.inputs.append(f)
            if len(self.outputs_ids) > 0:
                files = Session().query(File).filter(File.id.in_(self.outputs_ids)).all()
                for f in files:
                    f.init(self.loading_depth-1)
                    self.outputs.append(f)
    except Exception as err:
        raise RegovarException("File data corrupted (id={}).".format(self.id), "", err)




def job_container_name(self):
    "{}{}-{}".format(LXD_CONTAINER_PREFIX, job.pipeline_id, job.id)





def job_from_id(job_id, loading_depth=0):
    """
        Retrieve job with the provided id in the database
    """
    job = Session().query(Job).filter_by(id=job_id).first()
    if job:
        Session().refresh(job)
        job.init(loading_depth)
    return job


def job_from_ids(job_ids, loading_depth=0):
    """
        Retrieve jobs corresponding to the list of provided id
    """
    jobs = []
    if job_ids and len(job_ids) > 0:
        jobs = Session().query(Job).filter(Job.id.in_(job_ids)).all()
        for f in jobs:
            Session().refresh(f)
            f.init(loading_depth)
    return jobs


def job_to_json(self, fields=None, loading_depth=-1):
    """
        Export the job into json format with only requested fields
    """
    result = {}
    if loading_depth < 0:
        loading_depth = self.loading_depth
    if fields is None:
        fields = ["id", "pipeline_id", "config", "create_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "logs", "name", "comment"]
    for f in fields:
        if f in Job.public_fields:
            if f in ["create_date","update_date"] :
                result.update({f: eval("self." + f + ".isoformat()")})
            elif f in ["inputs", "outputs"]:
                result.update({f : [i.to_json(None, loading_depth-1) for i in eval("self." + f)]})
            elif f == "pipeline" and self.loading_depth > 0:
                result.update({"pipeline" : self.pipeline.to_json(None, loading_depth-1)})
            elif f == "logs":
                logs = []
                for l in self.logs:
                    logs.append(l.path)
                result.update({"logs" : logs})
            else :
                result.update({f: eval("self." + f)})
    return result


def job_load(self, data):
    try:
        # Required fields
        if "name" in data.keys(): self.name = check_string(data['name'])
        if "comment" in data.keys(): self.comment = check_string(data['comment'])
        if "pipeline_id" in data.keys(): self.pipeline_id = check_int(data['pipeline_id'])
        if "config" in data.keys(): self.config = data["config"]
        if "create_date" in data.keys(): self.create_date = check_date(data["create_date"])
        if "update_date" in data.keys(): self.update_date = check_date(data["update_date"])
        if "status" in data.keys(): self.status = check_string(data["status"])
        if "progress_value" in data.keys(): self.progress_value = check_float(data["progress_value"])
        if "progress_label" in data.keys(): self.progress_label = check_string(data['progress_label'])
        if "inputs_ids" in data.keys(): self.inputs_ids = data["inputs_ids"]
        if "outputs_ids" in data.keys(): self.outputs_ids = data["outputs_ids"]
        if "path" in data.keys(): self.path = check_string(data["path"])
        self.save()

        # delete old file/job links
        Session().query(JobFile).filter_by(job_id=self.id).delete(synchronize_session=False)
        # create new links
        for fid in self.inputs_ids: JobFile.new(self.id, fid, True)
        for fid in self.outputs_ids: JobFile.new(self.id, fid, False)

        # Reload dynamics properties
        self.init(self.loading_depth, True)
    except KeyError as e:
        raise RegovarException('Invalid input job: missing ' + e.args[0])
    return self


def job_save(self):
    generic_save(self)

    # Todo : save job/files associations
    if hasattr(self, 'inputs') and self.inputs: 
        # clear all associations
        # save new associations
        pass
    if hasattr(self, 'outputs') and self.outputs: 
        # clear all associations
        # save new associations
        pass


def job_delete(job_id):
    """
        Delete the job with the provided id in the database
    """
    Session().query(Job).filter_by(id=job_id).delete(synchronize_session=False)
    Session().query(JobFile).filter_by(job_id=job_id).delete(synchronize_session=False)


def job_new():
    """
        Create a new job and init/synchronise it with the database
    """
    j = Job()
    j.save()
    j.init()
    return j


def job_count():
    """
        Return total of Job entries in database
    """
    return generic_count(Job)


Job = Base.classes.job
Job.public_fields = ["id", "pipeline_id", "pipeline", "config", "create_date", "update_date", "status", "progress_value", "progress_label", "inputs_ids", "outputs_ids", "inputs", "outputs", "path", "logs", "name", "comment"]
Job.init = job_init
Job.from_id = job_from_id
Job.from_ids = job_from_ids
Job.to_json = job_to_json
Job.load = job_load
Job.save = job_save
Job.new = job_new
Job.delete = job_delete
Job.count = job_count








# =====================================================================================================================
# JOBFILE associations
# =====================================================================================================================



def jobfile_get_jobs(file_id, loading_depth=0):
    """
        Return the list of jobs that are using the file (as input and/or output)
    """
    result = jobs = []
    jobs_ids = jobfile_get_jobs_ids(file_id)
    if len(jobs_ids) > 0:
        jobs = Session().query(Job).filter(Job.id.in_(jobs_ids)).all()
    for j in jobs:
        j.init(loading_depth)
        result.append(j)
    return result


def jobfile_get_inputs(job_id, loading_depth=0):
    """
        Return the list of input's files of the job
    """
    result = files = []
    files_ids = jobfile_get_inputs_ids(job_id)
    if len(files) > 0:
        files = Session().query(File).filter(File.id.in_(files_ids)).all()
    for f in files:
        f.init(loading_depth)
        result.append(f)
    return result


def jobfile_get_outputs(job_id, loading_depth=0):
    """
        Return the list of output's files of the job
    """
    result = files = []
    files_ids = jobfile_get_outputs_ids(job_id)
    if len(files) > 0:
        files = Session().query(File).filter(File.id.in_(files_ids)).all()
    for f in files:
        f.init(loading_depth)
        result.append(f)
    return result


def jobfile_get_jobs_ids(file_id):
    """
        Return the list of job's id that are using the file (as input and/or output)
    """
    result = []
    jobs = Session().query(JobFile).filter_by(file_id=file_id).all()
    for j in jobs:
        result.append(j.job_id)
    return result
    

def jobfile_get_inputs_ids(job_id):
    """
        Return the list of file's id that are used as input for the job
    """
    result = []
    files = Session().query(JobFile).filter_by(job_id=job_id, as_input=True).all()
    for f in files:
        result.append(f.file_id)
    return result


def jobfile_get_outputs_ids(job_id):
    """
        Return the list of file's id that are used as output for the job
    """
    result = []
    files = Session().query(JobFile).filter_by(job_id=job_id, as_input=False).all()
    for f in files:
        result.append(f.file_id)
    return result


def jobfile_new(job_id, file_id, as_input=False):
    """
        Create a new job-file association and save it in the database
    """
    jf = JobFile(job_id=job_id, file_id=file_id, as_input=as_input)
    jf.save()
    return jf

JobFile = Base.classes.job_file
JobFile.get_jobs = jobfile_get_jobs
JobFile.get_inputs = jobfile_get_inputs
JobFile.get_outputs = jobfile_get_outputs
JobFile.get_jobs_ids = jobfile_get_jobs_ids
JobFile.get_inputs_ids = jobfile_get_inputs_ids
JobFile.get_outputs_ids = jobfile_get_outputs_ids
JobFile.save = generic_save
JobFile.new = jobfile_new
 
