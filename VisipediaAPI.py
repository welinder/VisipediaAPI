import os
import urllib
import pycurl
import StringIO
import yaml
import zipfile
import glob
from xml.etree import ElementTree

class Response:
    pass

class Connection:
    
    def __init__(self, access_key,
                 url='http://173.203.120.143',
                 verbosity=1):
        # allow the use of a configuration yaml file
        if access_key[-4:] == 'yaml':
            conf = yaml.load(open(access_key))
            access_key = conf['access_key']
            if conf.has_key('url'): url = conf['url']
            if conf.has_key('verbosity'): verbosity = conf['verbosity']
        # set member vars
        self.base_url = url
        self.access_key = access_key
        self.verbosity = verbosity
        self.cookie_file_name = 'cookie.txt'
    
    def http_connect(self, http_type, controller, action,
                     id=None, params={}, files=None):
        """
        Generic function supporting HTTP POST, GET, PUT, DELETE requests.
        """
        url = self.base_url + '/' + controller
        if not action:
            url += '.xml'
        elif id and id > 0:
            url += '/' + action + '/' + str(id) + '.xml'
        else:
            url += '/' + action + '.xml'
        params = wrap_params(params, controller, action)
        return self.http_connect_url(http_type, url, params, files)

    def http_connect_url(self, http_type, url, params={}, files=None):
        if self.access_key:
            params['access_key'] = self.access_key
        args = urllib.urlencode(params)
        res = StringIO.StringIO()
        crl = pycurl.Curl()
        crl.setopt(pycurl.FOLLOWLOCATION, 1)
        crl.setopt(pycurl.COOKIEFILE, self.cookie_file_name)
        crl.setopt(pycurl.COOKIEJAR, self.cookie_file_name)
        crl.setopt(pycurl.CUSTOMREQUEST, http_type)
        if(http_type == "POST" and not files):
            crl.setopt(pycurl.POSTFIELDS, args)
        elif files:
            crl.setopt(pycurl.HTTPPOST, files)
        full_url = url + "?" + args if(http_type != "POST" or files) else url
        crl.setopt(pycurl.URL, full_url)
        crl.setopt(pycurl.WRITEFUNCTION, res.write)
        crl.perform()
        status = crl.getinfo(pycurl.HTTP_CODE)
        crl.close()
        if(status < 200 or status >= 300):
            print "HTTP " + http_type + " " + full_url + \
                  " returned " + str(status) + "\n" + res.getvalue()
            return None
        resp = self.parse_response(res.getvalue())
        if(self.verbosity > 0):
           print "HTTP " + http_type + " " + full_url + \
                 " returned " + str(status) + " (API Status: " + \
                 resp.status + ")"
        resp.params = params
        return resp

    def call(self, controller, action=None, id=None, params={},
             files=None, method="POST"):
        if not action: method = "GET"
        elif(action == 'show' or action == 'list'): method = "GET"
        elif(action == 'update'): method = "PUT"
        elif(action == 'destroy'): method = "DELETE"
            
        return self.http_connect(method, controller, action,
                                 id, params, files)

    def parse_response(self, response):
        assert response, "Response is empty"
        resp = Response()
        resp.status = 'OK'
        resp.xml = response
        resp.content = dict()
        try:
            tree = ElementTree.XML(response)
            if(tree.tag == 'response' and tree[0].tag != 'err'):
                if len(tree)==0:
                    if not tree.attrib.has_key('status'):
                        resp.status = 'ERROR'
                    resp.content = ''
                    return resp
                else:
                    tree = tree[0]
            if(tree[0].tag == 'err'):
                resp.status = 'ERROR'
                for child in tree.getchildren():
                    resp.content[child.tag] = xml2dict(child)
            else:
                resp.content = xml2dict(tree)
        except Exception as ex:
            resp.status = 'ERROR'
            resp.content = ex
        return resp

def xml2dict(element):
    """
    Converts an XML element structure to a Python dict.
    """
    res = dict()
    for (attr, val) in element.items():
        if(attr != 'type'): res[attr] = val

    etype = 'string'
    if element.attrib.has_key('type'): etype = element.attrib['type']
    # parse the node depending on its type
    if(len(element.getchildren())>0):
        if(etype == 'array'):
            res[element.tag] = []
            for child in element.getchildren():
                res[element.tag].append(xml2dict(child))
        else:
            for child in element.getchildren():
                res[child.tag] = xml2dict(child)
    else:
        if(element.text and etype == 'integer'):
            res = int(element.text)
        elif(element.text and etype == 'yaml'):
            res = yaml.load(element.text)
        else:
            res = element.text
    return res

def wrap_params(params, controller, action):
    """
    Wrap parameters appropriately for the API.
    """
    # first value is the wrapper string, the second value is a dict with
    # a list of arguments excluded from wrapping for each action
    wrappers = {
        'annotation_types' : ['annotation_type'],
        'annotation_type_versions' : ['annotation_type_version'],
        'annotation_instances' : ['annotation_instance'],
        'hit_types' : ['hit_type', { 'create' : ['register'] }],
        'hits' : ['hit', { 'create' : ['register'], 
                           'extend' : ['max_assignments_increment',
                                       'expiration_increment_in_seconds']}],
        'searches' : ['search'],
        'search_queries' : ['search_query'],
        'wikipedia_articles' : ['wikipedia_article'],
        'objs' : ['obj', { 'create' : ['obj_id'] }],
        'api_keys' : ['api_key'],
        'qualification_types' : ['qualification_type', 
                                 { 'create' : ['register'] }],
        'worker_qualifications' : ['worker_qualification'],
        'features' : ['feature'],
        'image_features' : ['image_feature'],
    }
    if action and wrappers.has_key(controller):
        wrapper = wrappers[controller][0]
        if len(wrappers[controller])>1 and \
           wrappers[controller][1].has_key(action):
            ignore_list = wrappers[controller][1][action]
        else:
            ignore_list = []
        newparams = {}
        for (key, val) in params.iteritems():
            if key in ignore_list:
                newparams[key] = val
            else:
                newparams[wrapper + '[' + str(key) + ']'] = val
        return newparams
    else:
        return params

def file_field(fname):
    """
    Use to attach a file to an API request.
    """
    return (pycurl.FORM_FILE, fname)

def qual_field(id, val, comparator):
    """
    Create a qualification requirement for a HIT.
    
    COMPARATORS (use the abbreviation):
    gt     -> 'GreaterThan'
    lt     -> 'LessThan'
    gte    -> 'GreaterThanOrEqualTo'
    lte    -> 'LessThanOrEqualTo'
    eql    -> 'EqualTo'
    not    -> 'NotEqualTo'
    exists -> 'Exists'

    FIXED QUALIFICATION IDS:
    000000000000000000L0 -> approval rate
    00000000000000000000 -> submission rate
    00000000000000000070 -> abandoned rate
    000000000000000000E0 -> return rate
    000000000000000000S0 -> rejection rate
    00000000000000000040 -> hits approved
    00000000000000000060 -> adult
    00000000000000000071 -> country

    For more info about qualifications, see:
    http://docs.amazonwebservices.com/AWSMechanicalTurkRequester/2008-04-01/ApiReference_QualificationRequirementDataStructureArticle.html
    
    You can see your account qualifications at:
    https://www.mturk.com/mturk/findquals?requestable=false&earned=true
    """
    return { "qualification_id" : id, "comparator" : comparator, "value" : val }

def yaml_field(obj):
    """
    Use to attach a the object as a YAML serialized string.
    """
    return "---\n" + yaml.dump(obj)

def folder_field(folder_name):
    """
    Use this to attach a folder onto an HTTP request.  
    
    The folder contents are zipped up in a .zip file.  Excludes '.svn' 
    folders and files ending with '~'.
    
    A temporary file called 'tmp.zip' is created in the current directory.
    """
    fname = 'tmp.zip'
    archive = zipfile.ZipFile(fname, 'w', compression=zipfile.ZIP_DEFLATED)
    root_len = len(os.path.abspath(folder_name))
    folder_helper(folder_name, archive, root_len)
    archive.close()
    return file_field(fname)

def folder_helper(folder_name, archive, root_len):
    for root, dirs, files in os.walk(folder_name):
        archive_root = os.path.abspath(root)[root_len:]
        for f in files:
            fullpath = os.path.join(root,f)
            archive_name = os.path.join(archive_root, f)
            if not ".svn" in fullpath and not fullpath.endswith("~"):
                archive.write(fullpath, archive_name, zipfile.ZIP_DEFLATED)
        for d in dirs:
            folder_helper(os.path.join(folder_name, d), archive, root_len)