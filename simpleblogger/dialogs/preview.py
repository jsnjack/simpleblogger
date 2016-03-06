import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit2', '4.0')
from gi.repository import Gtk, WebKit2, Gio
from pygments.formatters import HtmlFormatter


class PreviewDialog(Gtk.Window):
    def __init__(self, parent):
        super(PreviewDialog, self).__init__(title="Preview")
        self.parent = parent
        self.set_default_size(800, 600)

        header_bar = Gtk.HeaderBar()
        header_bar.set_show_close_button(True)
        header_bar.set_title("Preview")

        refresh_button = Gtk.Button()
        refresh_button.set_tooltip_text("Refresh")
        refresh_button.connect("clicked", self.on_refresh_button_clicked)
        icon = Gio.ThemedIcon(name="view-refresh-symbolic")
        image = Gtk.Image.new_from_gicon(icon, Gtk.IconSize.BUTTON)
        refresh_button.add(image)
        header_bar.pack_start(refresh_button)
        self.set_titlebar(header_bar)

        self.webview = WebKit2.WebView.new()
        self.webview.props.expand = True
        self.add(self.webview)

        self.on_refresh_button_clicked(None)

        self.show_all()

    def on_refresh_button_clicked(self, target):
        """
        Refresh preview window
        """
        html = "<style>{css}</style>{content}".format(
            css=HtmlFormatter().get_style_defs(),
            content=self.parent.sourceview.get_buffer().props.text
        )
        self.webview.load_html(html, None)
