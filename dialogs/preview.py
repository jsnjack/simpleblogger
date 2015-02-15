from gi.repository import Gtk, WebKit2


class PreviewDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Preview", parent, 0, use_header_bar=True)
        self.set_default_size(800, 600)

        box = self.get_content_area()
        webview = WebKit2.WebView.new()
        webview.props.expand = True
        webview.load_html(parent.sourceview.get_buffer().props.text, None)
        box.add(webview)

        self.show_all()
