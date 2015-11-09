#!/usr/bin/env python2
import gi
import os
import pickle
import sys

gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
from gi.repository import Gtk, Gio, GtkSource, GdkPixbuf
from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer, get_lexer_by_name

import utils

from dialogs.add_account import AddAccountDialog
from dialogs.insert_code import InsertCodeDialog
from dialogs.preview import PreviewDialog
from providers.google import get_credentials, get_user_info, create_service, get_blogs, save_credentials, publish_post
from providers.picasa import PicasaImageThreading


# Use debug directory
if sys.argv[-1] == '-d':
    sys.argv.pop(-1)
    CONFIG_DIRECTORY = os.path.join(os.path.expanduser("~"), ".simpleblogger-debug")
else:
    CONFIG_DIRECTORY = os.path.join(os.path.expanduser("~"), ".simpleblogger")


class SBWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        self.app = app

        Gtk.Window.__init__(self, title="simpleblogger", application=app)
        self.set_wmclass("simpleblogger", "simpleblogger")

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
        post_button.set_tooltip_text("Publish post")
        post_button.connect("clicked", self.on_post_button_clicked)
        icon = Gio.ThemedIcon(name="document-send-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        post_button.add(image)
        header_bar.pack_start(post_button)

        tag_button = Gtk.Button()
        tag_button.set_tooltip_text("Add tags")
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
        insert_button.set_tooltip_text("Insert image, code")
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
        post_menu_section = Gio.Menu()
        post_menu_section.append("New", "app.new")
        post_menu_section.append("Preview...", "app.preview")
        menumodel.append_section("Post", post_menu_section)
        draft_menu_section = Gio.Menu()
        draft_menu_section.append("Open...", "app.open_draft")
        draft_menu_section.append("Save...", "app.save_draft")
        menumodel.append_section("Drafts", draft_menu_section)
        blog_menu_section = Gio.Menu()
        blog_menu_section.append("Add account...", "app.add_account")
        blog_menu_section.append("Remove current blog", "app.remove_current_blog")
        self.select_blog_menu = Gio.Menu()
        for item in self.app.config["blogs"]:
            self.select_blog_menu.append(item["name"], "app.select_blog_%s" % item["id"])
        blog_menu_section.append_submenu("Blogs", self.select_blog_menu)
        menumodel.append_section("Blog and account management", blog_menu_section)
        application_menu_section = Gio.Menu()
        application_menu_section.append("Quit", "app.quit")
        menumodel.append_section(None, application_menu_section)

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
        self.infobar.add_button("_New", Gtk.ResponseType.APPLY)
        self.infobar.add_button("_Close", Gtk.ResponseType.CLOSE)
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
        blog = utils.get_blog_by_id(self.app.config, self.app.config["active_blog"])
        if blog:
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
                utils.save_config(self.app.config)
            publish_post(
                blog,
                self.title_entry.get_text(),
                self.sourceview.get_buffer().props.text,
                tags
            )
            self.infobar.get_content_area().get_children()[0].set_text("Published")
            self.infobar.get_action_area().get_children()[1].props.visible = True
            self.infobar.show()
        else:
            self.infobar.get_content_area().get_children()[0].set_text("No blog is selected")
            # Hide New button
            self.infobar.get_action_area().get_children()[1].props.visible = False
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

        blog = utils.get_blog_by_id(self.app.config, self.app.config["active_blog"])

        liststore = Gtk.ListStore(str)
        if blog:
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

    def __init__(self):
        Gtk.Application.__init__(self)

    def do_activate(self):
        self.main_window = SBWindow(self)
        self.main_window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

        self.config = utils.load_config()

        add_account_action = Gio.SimpleAction.new("add_account", None)
        add_account_action.connect("activate", self.add_account_callback)
        self.add_action(add_account_action)

        new_action = Gio.SimpleAction.new("new", None)
        new_action.connect("activate", self.on_new)
        self.add_action(new_action)

        preview_action = Gio.SimpleAction.new("preview", None)
        preview_action.connect("activate", self.on_preview)
        self.add_action(preview_action)

        open_action = Gio.SimpleAction.new("open_draft", None)
        open_action.connect("activate", self.on_open_draft)
        self.add_action(open_action)

        save_action = Gio.SimpleAction.new("save_draft", None)
        save_action.connect("activate", self.on_save_draft)
        self.add_action(save_action)

        remove_current_blog_action = Gio.SimpleAction.new("remove_current_blog", None)
        remove_current_blog_action.connect("activate", self.on_remove_current_blog)
        self.add_action(remove_current_blog_action)

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

    def on_remove_current_blog(self, action, parameter):
        """
        Removes current blog
        """
        dialog = Gtk.MessageDialog(
            parent=self.main_window,
            text="Confirm removing blog",
            buttons=(
                "_Cancel", Gtk.ResponseType.CANCEL,
                "_Remove", Gtk.ResponseType.OK
            )
        )
        dialog.get_action_area().get_children()[1].get_style_context().add_class("destructive-action")
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
            blog = utils.get_blog_by_id(self.config, self.config["active_blog"])
            if blog:
                index = self.config["blogs"].index(blog)
                self.config["blogs"].pop(index)
                self.config["active_blog"] = None
                header_bar = self.main_window.get_children()[1]
                subtitle = header_bar.get_custom_title().get_children()[1]
                subtitle.set_text("")
                utils.save_config(self.config)
                # Build menu items
                self.main_window.select_blog_menu.remove_all()
                for item in self.config["blogs"]:
                        # Creat actions and add new item in the menu
                        self.create_select_blog_action(item["id"])
                        self.main_window.select_blog_menu.append(item["name"], "app.select_blog_%s" % item["id"])
            else:
                self.main_window.infobar.get_content_area().get_children()[0].set_text("No blog to remove")
                self.main_window.infobar.get_action_area().get_children()[1].props.visible = False
                self.main_window.infobar.show()
        else:
            dialog.destroy()

    def add_account_callback(self, action, parameter):
        """
        Shows add new account dialog
        """
        def run_dialog(dialog):
            """
            Recreates dialog loop
            """
            response = dialog.run()
            error = u"No blogs associated with the account"
            if response == Gtk.ResponseType.OK:
                content_widgets = dialog.get_content_area().get_children()
                code = content_widgets[2].get_text()
                credentials = get_credentials(code)
                if credentials:
                    email = get_user_info(credentials).get("email")
                    service = create_service(credentials, "blogger")
                    blogs = get_blogs(service, email)
                else:
                    blogs = None
                    error = u"Can't exchange code for credentials"
                if blogs:
                    message = "<b>Following blogs will be added:</b> \n"
                    for item in blogs:
                        message = message + item["name"] + "\n"
                    ok_dialog = Gtk.MessageDialog(parent=dialog, text=message, buttons=("_Apply", Gtk.ResponseType.OK),
                                                  use_markup=True)
                    ok_dialog.run()
                    ok_dialog.destroy()
                    dialog.destroy()

                    for item in blogs:
                        if not utils.get_blog_by_id(self.config, item["id"]):
                            self.config["blogs"].append(item)
                            # Creat actions and add new item in the menu
                            self.create_select_blog_action(item["id"])
                            main_window = self.get_windows()[0]
                            main_window.select_blog_menu.append(item["name"], "app.select_blog_%s" % item["id"])

                    utils.save_config(self.config)
                    save_credentials(credentials, email)
                else:
                    error_dialog = Gtk.MessageDialog(
                        parent=dialog, text=error, buttons=("_Close", Gtk.ResponseType.OK)
                    )
                    error_dialog.run()
                    error_dialog.destroy()
                    run_dialog(dialog)
            else:
                dialog.destroy()

        dialog = AddAccountDialog(self.main_window)
        run_dialog(dialog)

    def on_open_draft(self, action, paraneter):
        """
        Open draft from previously saved file
        """
        dialog = Gtk.FileChooserDialog(
            "Open draft", self.main_window, Gtk.FileChooserAction.OPEN,
            ("_Cancel", Gtk.ResponseType.CANCEL,
             "_Open", Gtk.ResponseType.OK)
        )

        open_button = dialog.get_header_bar().get_children()[1]
        open_button.get_style_context().add_class("suggested-action")

        # Add filters
        draft_filter = Gtk.FileFilter()
        draft_filter.set_name("Draft files")
        draft_filter.add_pattern("*.sbd")
        dialog.add_filter(draft_filter)

        any_filter = Gtk.FileFilter()
        any_filter.set_name("Any files")
        any_filter.add_pattern("*")
        dialog.add_filter(any_filter)

        dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            with open(filename, "rb") as draft_file:
                draft_obj = pickle.load(draft_file)
                self.main_window.title_entry.set_text(draft_obj["title"])
                self.main_window.sourceview.get_buffer().props.text = draft_obj["body"]
                if draft_obj["tags"]:
                    self.main_window.tag_entry.get_parent().get_relative_to().get_style_context().remove_class(
                        "suggested-action")
                self.main_window.tag_entry.set_text(draft_obj["tags"])
        dialog.destroy()

    def on_save_draft(self, action, paraneter):
        """
        Save post data to the draft file
        """
        dialog = Gtk.FileChooserDialog(
            "Save draft", self.main_window, Gtk.FileChooserAction.SAVE,
            ("_Cancel", Gtk.ResponseType.CANCEL,
             "_Save", Gtk.ResponseType.OK)
        )

        save_button = dialog.get_header_bar().get_children()[1]
        save_button.get_style_context().add_class("suggested-action")

        # Add filters
        draft_filter = Gtk.FileFilter()
        draft_filter.set_name("Draft files")
        draft_filter.add_pattern("*.sbd")
        dialog.add_filter(draft_filter)

        any_filter = Gtk.FileFilter()
        any_filter.set_name("Any files")
        any_filter.add_pattern("*")
        dialog.add_filter(any_filter)

        post_title = self.main_window.title_entry.get_text()
        dialog.set_current_name(utils.generate_filename(post_title) + u".sbd")
        dialog.set_current_folder(os.path.expanduser("~"))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            with open(filename, "wb") as draft_file:
                draft_obj = {
                    "title": post_title,
                    "body": self.main_window.sourceview.get_buffer().props.text,
                    "tags": self.main_window.tag_entry.get_text()
                }
                pickle.dump(draft_obj, draft_file)
            self.main_window.infobar.get_content_area().get_children()[0].set_text("Draft was succesfully saved")
            self.main_window.infobar.get_action_area().get_children()[1].props.visible = True
            self.main_window.infobar.show()
        dialog.destroy()

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

        if not utils.get_blog_by_id(self.config, self.config["active_blog"]):
            # If can't get blog from config show message
            self.main_window.infobar.get_content_area().get_children()[0].set_text("No blog is selected")
            # Hide New button
            self.main_window.infobar.get_action_area().get_children()[1].props.visible = False
            self.main_window.infobar.show()
            return

        dialog = Gtk.FileChooserDialog(
            "Please choose an image", self.main_window, Gtk.FileChooserAction.OPEN,
            ("_Cancel", Gtk.ResponseType.CANCEL,
             "_Add", Gtk.ResponseType.OK)
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
                buttons=("_Cancel", Gtk.ResponseType.CANCEL)
            )
            box = spinner_dialog.get_content_area()
            spinner = Gtk.Spinner()
            spinner.props.visible = True
            box.add(spinner)
            spinner.start()
            uploading_thread = PicasaImageThreading(
                utils.get_blog_by_id(self.config, self.config["active_blog"]),
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
                self.main_window.sourceview.get_buffer().insert_at_cursor(utils.wrap_image_url(image_url))
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
        initial_lexer_name = self.config.get("last_lexer", None)
        dialog = InsertCodeDialog(self.main_window, initial_lexer_name)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            lexer_name = None
            lexer_verbose_name = dialog.get_content_area().get_children()[0].get_active_text()
            list_model = dialog.get_content_area().get_children()[0].get_model()
            for item in list_model:
                if item[0] == lexer_verbose_name:
                    lexer_name = item[1]
                    # Save as the last used
                    self.config["last_lexer"] = lexer_verbose_name
                    utils.save_config(self.config)
                    break
            code = dialog.get_content_area().get_children()[1].get_buffer().props.text

            dialog.destroy()

            if lexer_name:
                lexer = get_lexer_by_name(lexer_name)
            else:
                lexer = guess_lexer(code)
            styled_code = highlight(code, lexer, HtmlFormatter())
            self.main_window.sourceview.get_buffer().insert_at_cursor(styled_code)
        else:
            dialog.destroy()

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
        utils.save_config(self.config)
        blog = utils.get_blog_by_id(self.config, blog_id)
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
