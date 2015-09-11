simpleblogger2
=============
###What is it?
simpleblogger2 is a blogger.com client written in Python and GTK+ 3 (see [this link](http://sourceforge.net/projects/simpleblogger/) for old version)

###Features list
* HTML syntax highlight
* Uploading images to the hosting service (picasa)
* Drafts
* Add tags to the post
* Code insertion and highlighting (pygments)
* Automatically adds all your blogs from Google account
* Post preview

###Screenshots
![ScreenShot](https://raw.githubusercontent.com/e-shulitsky/simpleblogger/master/screenshots/simpleblogger2.png)

###Dependencies
* gobject-introspection
* pygobject3
* python-pygments
* python-keyring
* google-api-python-client

###How to build RPM file
* Create rpm-tree with command:
```bash
rpmdev-setuptree
```
* Build python package with command:
```bash
python setup.py sdist
```
* Place it into SOURCE folder of rpm tree. Place simpleblogger.spec into SPEC folder of rpm tree
* Build rpm package:
```bash
rpmbuild -v -bs --clean SPECS/simpleblogger.spec
```

###Development
Simpleblogger creates `.simpleblogger` folder in your home directory to store configuration.
There is an option to store configuration data in `.simpleblogger-debug` folder. To activate
it run `simpleblogger.py` with `-d` flag

***
![logo](http://www.wingware.com/images/wingware-logo-107x34.png)
This application was developed with the help of the Wingware IDE (the only one IDE that supports GTK+ autocomplete)
