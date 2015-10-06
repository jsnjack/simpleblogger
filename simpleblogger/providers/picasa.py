import threading
from gdata.photos.service import PhotosService
from gi.repository import Gtk

from providers.google import load_credentials, get_connection


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
        credentials = load_credentials(self.blog["email"])
        # Update access token
        if credentials.access_token_expired:
            get_connection(credentials)
        # Login to Picasa
        client = PhotosService(
            source="simpleblogger",
            email=self.blog["email"],
            additional_headers={'Authorization': 'Bearer %s' % credentials.access_token}
        )
        albums = client.GetUserFeed(user=self.blog["email"])

        # Finding album and post photo
        for item in albums.entry:
            if self.blog["name"] == unicode(item.title.text, 'utf-8'):
                album_url = '/data/feed/api/user/' + self.blog["email"]
                album_url = album_url + '/albumid/'
                album_url = album_url + item.gphoto_id.text
                image_name = self.filename.split("/")[-1]
                photo = client.InsertPhotoSimple(
                    album_url,
                    image_name,
                    image_name,
                    self.filename)
                self.dialog.uploaded_image_link = photo.content.src
                self.dialog.emit("response", Gtk.ResponseType.OK)

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()
