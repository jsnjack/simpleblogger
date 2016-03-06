import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from pygments.lexers import get_all_lexers


class InsertCodeDialog(Gtk.Dialog):
    def __init__(self, parent, initial_lexer_name=None):
        Gtk.Dialog.__init__(self, "Insert code", parent, 0, use_header_bar=True,
                            buttons=("_OK", Gtk.ResponseType.OK, "_Cancel", Gtk.ResponseType.CANCEL))
        self.set_modal(True)
        self.set_default_size(500, 350)
        self.set_resizable(True)
        self.set_size_request(-1, 200)

        box = self.get_content_area()

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        scroll_box = Gtk.VBox()
        scroll_box.props.homogeneous = False

        cancel_button = self.get_header_bar().get_children()[0]
        self.set_focus(cancel_button)

        ok_button = self.get_header_bar().get_children()[1]
        ok_button.set_name("Insert")
        ok_button.get_style_context().add_class("suggested-action")

        combobox = Gtk.ComboBoxText.new_with_entry()
        combobox_entry = combobox.get_child()
        completion = Gtk.EntryCompletion()
        completion.set_model(combobox.get_model())
        completion.set_text_column(0)
        combobox_entry.set_completion(completion)
        combobox_entry.set_placeholder_text("Select language")

        if initial_lexer_name:
            combobox_entry.set_text(initial_lexer_name)

        # Fill combobox with languages
        for item in get_all_lexers():
            combobox.append(item[1][0], item[0])

        textview = Gtk.TextView()
        textview.props.expand = True

        scroll_box.pack_start(combobox, False, False, 0)
        scroll_box.pack_end(textview, True, True, 0)
        scrolled_window.add(scroll_box)

        box.add(scrolled_window)

        self.show_all()
