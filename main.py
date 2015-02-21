import os
import sys

from gi.repository import Gtk, Gio, GtkSource, GdkPixbuf

from dialogs.add_account import AddAccountDialog
from dialogs.preview import PreviewDialog
from providers.blogger import BloggerProvider
from providers.picasa import PicasaImageThreading
from utils import load_config, save_config, get_blog_by_id, wrap_image_url


class SBWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        self.app = app

        Gtk.Window.__init__(self, title="Simpleblogger", application=app)

        # Build UI
        scrolled_window = Gtk.ScrolledWindow()
        main_box = Gtk.VBox()
        main_box.props.homogeneous = False
        scrolled_window.add(main_box)
        self.set_border_width(2)
        self.set_default_size(700, 550)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.props.hexpand = True
        header_bar.props.vexpand = True
        header_bar_box = Gtk.VBox()

        self.title_entry = Gtk.Entry(placeholder_text=u"New post title")
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

        tag_button = Gtk.Button()
        tag_button.get_style_context().add_class("suggested-action")
        self.tag_popover = Gtk.Popover.new(tag_button)
        self.tag_entry = Gtk.Entry()
        self.tag_popover.add(self.tag_entry)
        tag_button.connect("clicked", self.on_tag_button_clicked)
        self.tag_popover.connect("hide", self.on_tag_popover_hide, tag_button)
        icon = Gio.ThemedIcon(name="bookmark-new-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        tag_button.add(image)
        header_bar.pack_start(tag_button)

        insert_button = Gtk.MenuButton()
        icon = Gio.ThemedIcon(name="list-add-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        insert_button.add(image)
        header_bar.pack_start(insert_button)

        insert_menumodel = Gio.Menu()
        insert_menumodel.append("Image...", "app.insert_image")
        insert_menumodel.append("Code...", "app.insert_code")

        insert_popover = Gtk.Popover().new_from_model(insert_button, insert_menumodel)
        insert_button.set_popover(insert_popover)

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

        menu_popover = Gtk.Popover().new_from_model(menu_button, menumodel)
        menu_button.set_popover(menu_popover)

        # Source view
        self.sourceview = GtkSource.View.new()
        self.sourceview.props.expand = True
        self.sourceview.set_auto_indent(True)
        self.sourceview.set_insert_spaces_instead_of_tabs(True)
        self.sourceview.set_indent_width(4)
        self.sourceview.set_wrap_mode(Gtk.WrapMode.WORD)
        lm = GtkSource.LanguageManager.new()
        buf = self.sourceview.get_buffer()
        buf.set_language(lm.get_language("html"))

        self.infobar = Gtk.InfoBar()
        self.infobar.props.no_show_all = True
        self.infobar.props.expand = False
        self.infobar.add_button(Gtk.STOCK_NEW, Gtk.ResponseType.APPLY)
        self.infobar.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        self.infobar.set_default_response(Gtk.ResponseType.CLOSE)
        self.infobar.connect("response", self.on_infobar_response)
        infobar_label = Gtk.Label("InfoBar example")
        infobar_label.props.visible = True
        content = self.infobar.get_content_area()
        content.add(infobar_label)

        main_box.pack_start(self.infobar, False, False, 0)
        main_box.pack_end(self.sourceview, True, True, 0)

        self.add(scrolled_window)
        if self.app.config["active_blog"]:
            self.app.activate_blog(self.app.config["active_blog"])

    def new_post(self):
        """
        Clear window for a new post
        """
        self.get_children()[1].get_custom_title().get_children()[0].set_text("")
        self.sourceview.get_buffer().props.text = ""
        self.tag_entry.set_text("")
        self.tag_entry.get_parent().get_relative_to().get_style_context().add_class("suggested-action")

    def on_infobar_response(self, infobar, response_id):
        """
        Handle user response
        """
        if response_id == Gtk.ResponseType.APPLY:
            self.new_post()
        infobar.hide()

    def on_post_button_clicked(self, target):
        """
        Send post to remote server
        """
        blog = get_blog_by_id(self.app.config, self.app.config["active_blog"])
        if blog["provider"] == "blogger":
            service = BloggerProvider(blog["username"], blog["password"])
            tags = self.tag_entry.get_text().split(",")
            tags = [x.strip() for x in tags]
            tags = [unicode(x, "utf-8") for x in tags]
            # Add new tags to the blog
            new_tags = []
            for tag in tags:
                if tag not in blog["tags"]:
                    new_tags.append(tag)
            if new_tags:
                index = self.app.config["blogs"].index(blog)
                self.app.config["blogs"][index]["tags"].extend(new_tags)
                save_config(self.app.config)
        result = service.send_post(blog["id"], self.title_entry.get_text(), self.sourceview.get_buffer().props.text, tags)
        self.infobar.get_content_area().get_children()[0].set_text(result)
        self.infobar.show()

    def on_tag_popover_hide(self, target, tag_button):
        """
        Highlights button if tags is empty
        """
        tag_button.get_style_context().remove_class("suggested-action")
        if not target.get_child().get_text():
            tag_button.get_style_context().add_class("suggested-action")

    def on_tag_button_clicked(self, target):
        """
        Select tag
        """
        def custom_match_func(completion, key, treeiter, user_data, data):
            """
            Filters matches
            """
            last_key = key.split(",")[-1].strip()
            if last_key in completion.get_model()[treeiter][0]:
                return True

        def on_match_selected(completion, treemodel, treeiter):
            """
            Adds selected match to the string
            """
            current_text = completion.get_entry().get_text()
            to_preserve = current_text.split(",")[:-1]
            old_text = u""
            for item in to_preserve:
                old_text = old_text + unicode(item.strip(), "utf-8") + u", "
            new_text = old_text + unicode(treemodel[treeiter][0], "utf-8")

            # set back the whole text
            completion.get_entry().set_text(new_text)
            # move the cursor at the end
            completion.get_entry().set_position(-1)
            return True

        blog = get_blog_by_id(self.app.config, self.app.config["active_blog"])

        liststore = Gtk.ListStore(str)
        for item in blog["tags"]:
            liststore.append([item])

        completion = Gtk.EntryCompletion()
        completion.set_model(liststore)
        completion.set_text_column(0)
        completion.set_match_func(custom_match_func, None, None)
        completion.connect('match-selected', on_match_selected)

        self.tag_entry.set_completion(completion)

        self.tag_popover.show_all()


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
        self.active_blog = self.config["active_blog"]

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

        # Insert actions
        insert_image_action = Gio.SimpleAction.new("insert_image", None)
        insert_image_action.connect("activate", self.on_insert_image)
        self.add_action(insert_image_action)

        insert_code_action = Gio.SimpleAction.new("insert_code", None)
        insert_code_action.connect("activate", self.on_insert_code)
        self.add_action(insert_code_action)

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

    def on_insert_image(self, action, parameter):
        """
        Insert image into post
        """
        def image_filter_func(filter_info, data):
            """
            Allows user to choose only images
            """
            allowed_mime_types = ("image/png", "image/jpeg")
            if filter_info.mime_type in allowed_mime_types:
                return True

        def image_preview_func(target):
            """
            Update preview widget
            """
            filename = target.get_preview_filename()
            preview_widget = target.get_preview_widget()
            preview_widget.props.margin_right = 10
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_size(filename, 200, 200)
                preview_widget.set_from_pixbuf(pixbuf)
                target.set_preview_widget_active(True)
            except:
                target.set_preview_widget_active(False)

        dialog = Gtk.FileChooserDialog(
            "Please choose an image", self.main_window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_ADD, Gtk.ResponseType.OK)
        )
        dialog.set_current_folder(os.path.join(os.path.expanduser('~'), 'Pictures'))

        add_button = dialog.get_header_bar().get_children()[1]
        add_button.get_style_context().add_class("suggested-action")

        # Add filters
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Image files")
        image_filter.add_custom(Gtk.FileFilterFlags.MIME_TYPE, image_filter_func, None)
        dialog.add_filter(image_filter)

        any_filter = Gtk.FileFilter()
        any_filter.set_name("Any files")
        any_filter.add_pattern("*")
        dialog.add_filter(any_filter)

        preview_widget = Gtk.Image()
        dialog.set_preview_widget(preview_widget)

        filechooser = dialog.get_content_area().get_children()[0]
        filechooser.connect("update-preview", image_preview_func)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            image_filename = dialog.get_filename()
            dialog.destroy()
            # Show spinner
            spinner_dialog = Gtk.MessageDialog(
                parent=self.main_window, text="Wait until your image is uploaded",
                buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
            )
            box = spinner_dialog.get_content_area()
            spinner = Gtk.Spinner()
            spinner.props.visible = True
            box.add(spinner)
            spinner.start()
            uploading_thread = PicasaImageThreading(
                get_blog_by_id(self.config, self.active_blog),
                image_filename,
                spinner_dialog
            )
            uploading_thread.start()
            response = spinner_dialog.run()
            if response == Gtk.ResponseType.OK:
                # Image was uploaded successfully insert code into post and close
                # dialog
                image_url = spinner_dialog.uploaded_image_link
                spinner_dialog.destroy()
                self.main_window.sourceview.get_buffer().insert_at_cursor(wrap_image_url(image_url))
            else:
                # User canceled uploading. Stop thread, close dialog
                uploading_thread.stop()
                spinner_dialog.destroy()
        else:
            dialog.destroy()

    def on_insert_code(self, action, parameter):
        """
        Insert code block into post
        """
        print("Insert code")

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
        window.new_post()

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
            text = u'<a href="{href}">{name}</a>'.format(href=blog["link"], name=blog["name"])
            subtitle = header_bar.get_custom_title().get_children()[1]
            subtitle.props.use_markup = True
            subtitle.props.track_visited_links = False
            subtitle.set_markup(text)


if __name__ == '__main__':
    app = SBApplication()
    exit_status = app.run(sys.argv)
    sys.exit(exit_status)
