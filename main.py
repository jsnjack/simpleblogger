import sys

from gi.repository import Gtk, Gio, GtkSource

from dialogs.add_account import AddAccountDialog
from utils import load_config, save_config, get_blog_by_id


class SBWindow(Gtk.ApplicationWindow):
    def __init__(self, app):

        Gtk.Window.__init__(self, title="Simpleblogger", application=app)

        # Build UI
        scrolled_window = Gtk.ScrolledWindow()
        self.set_border_width(2)
        self.set_default_size(700, 550)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.title = "simpleblogger"
        header_bar.props.subtitle = "http://jsn-techtips.blogspot.com"
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
        menumodel.append("Add account...", "app.add_account")
        menumodel.append("Quit", "app.quit")

        m2 = Gio.Menu()
        for item in app.config["blogs"]:
            m2.append(item["name"], "app.select_blog_%s" % item["id"])
        menumodel.append_submenu("Blogs", m2)

        popover = Gtk.Popover().new_from_model(menu_button, menumodel)
        menu_button.set_popover(popover)

        # Source view
        sourceview = GtkSource.View.new()
        sourceview.set_auto_indent(True)
        sourceview.set_insert_spaces_instead_of_tabs(True)
        sourceview.set_indent_width(4)
        sourceview.set_wrap_mode(Gtk.WrapMode.WORD)
        lm = GtkSource.LanguageManager.new()
        buf = sourceview.get_buffer()
        buf.set_language(lm.get_language("html"))
        scrolled_window.add(sourceview)

        self.add(scrolled_window)
        if app.config["active_blog"]:
            app.activate_blog(app.config["active_blog"])


class SBApplication(Gtk.Application):
    config = None
    active_blog = None

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        self.main_window = SBWindow(self)
        self.main_window.show_all()

    def do_startup(self):
            Gtk.Application.do_startup(self)

            self.config = load_config()

            add_account_action = Gio.SimpleAction.new("add_account", None)
            add_account_action.connect("activate", self.add_account_callback)
            self.add_action(add_account_action)

            new_action = Gio.SimpleAction.new("new", None)
            new_action.connect("activate", self.new_callback)
            self.add_action(new_action)

            quit_action = Gio.SimpleAction.new("quit", None)
            quit_action.connect("activate", self.quit_callback)
            self.add_action(quit_action)

            for item in self.config["blogs"]:
                select_blog_action = Gio.SimpleAction.new("select_blog_%s" % item["id"], None)
                select_blog_action.connect("activate", self.select_blog_callback)
                self.add_action(select_blog_action)

    def add_account_callback(self, action, parameter):
        """
        Shows add new account dialog
        """
        def run_dialog(dialog):
            """
            Recreates dialog loop
            """
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                content_widgets = dialog.get_content_area().get_children()
                username = content_widgets[0].get_text()
                password = content_widgets[1].get_text()
                provider = content_widgets[2].get_active_id()
                if provider == "blogger":
                    from blogger import get_blogs
                data = get_blogs(username, password)
                if data["status"] == "ok":
                    message = "<b>Following blogs will be added:</b> \n"
                    for item in data["blogs"]:
                        message = message + item["name"] + "\n"
                    ok_dialog = Gtk.MessageDialog(parent=dialog, text=message, buttons=(Gtk.STOCK_APPLY, Gtk.ResponseType.OK),
                                                  use_markup=True)
                    ok_dialog.run()
                    ok_dialog.destroy()
                    dialog.destroy()

                for item in data["blogs"]:
                    self.config["blogs"].append(item)
                save_config(self.config)

                if data["status"] == "error":
                    error_dialog = Gtk.MessageDialog(parent=dialog, text=data["error"], buttons=(Gtk.STOCK_APPLY, Gtk.ResponseType.OK))
                    error_dialog.run()
                    error_dialog.destroy()
                    run_dialog(dialog)
            else:
                dialog.destroy()

        dialog = AddAccountDialog(self.main_window)
        run_dialog(dialog)

    def new_callback(self, action, parameter):
            print("You clicked \"New\"")

    def quit_callback(self, action, parameter):
            print("You clicked \"Quit\"")
            self.quit()

    def select_blog_callback(self, action, parameter):
        """
        Make selected blog active
        """
        blog_id = action.get_name().replace("select_blog_", "")
        self.activate_blog(blog_id)

    def activate_blog(self, blog_id):
        """
        Makes blog active
        """
        self.config["active_blog"] = blog_id
        save_config(self.config)
        blog = get_blog_by_id(self.config, blog_id)
        if blog:
            window = self.get_windows()[0]
            header_bar = window.get_children()[1]
            header_bar.set_title(blog["name"])
            header_bar.set_subtitle(blog["link"])


if __name__ == '__main__':
    app = SBApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
