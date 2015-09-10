from gi.repository import Gtk
from webbrowser import open as open_page

from providers.google import get_authorization_url


class AddAccountDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Add account", parent, 0, use_header_bar=True,
                            buttons=("_Apply", Gtk.ResponseType.OK, "_Cancel", Gtk.ResponseType.CANCEL))
        self.set_modal(True)

        # Set focus to cancel button (so that placeholder text will be visible)
        cancel_button = self.get_header_bar().get_children()[0]
        self.set_focus(cancel_button)

        apply_button = self.get_header_bar().get_children()[1]
        apply_button.get_style_context().add_class("suggested-action")

        self.email_entry = Gtk.Entry(placeholder_text=u"Email")

        auth_link_button = Gtk.Button("Authenticate simpleblogger (in browser)")
        auth_link_button.connect("clicked", self.on_auth_link_button_clicked)

        code_entry = Gtk.Entry(placeholder_text=u"Authentication code from the browser")

        box = self.get_content_area()
        box.add(self.email_entry)
        box.add(auth_link_button)
        box.add(code_entry)

        box.set_spacing(5)

        self.show_all()

    def on_auth_link_button_clicked(self, target):
        open_page(get_authorization_url(self.email_entry.get_text()))
