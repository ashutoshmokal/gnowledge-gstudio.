from django.http import HttpResponseRedirect,HttpResponse
#from django.http import HttpResponse
from django.shortcuts import render_to_response #render  uncomment when to use
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django_mongokit import get_database
import json  

from mongokit import IS
try:
    from bson import ObjectId
except ImportError:  # old pymongo
    from pymongo.objectid import ObjectId

from gnowsys_ndf.settings import GAPPS, MEDIA_ROOT
from gnowsys_ndf.ndf.models import GSystemType, Node
from gnowsys_ndf.ndf.views.methods import create_grelation

db = get_database()
collection = db[Node.collection_name]
GST_BATCH = collection.GSystemType.one({'name': GAPPS[9]})
app = collection.GSystemType.one({'name': GAPPS[9]})

def batch(request, group_id):
    """
   * Renders a list of all 'batches' available within the database.
    """
    ins_objectid  = ObjectId()
    st_student = collection.Node.one({'_type':'GSystemType','name':'Student'})
    if ins_objectid.is_valid(group_id) is False :
        group_ins = collection.Node.find_one({'_type': "Group","name": group_id})
        auth = collection.Node.one({'_type': 'Author', 'name': unicode(request.user.username) })
        if group_ins:
            group_id = str(group_ins._id)
        else :
            auth = collection.Node.one({'_type': 'Author', 'name': unicode(request.user.username) })
            if auth :
                group_id = str(auth._id)
    else :
        pass
    batch_coll = collection.GSystem.find({'member_of': {'$all': [GST_BATCH._id]}, 'group_set': {'$all': [ObjectId(group_id)]}})
    st_student = collection.Node.one({'_type':'GSystemType','name':'Student'})
    student_coll = collection.GSystem.find({'member_of': {'$all': [st_student._id]}, 'group_set': {'$all': [ObjectId(group_id)]}})
    #users_in_group = collection.Node.one({'_id':ObjectId(group_id)}).author_set
    template = "ndf/batch.html"
    variable = RequestContext(request, {'batch_coll': batch_coll,'appId':app._id, 'group_id':group_id, 'groupid':group_id,'title':GST_BATCH.name,'st_batch_id':GST_BATCH._id,'student_count':student_coll.count()})
    return render_to_response(template, variable)

#older methode to create and edit batch
def create_and_edit(request, group_id, _id = None):
    '''
    This method is not in use
    '''
    fc_courses = []
    batch = ""
    batch_count = ""
    course_name = ""
    if request.method == 'POST':
        batch_count = request.POST.get('batch_count','')
    else:
        batch_count = 1
        group = collection.Node.one({"_id":ObjectId(group_id)})
        fc_st = collection.Node.one({'_type':'GSystemType','name':'Foundation Course'})
        rt_has_course = collection.Node.one({'_type':'RelationType', 'name':'has_course'})
        if _id:
            batch = collection.Node.one({'_id':ObjectId(_id)})
        if fc_st:
            fc_courses = collection.Node.find({'member_of': {'$all': [fc_st._id]}})
            
        if rt_has_course and _id:
            course = collection.Triple.one({'relation_type.$id':rt_has_course._id,'right_subject':ObjectId(_id)})
            if course:
                course_name = collection.Node.one({'_id':ObjectId(course.subject)}).name

        template = "ndf/create_batch.html"
        variable = RequestContext(request, {'group_id':group_id, 'appId':app._id, 'groupid':group_id,'title':GST_BATCH.name,'batch_count':batch_count,'st_batch_id':GST_BATCH._id,'fc_courses':fc_courses,'batch':batch,'course_name':course_name})
        return render_to_response(template, variable)

def batch_create_criteria(request, group_id, _id = None):
    st_student = collection.Node.one({'_type':'GSystemType','name':'Student'})
    student_coll = collection.GSystem.find({'member_of': {'$all': [st_student._id]}, 'group_set': {'$all': [ObjectId(group_id)]}})
    template = "ndf/new_batch_criteria.html"
    variable = RequestContext(request, {'group_id':group_id, 'appId':app._id, 'groupid':group_id,'title':GST_BATCH.name,'student_count':student_coll.count()})
    return render_to_response(template, variable)

def new_create_and_edit(request, group_id, _id = None):
    node = ""
    count = ""
    batch_count = 1
    batch = ""
    if request.method == 'POST':
        batch_count = int(request.POST.get('batch_count',''))
    if _id:
        batch = collection.Node.one({'_id':ObjectId(_id)})
    st_student = collection.Node.one({'_type':'GSystemType','name':'Student'})
    student_coll = collection.GSystem.find({'member_of': {'$all': [st_student._id]}, 'group_set': {'$all': [ObjectId(group_id)]}})
    fetch_ATs = ["nussd_course_type"]
    req_ATs = []

    for each in fetch_ATs:
        each = collection.Node.one({'_type': "AttributeType", 'name': each}, {'_type': 1, '_id': 1, 'data_type': 1, 'complex_data_type': 1, 'name': 1, 'altnames': 1})

        if each["data_type"] == "IS()":
            dt = "IS("
            for v in each.complex_data_type:
                dt = dt + "u'" + v + "'" + ", " 
            dt = dt[:(dt.rfind(", "))] + ")"
            each["data_type"] = dt

        each["data_type"] = eval(each["data_type"])
        each["value"] = None
        req_ATs.append(each)

    template = "ndf/new_create_batch.html"
    variable = RequestContext(request, {'group_id':group_id, 'appId':app._id,'ATs': req_ATs, 'groupid':group_id,'title':GST_BATCH.name,'batch_count':xrange(batch_count),'st_batch_id':GST_BATCH._id,'student_count':student_coll.count(),'count':batch_count, 'node':batch})
    return render_to_response(template, variable)

def save(request, group_id):
    '''
    This save method create new  and update existing the batches
    '''
    if request.method == 'POST':
        batch_count = request.POST.get('user_list', '')
        node_id = request.POST.get('node_id', '')
        batch_name = request.POST.get('batch_name', '')
        save_batch(batch_name, user_list, group_id, request, node_id)
        return HttpResponseRedirect('/'+group_id+'/'+'batch')
        
def save_students_for_batches(request, group_id):
    '''
    This save method creates new  and update existing the batches
    '''
    if request.method == 'POST':
        user_list = request.POST.get('user_list', '')
        node_id = request.POST.get('node_id', '')
        batch_name = request.POST.get('batch_name', '')
        print "user_list",json.loads(user_list)
        save_batch(batch_name, json.loads(user_list), group_id, request, node_id)
        return HttpResponse("")


def save_batch(batch_name, user_list, group_id, request, node_id):

    if node_id:
        new_batch = collection.Node.one({'_id':ObjectId(node_id)})
        rt_has_batch_member = collection.Node.one({'_type':'RelationType','name':'has_batch_member'})
        relation_coll = collection.Triple.find({'_type':'GRelation','relation_type.$id':rt_has_batch_member._id,'right_subject':ObjectId(node_id)})
        for each in relation_coll:
            rel = collection.Triple.one({'_id':each._id})
            rel.delete()
    else:
        new_batch = collection.GSystem()
        new_batch.created_by = int(request.user.id)
        new_batch.member_of.append(GST_BATCH._id)
        new_batch.group_set.append(ObjectId(group_id))
    new_batch.name = batch_name
    new_batch.contributors.append(int(request.user.id))
    new_batch.modified_by = int(request.user.id)
    new_batch.save()
    print user_list,"user_list"
    rt_has_batch_member = collection.Node.one({'_type':'RelationType', 'name':'has_batch_member'})
    rt_batch_of_group = collection.Node.one({'_type':'RelationType', 'name':'batch_of_group'})
    for each in user_list:
        create_grelation(new_batch._id,rt_has_batch_member,ObjectId(each))
    create_grelation(new_batch._id,rt_batch_of_group,ObjectId(group_id))
    
   

def detail(request, group_id, _id):
    student_coll = []
    node = collection.Node.one({'_id':ObjectId(_id)})
    rt_has_batch_member = collection.Node.one({'_type':'RelationType','name':'has_batch_member'})
    relation_coll = collection.Triple.find({'_type':'GRelation','relation_type.$id':rt_has_batch_member._id,'relation_type.subject':node._id})
    for each in relation_coll:
        n = collection.Node.one({'_id':ObjectId(each.subject)})
        student_coll.append(n)
    print "student_coll",student_coll
    template = "ndf/batch_detail.html"
    variable = RequestContext(request, {'node':node, 'appId':app._id, 'groupid':group_id, 'group_id': group_id,'title':GST_BATCH.name, 'student_coll':student_coll})
    return render_to_response(template, variable)
