import boto
import flask as f
import flask.ext.uploads as fu
import os
import redis
import time
import urlparse
import uuid

import json

app = f.Flask(__name__)
app.debug = os.getenv('APP_DEBUG')

## Redis.
url = urlparse.urlparse(os.environ.get('REDISCLOUD_URL'))
r = redis.Redis(host=url.hostname, port=url.port, password=url.password)

## Flask-Uploads config.
app.config['UPLOADED_IMAGES_DEST'] = 'tmp'
images = fu.UploadSet('images', fu.IMAGES)
fu.configure_uploads(app, (images))

## S3.
S3_BUCKET = os.getenv('S3_BUCKET')
c = boto.connect_s3()
b = c.get_bucket(S3_BUCKET)
k = boto.s3.key.Key(b)

def now():
  return int(time.time())

def img_url(s):
  return 'http://' + S3_BUCKET + '/' + s

@app.route('/', methods=['GET', 'POST'])
def index():
  if f.request.method == 'GET':
    return f.render_template('index.html')
  else:
    ## Process incoming args
    img = f.request.files['image']
    ## Save incoming file to Flask-Uploads collection and local disk.
    localname = str(uuid.uuid4()) + os.path.splitext(img.filename)[1]
    images.save(img, None, localname)
    ## Move file to S3
    k.key = os.path.basename(localname)
    k.set_contents_from_filename(images.path(localname))
    os.remove(images.path(localname))
    ## Store in DB
    key = 'key:' + str(r.incr('key'))
    r.lpush('keys', key)
    r.lpush('images', localname)
    r.hmset(key, {'filename': localname, 'inserted': now()})
    ## Return URL to S3 zipfile
    url = img_url(os.path.basename(images.path(localname)))
    return f.render_template('list.html', url=url)

@app.route('/api/list', methods=['GET'])
def api_list():
   images = r.lrange('images', 0, 9)
   urls = map(img_url, images)
   return json.dumps(urls)

@app.route('/mithril', methods=['GET'])
def list2():
   return f.render_template('mithril.html')

if __name__ == '__main__':
  app.run()
