
import pickle
import numpy as np
import math

def aggregate_to_sample_data(sample, data_list, name='xps',  x_sampling=None):
    if x_sampling is None: 
        x_sampling = np.linspace(0,1000,2000)

    if sample.aggregated_data:
        path = sample.aggregated_data.path
        with open(path, 'rb') as fd:
            data_obj = pickle.load(fd)
            agg_data = data_obj.get(name, None)
    else:        
        path ="/tmp/aggregated_data.pkl"
        data_obj = {}
        agg_data = None

    if agg_data is None:
        x = x_sampling 
        y = np.zeros(len(x))
        agg_data = np.vstack((x,y)).transpose()

    for data in data_list:
        data = data[data[:, 0].argsort()] # sort array by x for np.interp
        xp = data[:,0]; yp = data[:,1];
        y_interp = np.interp(agg_data[:,0], xp, yp,left=0, right=0)
        agg_data[:,1] = agg_data[:,1] +  y_interp

    data_obj[name] = agg_data            
    with open(path, 'wb') as fd:
        pickle.dump(data_obj,fd)
        
    return data_obj, path
        

def GAF_transform(serie):
    """Compute the Gramian Angular Field of an image"""
    
    def tabulate(x, y, f):
      """Return a table of f(x, y). Useful for the Gram-like operations."""
      return np.vectorize(f)(*np.meshgrid(x, y, sparse=True))
    
    def cos_sum(a, b):
      """To work with tabulate."""
      return(math.cos(a+b))
    
    # Min-Max scaling
    min_ = np.amin(serie)
    max_ = np.amax(serie)
    scaled_serie = (2*serie - max_ - min_)/(max_ - min_)

    # Floating point inaccuracy!
    scaled_serie = np.where(scaled_serie >= 1., 1., scaled_serie)
    scaled_serie = np.where(scaled_serie <= -1., -1., scaled_serie)

    # Polar encoding
    phi = np.arccos(scaled_serie)

    # GAF Computation (every term of the matrix)
    gaf = tabulate(phi, phi, cos_sum)

    return(gaf, phi, scaled_serie)



def convert_data_layers_to_img(*layers):
    from PIL import Image
    out_layers = []
    for layer in layers:
        min_gaf = np.amin(np.amin(layer))
        max_gaf = np.amax(np.amax(layer))
        range_gaf = max_gaf - min_gaf
        if range_gaf == 0:
            range_gaf = 1            
        out_layers.append((layer - min_gaf) / range_gaf * 255) 

    rgb_uint8 = np.dstack(out_layers).astype(np.uint8)
    img = Image.fromarray(rgb_uint8)
    return img
    