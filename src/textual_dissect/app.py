from __future__ import annotations

from importlib import import_module
from textwrap import dedent

from textual import __version__, on
from textual.app import App, ComposeResult
from textual.case import camel_to_snake
from textual.reactive import var
from textual.widgets import Link, OptionList, TextArea
from textual.widgets.option_list import Option

WIDGET_CLASSES = [
    "Button",
    "Checkbox",
    "Collapsible",
    "ContentSwitcher",
    "DataTable",
    "Digits",
    "DirectoryTree",
    "Footer",
    "Header",
    "Input",
    "Label",
    "Link",
    "ListView",
    "LoadingIndicator",
    "Log",
    "MarkdownViewer",
    "Markdown",
    "MaskedInput",
    "OptionList",
    "Placeholder",
    "Pretty",
    "ProgressBar",
    "RadioButton",
    "RadioSet",
    "RichLog",
    "Rule",
    "Select",
    "SelectionList",
    "Sparkline",
    "Static",
    "Switch",
    "Tabs",
    "TabbedContent",
    "TextArea",
    "Tree",
]


class WidgetsList(OptionList):
    DEFAULT_CSS = """
    WidgetsList {
        height: 1fr;
        width: 25;
        dock: left;
        border: heavy $foreground 50%;

        &:focus {
            border: heavy $border;
        }
    }
    """

    def __init__(self) -> None:
        super().__init__(
            *[Option(widget, id=widget) for widget in WIDGET_CLASSES],
        )


class DocumentationLink(Link):
    BASE_URL = "https://textual.textualize.io/widgets/"

    DEFAULT_CSS = """
    DocumentationLink {
        width: 1fr;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            border: solid $border;
        }
    }
    """

    widget_class: var[str] = var(WIDGET_CLASSES[0])

    def __init__(self) -> None:
        super().__init__(text=self.BASE_URL, url=self.BASE_URL)

    def watch_widget_class(self, widget_class: str) -> None:
        widget_url = self.BASE_URL + camel_to_snake(widget_class)
        self.text = widget_url
        self.url = widget_url


class SourceCodeLink(Link):
    BASE_URL = "https://github.com/Textualize/textual/"
    VERSION_PATH = f"blob/v{__version__}/"
    WIDGETS_PATH = "src/textual/widgets/"

    SOURCE_URL = BASE_URL + VERSION_PATH + WIDGETS_PATH

    DEFAULT_CSS = """
    SourceCodeLink {
        width: 1fr;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            border: solid $border;
        }
    }
    """

    widget_class: var[str] = var(WIDGET_CLASSES[0])

    def __init__(self) -> None:
        super().__init__(text=self.SOURCE_URL, url=self.SOURCE_URL)

    def watch_widget_class(self, widget_class: str) -> None:
        widget_file = f"_{camel_to_snake(widget_class)}.py"
        widget_url = self.SOURCE_URL + widget_file
        self.text = widget_url
        self.url = widget_url


_WIDGET_DEFAULT_CSS_CACHE: dict[str, str] = {}


def get_default_css(widget_class: str) -> str:
    if widget_class not in _WIDGET_DEFAULT_CSS_CACHE:
        widget_module_path = f"._{camel_to_snake(widget_class)}"
        module = import_module(widget_module_path, package="textual.widgets")
        class_ = getattr(module, widget_class)

        raw_default_css = class_.DEFAULT_CSS
        clean_default_css = dedent(raw_default_css).strip()
        _WIDGET_DEFAULT_CSS_CACHE[widget_class] = clean_default_css

    return _WIDGET_DEFAULT_CSS_CACHE[widget_class]


class DefaultCSSView(TextArea):
    DEFAULT_CSS = """
    DefaultCSSView {
        width: 1fr;
        border: solid $foreground 50%;
        padding: 0 1;
        scrollbar-gutter: stable;

        &:focus {
            border: solid $border;
        }
    }
    """

    widget_class: var[str] = var(WIDGET_CLASSES[0])

    def __init__(self) -> None:
        super().__init__(read_only=True)

    def watch_widget_class(self, widget_class: str) -> None:
        default_css = get_default_css(widget_class)
        self.load_text(default_css)


class TextualDissectApp(App):
    widget_class: var[str] = var(WIDGET_CLASSES[0])

    def compose(self) -> ComposeResult:
        widgets_list = WidgetsList()
        widgets_list.border_title = "Widgets"

        documentation_link = DocumentationLink()
        documentation_link.data_bind(TextualDissectApp.widget_class)
        documentation_link.border_title = "Documentation"

        source_code_link = SourceCodeLink()
        source_code_link.data_bind(TextualDissectApp.widget_class)
        source_code_link.border_title = "Source Code"

        default_css_view = DefaultCSSView()
        default_css_view.data_bind(TextualDissectApp.widget_class)
        default_css_view.border_title = "Default CSS"
        default_css_view.cursor_blink = False

        yield widgets_list
        yield documentation_link
        yield source_code_link
        yield default_css_view

    @on(WidgetsList.OptionHighlighted)
    def on_widgets_list_option_highlighted(
        self, event: WidgetsList.OptionHighlighted
    ) -> None:
        widget_class = event.option_id
        assert widget_class is not None
        self.widget_class = widget_class


def run() -> None:
    app = TextualDissectApp()
    app.run()
