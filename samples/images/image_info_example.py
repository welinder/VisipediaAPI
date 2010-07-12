import sys
sys.path.append("../../")
import VisipediaAPI as vis

# set up connection
vc = vis.Connection('../../config.yaml')

# get information about image with ID=1000 (including Flickr meta info)
resp = vc.call('images', 'show', id=1000, params={'show_meta' : 1})

# to create a new image, you just call the create function
# NOTE the name of the field, 'image[image]', this is due to legacy code
# and will be changed in the future, so please make it easy to switch this
# in your code if you upgrade to a new version of these bindings
FILENAME = 'solvay_conference_1927.jpg'
resp = vc.call('images', 'create', 
               files=[('image[image]', vis.file_field(FILENAME))])
# you can get the info about the file from:
img_id = resp.content['id'] # Saved as id=174845 already...
resp = vc.call('images', 'show', id=img_id)