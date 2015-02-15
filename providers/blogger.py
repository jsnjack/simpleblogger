#!/usr/bin/python2.7

'''
Simple Blogger module for communication with GOOGLE
'''

import atom
import gdata
import gdata.photos.service
import gdata.media
import gdata.geo
from gdata import service

blogger_service = ''


class BloggerProvider():
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def _login(self):
        """
        Log in service
        """
        blogger_service = service.GDataService(self.username, self.password)
        blogger_service.source = 'jsn-simpleblogger'
        blogger_service.service = 'blogger'
        blogger_service.account_type = 'GOOGLE'
        blogger_service.server = 'www.blogger.com'
        try:
            blogger_service.ProgrammaticLogin()
        except service.BadAuthentication:
            result = {'error': 'Incorrect username or password'}
        except service.CaptchaRequired:
            result = {'error': 'Google asks you to verify your account with captcha. Please do it in your browser and get back to Simple Blogger'}
        else:
            result = {'success': 'Loged in'}
        return result, blogger_service

    def send_post(self, blogid, post_title, post_text, labels):
        """
        Send post to the service
        """
        result, blogger_service = self._login()
        if 'success' in result:
            try:
                #create a post
                entry = gdata.GDataEntry()
                entry.title = atom.Title('xhtml', post_title)
                entry.content = atom.Content(content_type='html', text=post_text)
                #Get selected labels
                tags = labels
                for tag in tags:
                    label = atom.Category(term=tag,
                                          scheme="http://www.blogger.com/atom/ns#")
                    entry.category.append(label)
                blogger_service.Post(entry, '/feeds/%s/posts/default' % blogid)
                result = u'Posted.'
            except:
                result = u'Error'
        else:
            result = result['error']
        return result

    def get_blogs(self):
        """
        Returns list with recived blogs
        """
        result, blogger_service = self._login()
        if 'error' in result:
            # if blogger_service is empty return error description
            return {
                "status": "error",
                "blogs": [],
                "error": result["error"]
            }
        query = service.Query()
        query.feed = '/feeds/default/blogs'
        feed = blogger_service.Get(query.ToUri())
        blogs = []
        for item in feed.entry:
            blogs.append({
                "name": unicode(item.title.text, "utf-8"),
                "id": item.GetSelfLink().href.split("/")[-1],
                "username": self.username,
                "password": self.password,
                "link": item.link[1].href,
                "tags": [unicode(tag.term, 'utf8') for tag in item.category],
                "provider": "blogger"
            })
        return {
            "status": "ok",
            "blogs": blogs
        }

    def login_image(self):
        picasa_client = gdata.photos.service.PhotosService()
        picasa_client.email = self.username + '@gmail.com'
        picasa_client.password = self.password
        picasa_client.source = 'jsn-simpleblogger'
        picasa_client.ProgrammaticLogin()
        albums = picasa_client.GetUserFeed(user=self.username)
        return albums, picasa_client

    def upload_photo(self, picasa_client, album_url, image_name, path):
        photo = picasa_client.InsertPhotoSimple(album_url, image_name, image_name,
                                                path)
        return photo
