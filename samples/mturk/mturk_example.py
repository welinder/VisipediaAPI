import sys
sys.path.append("../../")
import VisipediaAPI as vis

# set up connection
vc = vis.Connection('../../config.yaml')

# GLOBALS
ANN_TYPE_ID = 4 # Use the dedicated test type
API_KEY_ID = 2 # Change this to your own key
ANN_INST_ID = 1135 # Change this to your own annotation instance

# To find your API keys, the following will return a list:
resp = vc.call('api_keys')
# then pick the 'id' of the API key you want to use

## create a new hit type
# set up the qualification requirements
qual_reqs = vis.yaml_field(
    [vis.qual_field("00000000000000000071", "US", "eql"),  # US workers only
     vis.qual_field("000000000000000000L0", "95", "gte")]) # >95% appr. rate
# create the hit type on the Visipedia server, but don't register it yet
resp = vc.call('hit_types', 'create', 
                params={'identifier' : 'Example Presence/Absence HIT',
                        'title' : 'Example Test HIT',
                        'description' : 'Test HIT to see if API works.',
                        'keywords' : 'images,labeling,test,example',
                        'reward' : 1,
                        'assignment_duration' : 500,
                        'auto_approval_delay' : 2592000,
                        'annotation_type_id' : ANN_TYPE_ID,
                        'api_key_id' : API_KEY_ID,
                        'sandbox' : 1,
                        'qualification_requirement' : qual_reqs,
                        'register' : 0})
hit_type_id = resp.content['id']
# register the hit (we could have done it directly above...)
resp = vc.call('hit_types', 'register', id=hit_type_id)
# now the hit type has an mturk id: resp.content['mturk-id']

## set up a few example hits
image_ids = [[4005, 4006, 4007, 4008, 4009, 4010],
             [5005, 5006, 5007, 5008, 5009, 5010]]
# set up and register hits
hit_ids = []
for id_set in image_ids:
    image_ids_str = "[" + ",".join([str(id) for id in id_set]) + "]"
    params = vis.yaml_field({ "image_ids" : image_ids_str })
    resp = vc.call('hits', 'create', 
                   params={'hit_type_id' : hit_type_id,
                           'annotation_instance_id' : ANN_INST_ID,
                           'lifetime' : 6000,
                           'max_assignments' : 1,
                           'meta' : '',
                           'parameters' : params,
                           'register' : 1})
    hit_ids.append(resp.content['id'])

# find out more info about your hits calling the show action
for hit_id in hit_ids:
    resp = vc.call('hits', 'show', id=hit_id)
    print str(resp.content)

## check for assignments
for hit_id in hit_ids:
    resp = vc.call('hits', 'get_assignments', id=hit_id)

## download assignment results using 'image_assignments'
resp = vc.call('image_assignments',
               params={ 'hit_type_id' : hit_type_id })

## or download full assignments using 'assigments'
resp = vc.call('assignments', params={'hit_id' : HIT_ID})