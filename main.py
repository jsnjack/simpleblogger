import sys

from gi.repository import Gtk, Gio


class SBWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        Gtk.Window.__init__(self, title="Simpleblogger", application=app)
        self.set_border_width(2)
        self.set_default_size(600, 400)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = "HeaderBar example"
        self.set_titlebar(header_bar)

        new_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-new-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        new_button.add(image)
        header_bar.pack_start(new_button)

        post_button = Gtk.Button()
        icon = Gio.ThemedIcon(name="document-send-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        post_button.add(image)
        header_bar.pack_start(post_button)

        menu_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="open-menu-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        menu_button.add(image)
        header_bar.pack_end(menu_button)

        menumodel = Gio.Menu()
        menumodel.append("New", "app.new")
        menumodel.append("Quit", "app.quit")
        popover = Gtk.Popover().new_from_model(menu_button, menumodel)
        menu_button.set_popover(popover)


class SBApplication(Gtk.Application):
    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        win = SBWindow(self)
        win.show_all()

    def do_startup(self):
            Gtk.Application.do_startup(self)

            new_action = Gio.SimpleAction.new("new", None)
            new_action.connect("activate", self.new_callback)
            self.add_action(new_action)

            quit_action = Gio.SimpleAction.new("quit", None)
            quit_action.connect("activate", self.quit_callback)
            self.add_action(quit_action)

    def new_callback(self, action, parameter):
            print("You clicked \"New\"")

    def quit_callback(self, action, parameter):
            print("You clicked \"Quit\"")
            self.quit()

if __name__ == '__main__':
    app = SBApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
