#!env/python3
# coding: utf-8
import ipdb


import config as C
from core.framework.common import *
from core.model import *
from core.managers import *










# =====================================================================================================================
# CORE MAIN OBJECT
# =====================================================================================================================
def notify_all_print(self, data):
    """
        Default delegate used by the core for notification.
    """
    print(str(data))


class Core:
    def __init__(self):
        # Pipeline and job management (Pirus part)
        self.files = FileManager()
        self.pipelines = PipelineManager()
        self.jobs = JobManager()
        self.container_managers = {}
        self.container_managers["lxd"] = LxdManager()
        # Annotations and variant management (Annso part)
        self.analyses = AnalysisManager()
        self.samples = SampleManager()
        self.annotations = AnnotationManager()
        self.filters = FilterEngine()
        self.phenotypes = PhenotypeManager()
        # Regovar Part (User, project, SLI management)
        self.users = UserManager()
        self.projects = ProjectManager()
        self.events = EventManager()
        self.subjects = SubjectManager()
        self.search = SearchManager()
        self.admin = AdminManager()


        # method handler to notify all
        # according to api that will be pluged on the core, this method should be overriden 
        # to really do a notification. (See how api_rest override this method)
        self.notify_all = notify_all_print




    def user_authentication(self, login, pwd):
        """
            Return the User if credential match.
        """
        return User.from_credential(login, pwd);







# =====================================================================================================================
# INIT OBJECTS
# =====================================================================================================================

core = Core()
log('Regovar core initialised. Server ready !')

