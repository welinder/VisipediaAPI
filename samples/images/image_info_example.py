import sys
sys.path.append("../../")
import VisipediaAPI as vis

# set up connection
vc = vis.Connection('../../config.yaml')

# get information about image with ID=1000 (including Flickr meta info)
resp = vc.call('images', 'show', id=1000, params={'show_meta' : 1})

