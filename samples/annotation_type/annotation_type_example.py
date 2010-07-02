import sys
sys.path.append("../../")
import VisipediaAPI as vis

# set up connection
vc = vis.Connection('../../config.yaml')

## create a new annotation type
resp = vc.call('annotation_types', 'create', 
    params={'name' : 'Example Task',
     'description' : 'This task is only used for API testing purposes.'})
annotation_type_id = resp.content['id']

# show it
resp = vc.call('annotation_types', 'show', id=annotation_type_id)

# destroy it
resp = vc.call('annotation_types', 'destroy', id=annotation_type_id)

## create a new annotation type version
# use a dedicated annotation type for testing the other functionality
ID = 4 # don't remove this annotation_type -- it is used for testing...
resp = vc.call('annotation_type_versions', 'create', 
               params={'annotation_type_id' : ID, },
               files=[('code', vis.folder_field('presence_absence'))])
annotation_type_version_id = resp.content['id']

## create an instance for the annotation type
# format the parameters for the instance
prm = vis.yaml_field({"object_name" : 'Foo',
                      "wikipedia_url" : "http://en.wikipedia.org/wiki/Foo",
                      "example_image_urls" : '["http://s3.amazonaws.com/visipedia/images/1001/medium.jpg","http://s3.amazonaws.com/visipedia/images/1002/medium.jpg"]'})
# create the instance
resp = vc.call('annotation_instances', 'create',
               params={'annotation_type_version_id' : annotation_type_version_id,
                       'name' : 'Foo',
                       'parameters' : prm})
annotation_instance_id = resp.content['id']