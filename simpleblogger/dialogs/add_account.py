from gi.repository import Gtk


class AddAccountDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Add account", parent, 0, use_header_bar=True,
                            buttons=(Gtk.STOCK_APPLY, Gtk.ResponseType.OK, Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        self.set_modal(True)

        # Set focus to cancel button (so that placeholder text will be visible)
        cancel_button = self.get_header_bar().get_children()[0]
        self.set_focus(cancel_button)

        apply_button = self.get_header_bar().get_children()[1]
        apply_button.get_style_context().add_class("suggested-action")

        username_entry = Gtk.Entry(placeholder_text=u"Username")
        password_entry = Gtk.Entry(placeholder_text=u"Password")
        password_entry.set_visibility(False)
        provider_choice = Gtk.ComboBoxText()
        provider_choice.append("blogger", u"Blogger")

        box = self.get_content_area()
        box.add(username_entry)
        box.add(password_entry)
        box.add(provider_choice)

        box.set_spacing(5)
        provider_choice.set_active_id("blogger")

        self.show_all()
