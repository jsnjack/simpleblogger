import sys

from gi.repository import Gtk, Gio, GtkSource

from dialogs.add_account import AddAccountDialog
from dialogs.preview import PreviewDialog
from providers.blogger import BloggerProvider
from utils import load_config, save_config, get_blog_by_id


class SBWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        self.app = app

        Gtk.Window.__init__(self, title="Simpleblogger", application=app)

        # Build UI
        scrolled_window = Gtk.ScrolledWindow()
        self.set_border_width(2)
        self.set_default_size(700, 550)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.hexpand = True
        header_bar.props.vexpand = True
        header_bar_box = Gtk.VBox()

        self.title_entry = Gtk.Entry(placeholder_text=u"New post title")
        self.title_entry.connect("focus_in_event", self.on_title_entry_focus_in)
        self.title_entry.connect("focus_out_event", self.on_title_entry_focus_out)
        self.title_entry.props.xalign = 0.5
        self.title_entry.props.hexpand = True
        self.title_entry.props.vexpand = True
        self.title_entry.props.width_chars = 50
        title_entry_style = self.title_entry.get_style_context()
        title_entry_style.add_class("title")
        title_entry_style.remove_class("entry")

        subtitle_label = Gtk.Label()
        subtitle_label.get_style_context().add_class("subtitle")

        header_bar_box.add(self.title_entry)
        header_bar_box.add(subtitle_label)
        header_bar.set_custom_title(header_bar_box)
        self.set_titlebar(header_bar)

        post_button = Gtk.Button()
        post_button.connect("clicked", self.on_post_button_clicked)
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
        menumodel.append("Preview", "app.preview")
        menumodel.append("Add account...", "app.add_account")
        menumodel.append("Quit", "app.quit")

        self.select_blog_menu = Gio.Menu()
        for item in self.app.config["blogs"]:
            self.select_blog_menu.append(item["name"], "app.select_blog_%s" % item["id"])
        menumodel.append_submenu("Blogs", self.select_blog_menu)

        popover = Gtk.Popover().new_from_model(menu_button, menumodel)
        menu_button.set_popover(popover)

        # Source view
        self.sourceview = GtkSource.View.new()
        self.sourceview.set_auto_indent(True)
        self.sourceview.set_insert_spaces_instead_of_tabs(True)
        self.sourceview.set_indent_width(4)
        self.sourceview.set_wrap_mode(Gtk.WrapMode.WORD)
        lm = GtkSource.LanguageManager.new()
        buf = self.sourceview.get_buffer()
        buf.set_language(lm.get_language("html"))
        scrolled_window.add(self.sourceview)

        self.add(scrolled_window)
        if self.app.config["active_blog"]:
            self.app.activate_blog(self.app.config["active_blog"])

    def on_title_entry_focus_in(self, target, x):
        """
        When focus on title entry make it look like entry
        """
        target.get_style_context().add_class("entry")

    def on_title_entry_focus_out(self, target, x):
        """
        When moving focus out of title entry make it look like label
        """
        target.get_style_context().remove_class("entry")

    def on_post_button_clicked(self, target):
        """
        Send post to remote server
        """
        blog = get_blog_by_id(self.app.config, self.app.config["active_blog"])
        if blog["provider"] == "blogger":
            service = BloggerProvider(blog["username"], blog["password"])
        result = service.send_post(blog["id"], self.title_entry.get_text(), self.sourceview.get_buffer().props.text, [])
        print result


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
            new_action.connect("activate", self.on_new)
            self.add_action(new_action)

            preview_action = Gio.SimpleAction.new("preview", None)
            preview_action.connect("activate", self.on_preview)
            self.add_action(preview_action)

            quit_action = Gio.SimpleAction.new("quit", None)
            quit_action.connect("activate", self.on_quit)
            self.add_action(quit_action)

            for item in self.config["blogs"]:
                self.create_select_blog_action(item["id"])

    def create_select_blog_action(self, blog_id):
        select_blog_action = Gio.SimpleAction.new("select_blog_%s" % blog_id, None)
        select_blog_action.connect("activate", self.on_select_blog)
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
                    service = BloggerProvider(username, password)
                data = service.get_blogs()
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
                        if not get_blog_by_id(self.config, item["id"]):
                            self.config["blogs"].append(item)
                            # Creat actions and add new item in the menu
                            self.create_select_blog_action(item["id"])
                            main_window = self.get_windows()[0]
                            main_window.select_blog_menu.append(item["name"], "app.select_blog_%s" % item["id"])

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

    def on_quit(self, action, parameter):
        """
        Quit from the application
        """
        self.quit()

    def on_new(self, action, parameter):
        """
        Clean title and source view
        """
        window = self.get_windows()[0]
        header_bar = window.get_children()[1]
        header_bar.get_custom_title().get_children()[0].set_text("")
        window.sourceview.get_buffer().props.text = ""

    def on_preview(self, action, parameter):
        """
        Open preview dialog
        """
        dialog = PreviewDialog(self.main_window)
        dialog.run()
        dialog.destroy()

    def on_select_blog(self, action, parameter):
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
            header_bar.get_custom_title().get_children()[1].set_text(blog["name"])


if __name__ == '__main__':
    app = SBApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
