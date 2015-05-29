import argparse
import os
import json
import random
from urllib import urlopen
try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO    

from clarifai.client import ClarifaiApi
from flickrapi import FlickrAPI
from PIL import Image, ImageFont, ImageDraw

from settings import CLARIFAI_API_KEY, CLARIFAI_API_SECRET, FLICKR_API_KEY, FLICKR_API_SECRET

LOW_PROB = 0.8
IMG_SIZE = (500, 500)
LOW_BLEND, HIGH_BLEND = (0.25, 0.75)
MARGINS = [20, 50]
TITLE_SIZE = 100
ALBUM_SIZE = 45
TOP_ALBUM = 200

class CoverMaker(object):
    
    def __init__(self, tags, band, album):
        self._tags, self.tags = tags, tags
        self.band = band
        self.album = album
        self.available_fonts = [font for font in os.listdir('./fonts') if font.lower().endswith('ttf')]
        self.flickr = FlickrAPI(FLICKR_API_KEY, FLICKR_API_SECRET)
        self.clarifai = ClarifaiApi(CLARIFAI_API_KEY, CLARIFAI_API_SECRET)

    def make_cover(self):
        # Generate random images
        img1 = self._get_random_photo()
        img2 = self._get_random_photo()
        # Blend images, with a level between 0.25 and 0.75 to make sure both can be seen
        cover = Image.blend(img1, img2, random.uniform(LOW_BLEND, HIGH_BLEND))
        # Add band name and title
        band_position = (random.choice(MARGINS), random.choice(MARGINS))
        band_font = self._get_random_font(TITLE_SIZE)
        ImageDraw.Draw(cover).text(band_position, self.band, font=band_font)
        album_position = (random.choice(MARGINS), TOP_ALBUM+random.choice(MARGINS))
        album_font = self._get_random_font(ALBUM_SIZE)
        ImageDraw.Draw(cover).text(album_position, self.album, font=album_font)
        # Return cover
        return cover
       
    def _get_random_font(self, size):
        return ImageFont.truetype("./fonts/{font}".format(**{
            'font' : random.choice(self.available_fonts)
        }), size)
        
    def _check_with_clarifai(self, url, tag):
        data = self.clarifai.tag_image_urls(url)['results'][0]['result']['tag']
        classes, probs = data['classes'], data['probs']
        tags = [class_ for (i, class_) in enumerate(classes) if probs[i] > LOW_PROB]
        return tag in tags
        
    def _get_random_photo(self, size=IMG_SIZE):
        """
        Get a random photo from Flickr and returns as a PIL image of a given size.
        """
        tag = random.choice(tags)
        data = self.flickr.photos.search(text=tag, per_page='500', content_type=1, sort='relevance', format="json")
        photos = json.loads(data).get('photos').get('photo')
        photo = random.choice(photos)
        url = "https://farm{farm-id}.staticflickr.com/{server-id}/{id}_{secret}.jpg".format(**{
            'farm-id' : photo.get('farm', ''),
            'server-id' : photo.get('server', ''),
            'id' : photo.get('id', ''),
            'secret' : photo.get('secret', ''),
        })
        if self._check_with_clarifai(url, tag):
            self.tags.remove(tag)
            file = StringIO(urlopen(url).read())
            return Image.open(file).resize(size)
        else:
            return self._get_random_photo()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('band', type=str, help='the band name')
    parser.add_argument('album', metavar='album', type=str, help='the album name')
    args = parser.parse_args()
    tags = [
        'horror',
        'fantasy',
        'water',
        'smoke',
        'black and white',
        'history',
        'fire',
        'pattern',
        'sky',
        'scary'
    ]
    c = CoverMaker(tags, args.band, args.album)
    c.make_cover().show()
    
