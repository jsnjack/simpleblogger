from gi.repository import Gtk, WebKit2
from pygments.formatters import HtmlFormatter


class PreviewDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(self, "Preview", parent, 0, use_header_bar=True)
        self.set_default_size(800, 600)

        box = self.get_content_area()
        webview = WebKit2.WebView.new()
        webview.props.expand = True
        html = "<style>{css}</style>{content}".format(
            css=HtmlFormatter().get_style_defs(),
            content=parent.sourceview.get_buffer().props.text
        )
        webview.load_html(html, None)
        box.add(webview)

        self.show_all()
