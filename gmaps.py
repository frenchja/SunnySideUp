#!/usr/bin/env python
# coding: utf-8
# Author: Jason A. French
# Digital Globes
from pygeocoder import Geocoder
import urllib
import numpy as np
from scipy import ndimage
from skimage import filter, io, measure
import matplotlib.patches as mpatches
from skimage import data
from skimage.filter import threshold_otsu
from skimage.segmentation import clear_border
from skimage.morphology import label, closing, square
from skimage.measure import regionprops
from skimage.color import label2rgb


def getMap(address):
    """Geocode address and retreive image centered
    around lat/long"""

    results = Geocoder.geocode(address)
    lat, lng = results[0].coordinates
    zip_code = results[0].postal_code

    map_url = 'https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&size=640x640&zoom=19&sensor=false&maptype=roadmap&&style=visibility:simplified|gamma:0.1'
    request_url = map_url.format(lat, lng)
    req = urllib.urlopen(request_url)
    return(req)

def mapEdge(req):
    """Convert img to bytearray and do edge detection
    on centered building"""
    
    img = io.imread(req.geturl(),flatten=True)
    labels, numobjects = ndimage.label(img)
    edges = filter.canny(img, sigma=3)
    return(edges)
    # plt.imshow(edges, cmap=plt.cm.gray)
    # plt.show()

def roofRegion(edge):
    """Estimate region based on edges of roofRegion
    """
    # apply threshold
    thresh = threshold_otsu(image)
    bw = closing(image > thresh, square(3))

    # remove artifacts connected to image border
    cleared = bw.copy()
    clear_border(cleared)

    # label image regions
    label_image = label(cleared)
    borders = np.logical_xor(bw, cleared)
    label_image[borders] = -1
    image_label_overlay = label2rgb(label_image, image=image)

    fig, ax = plt.subplots(ncols=1, nrows=1, figsize=(6, 6))
    ax.imshow(image_label_overlay)

    for region in regionprops(label_image):

        # skip small images
        if region.area < 100:
            continue

        # draw rectangle around segmented coins
        minr, minc, maxr, maxc = region.bbox
        rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                                  fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(rect)

    plt.show()