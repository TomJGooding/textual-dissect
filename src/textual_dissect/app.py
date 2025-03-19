from __future__ import annotations

from importlib import import_module
from textwrap import dedent

import tree_sitter_scss
from textual import __version__, on
from textual.app import App, ComposeResult
from textual.case import camel_to_snake
from textual.dom import DOMNode
from textual.reactive import var
from textual.widgets import Link, OptionList, TextArea, Tree
from textual.widgets.option_list import Option
from tree_sitter import Language

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


_WIDGET_BASE_CLASSES_CACHE: dict[str, list[str]] = {}


def get_base_classes(widget_class: str) -> list[str]:
    if widget_class not in _WIDGET_BASE_CLASSES_CACHE:
        widget_module_path = f"._{camel_to_snake(widget_class)}"
        module = import_module(widget_module_path, package="textual.widgets")

        classes: list[str] = []
        class_ = getattr(module, widget_class)
        while True:
            classes.append(class_.__name__)
            for base in class_.__bases__:
                if issubclass(base, DOMNode):
                    class_ = base
                    break
            else:
                break

        classes.reverse()
        _WIDGET_BASE_CLASSES_CACHE[widget_class] = classes

    return _WIDGET_BASE_CLASSES_CACHE[widget_class]


class InheritanceTree(Tree):
    DEFAULT_CSS = """
    InheritanceTree {
        height: 7;
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
        super().__init__("DOMNode")

    def watch_widget_class(self, widget_class: str) -> None:
        self.clear()

        base_classes = get_base_classes(widget_class)
        widget = self.root.add(base_classes[1], expand=True, allow_expand=False)
        for class_ in base_classes[2:]:
            widget = widget.add(class_, expand=True, allow_expand=False)

        self.cursor_line = self.last_line


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


_TCSS_LANGUAGE = Language(tree_sitter_scss.language())
_TCSS_HIGHLIGHT_QUERY = """
(comment) @comment @spell

[
 (tag_name)
 (nesting_selector)
 (universal_selector)
 ] @type.class

[
 (class_name)
 (id_name)
 (property_name)
 ] @css.property

(variable) @type.builtin

((property_name) @type.definition
  (#lua-match? @type.definition "^[-][-]"))
((plain_value) @type
  (#lua-match? @type "^[-][-]"))

[
 (string_value)
 (color_value)
 (unit)
 ] @string

[
 (integer_value)
 (float_value)
 ] @number
"""


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

        inheritance_tree = InheritanceTree()
        inheritance_tree.data_bind(TextualDissectApp.widget_class)
        inheritance_tree.border_title = "Inheritance Tree"
        inheritance_tree.show_root = False

        default_css_view = DefaultCSSView()
        default_css_view.data_bind(TextualDissectApp.widget_class)
        default_css_view.border_title = "Default CSS"
        default_css_view.cursor_blink = False
        default_css_view.register_language(
            "tcss", _TCSS_LANGUAGE, _TCSS_HIGHLIGHT_QUERY
        )
        default_css_view.language = "tcss"

        yield widgets_list
        yield documentation_link
        yield source_code_link
        yield inheritance_tree
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
