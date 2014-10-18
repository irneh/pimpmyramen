import boto
import flask as f
import flask.ext.uploads as fu
import os
import redis
import time
import urlparse
import uuid
import wand.image as wi

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

def get_ramens(first, last):
  keys = r.lrange('keys', first, last)
  objects = []
  for key in keys:
    ramen = r.hgetall(key)
    id = key.split(':')[1]
    url = img_url(ramen['filename'])
    description = 'description' in ramen.keys() and ramen['description'] or ''
    objects.append({'id': id, 'url': url, 'description': description})
  return objects

@app.route('/', methods=['GET', 'POST'])
def index():
  if f.request.method == 'GET':
    objects = get_ramens(0, 9)
    return f.render_template('list.html', objects=objects)
  else:
    ## Process incoming args
    img = f.request.files['image']
    desc = f.request.form['description'].strip()
    ## Save incoming file to Flask-Uploads collection and local disk.
    localname = str(uuid.uuid4()) + os.path.splitext(img.filename)[1].lower()
    images.save(img, None, localname)
    ## Resize
    print os.path.splitext(img.filename)[1].lower()
    if os.path.splitext(img.filename)[1].lower() != '.gif':
      wimg = wi.Image(filename=images.path(localname))
      wimg.transform(resize='1024x1024>')
      wimg.save(filename=images.path(localname))
    ## Move file to S3
    k.key = os.path.basename(localname)
    k.set_contents_from_filename(images.path(localname))
    os.remove(images.path(localname))
    ## Store in DB
    key = 'ramen:' + str(r.incr('key'))
    r.lpush('keys', key)
    r.lpush('ramens', localname)
    r.hmset(key, {'filename': localname,
      'description': desc,
      'inserted': now()})
    objects = get_ramens(0, 9)
    return f.render_template('list.html', objects=objects)

@app.route('/list/<int:index>', methods=['GET'])
def list(index):
   first = 0 + (10 * index)
   last = 9 + (10 * index)
   ramens = get_ramens(first, last)
   if ramens:
     return f.render_template('grid.html', objects=ramens)
   else:
     return ""

@app.route('/detail/<index>', methods=['GET'])
def detail(index):
  ramen = r.hgetall('ramen:' + index)
  if ramen:
    ramen['url'] = img_url(ramen['filename'])
    return f.render_template('detail.html', ramen=ramen)
  else:
    return "Not found.", 404

if __name__ == '__main__':
  app.run()
