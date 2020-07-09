from geojson import Point, Feature, FeatureCollection, dump
import tempfile

def to_geojson(linefeature):

    tmp_file=tempfile.mkstemp(suffix='.geojson')
    features = []
    features.append(Feature(linefeature))
    feature_collection=FeatureCollection(features)
    with open(tmp_file[1], 'w') as f:
        dump(feature_collection, f)
        
    return tmp_file[1]