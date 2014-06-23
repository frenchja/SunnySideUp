from flask import render_template, redirect, request, send_file, make_response, session
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from app import app, host, port, user, passwd, db
from app.helpers.database import con_db
from forms import EditForm
import Image
from StringIO import StringIO
import matplotlib.pyplot as plt
from math import sqrt

# Google Maps Stuff
from pygeocoder import Geocoder
import urllib
import numpy as np
from scipy import ndimage
from skimage import filter, io, measure, data
import matplotlib.patches as mpatches
from skimage.filter import threshold_otsu
from skimage.segmentation import clear_border
from skimage.morphology import label, closing, square
from skimage.measure import regionprops
from skimage.color import label2rgb
from sqlalchemy import *

def getRegions():
    """Geocode address and retreive image centered
    around lat/long"""
    address = request.args.get('address')
    results = Geocoder.geocode(address)
    lat, lng = results[0].coordinates
    zip_code = results[0].postal_code

    map_url = 'https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&size=640x640&zoom=19&sensor=false&maptype=roadmap&&style=visibility:simplified|gamma:0.1'
    request_url = map_url.format(lat, lng)
    req = urllib.urlopen(request_url)
    img = io.imread(req.geturl(),flatten=True)
    labels, numobjects = ndimage.label(img)
    image = filter.canny(img, sigma=3)
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

def distanceRegion():
    regions = getRegions()
    dist = math.sqrt( ( x1-x2 )**2 + ( y1-y2 )**2 )
    return(dist)

def getRate(zip_code):
    engine = create_engine('mysql+pymysql://root@localhost/sustainable?charset=utf8&use_unicode=0', pool_recycle=3600)
    connection = engine.connect()
    sql_command = "SELECT zip, resrate FROM utilities WHERE zip = '{0}'".format(zip_code)
    result = engine.execute(sql_command)
    row = result.fetchone()
    return(row['resrate'])
    result.close()

def getUsage(zip_code):
    engine = create_engine('mysql+pymysql://root@localhost/sustainable?charset=utf8&use_unicode=0', pool_recycle=3600)
    connection = engine.connect()
    sql_command = "SELECT kwh_month FROM consumption WHERE zip = '{0}'".format(zip_code)
    result = engine.execute(sql_command)
    row = result.fetchone()
    try:
        rate = row['kwh_month']
    except TypeError:
        results = Geocoder.geocode(zip_code)
        sql_command = "SELECT kwh_month FROM consumption_state WHERE state = '{0}'".format(results.state)
        result = engine.execute(sql_command)
        row = result.fetchone()
        rate = row['kwh_month']
    return(rate)
    result.close()

# within your view functions:
# con = con_db('127.0.0.1', 3306, user='root', passwd=NULL, db='sustainable')
def getZip(address):
    """Geocode address and retreive image centered
    around lat/long"""
    results = Geocoder.geocode(address)
    return results

def getArea(address):
    """Geocode address and retreive image centered
    around lat/long"""
    address = address
    results = Geocoder.geocode(address)
    lat, lng = results[0].coordinates
    zip_code = results[0].postal_code

    map_url = 'https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&size=640x640&zoom=19&sensor=false&maptype=roadmap&&style=visibility:simplified|gamma:0.1'
    request_url = map_url.format(lat, lng)
    req = urllib.urlopen(request_url)
    img = io.imread(req.geturl(),flatten=True)
    labels, numobjects = ndimage.label(img)
    image = filter.canny(img, sigma=3)
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
    dist = []
    rp = regionprops(label_image)
    rp = [x for x in rp if 100 < x.area <= 900]

    for region in rp:

        # skip small images
        #if region.area < 100:
        #    continue
        dist.append(sqrt( ( 320-region.centroid[0] )**2 + ( 320-region.centroid[1] )**2 ))
        # draw rectangle around segmented coins
        #minr, minc, maxr, maxc = region.bbox
        #rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
        #                      fill=False, edgecolor='red', linewidth=2)
        #ax.add_patch(rect)

    roof_index = dist.index(min(dist))
    minr, minc, maxr, maxc = rp[roof_index].bbox
    rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                          fill=False, edgecolor='red', linewidth=2)
    ax.add_patch(rect)

    img = StringIO()
    fig.savefig(img)
    img.seek(0)
    session['roof_area'] = rp[roof_index].area
    roof_area = (rp[roof_index].area)*12
    return(roof_area)

def getSize(zip_code, usage):
    """Compute costs of solar system for given zip code
    """
    engine = create_engine('mysql+pymysql://root@localhost/sustainable?charset=utf8&use_unicode=0', pool_recycle=3600)
    connection = engine.connect()
    sql_command = "SELECT average_solar FROM solarhours WHERE zip_code = '{0}'".format(zip_code)
    result = engine.execute(sql_command)
    row = result.fetchone()
    solar = float(row['average_solar'])
    age = request.args.get('age')
    watts_day = float(usage)/30.4375
    size = (float(usage)/30.7543)/solar
    #size = float(usage) / (solar * watts_day * 30.4375)
    return(size)

# ROUTING/VIEW FUNCTIONS
@app.route('/', methods = ['GET', 'POST'])
@app.route('/index', methods = ['GET', 'POST'])
def index():
    form = EditForm(csrf_enabled = False)
    if form.validate_on_submit():
        return redirect('/solar')
    # Renders index.html.
    return render_template('index.html',
        form = form)

@app.route('/plot.png')
def getMap():
    """Geocode address and retreive image centered
    around lat/long"""
    address = request.args.get('address')
    results = Geocoder.geocode(address)
    lat, lng = results[0].coordinates
    zip_code = results[0].postal_code

    map_url = 'https://maps.googleapis.com/maps/api/staticmap?center={0},{1}&size=640x640&zoom=19&sensor=false&maptype=roadmap&&style=visibility:simplified|gamma:0.1'
    request_url = map_url.format(lat, lng)
    req = urllib.urlopen(request_url)
    img = io.imread(req.geturl(),flatten=True)
    labels, numobjects = ndimage.label(img)
    image = filter.canny(img, sigma=3)
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
    dist = []
    rp = regionprops(label_image)
    rp = [x for x in rp if 100 < x.area <= 900]
    for region in rp:

        # skip small images
        #if region.area < 100:
        #    continue
        dist.append(sqrt( ( 320-region.centroid[0] )**2 + ( 320-region.centroid[1] )**2 ))
        # draw rectangle around segmented coins
        #minr, minc, maxr, maxc = region.bbox
        #rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
        #                      fill=False, edgecolor='red', linewidth=2)
        #ax.add_patch(rect)

    roof_index = dist.index(min(dist))
    minr, minc, maxr, maxc = rp[roof_index].bbox
    rect = mpatches.Rectangle((minc, minr), maxc - minc, maxr - minr,
                          fill=False, edgecolor='red', linewidth=2)
    ax.add_patch(rect)

    img = StringIO()
    fig.savefig(img)
    img.seek(0)
    session['roof_area'] = rp[roof_index].area
    return send_file(img, mimetype='image/png')

@app.route('/solar', methods=['POST'])
def solar():
    results = getZip(request.form['address'])
    lat, lng = results[0].coordinates
    zip_code = results[0].postal_code
    rate = float(getRate(zip_code)) / 1000
    usage = float(getUsage(zip_code))
    address = request.form['address']
    area = getArea(address)
    size = getSize(zip_code, usage)
    age = float(request.form['age'])
    worth = (usage * rate * age)-((size * 111.1111)*4.8*9)
    return render_template('solar.html', address=address,
        zip_code = zip_code, lat = lat, lng = lng,
        rate = rate, usage = usage, area = area, size = size, age = age,
        worth = worth)

@app.route('/home')
def home():
    # Renders home.html.
    return render_template('home.html')

@app.route('/slides')
def about():
    # Renders slides.html.
    return render_template('slides.html')

@app.route('/author')
def contact():
    # Renders author.html.
    return render_template('author.html')

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500
