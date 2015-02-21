import threading
from gi.repository import Gtk

from providers.blogger import BloggerProvider


class PicasaImageThreading(threading.Thread):
    """
    Uploads image to Picasa server
    """
    def __init__(self, blog, filename, dialog):
        super(PicasaImageThreading, self).__init__()
        self.blog = blog
        self.filename = filename
        self.dialog = dialog
        self._stop = threading.Event()

    def run(self):
        # Login to Picasa
        provider = BloggerProvider(self.blog["username"], self.blog["password"])
        albums, client = provider.login_picasa()

        # Finding album and post photo
        for item in albums.entry:
            if self.blog["name"] == unicode(item.title.text, 'utf-8'):
                album_url = '/data/feed/api/user/' + self.blog["username"]
                album_url = album_url + '/albumid/'
                album_url = album_url + item.gphoto_id.text
                image_name = self.filename.split("/")[-1]
                photo = provider.upload_photo(client, album_url, image_name, self.filename)
                self.dialog.uploaded_image_link = photo.content.src
                self.dialog.emit("response", Gtk.ResponseType.OK)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
