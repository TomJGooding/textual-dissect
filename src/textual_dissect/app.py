from __future__ import annotations

import inspect
from dataclasses import dataclass
from importlib import import_module
from textwrap import dedent

import tree_sitter_scss
from textual import __version__, on
from textual.app import App, ComposeResult
from textual.case import camel_to_snake
from textual.containers import HorizontalGroup
from textual.dom import DOMNode
from textual.reactive import var
from textual.widget import Widget
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

DOCS_BASE_URL = "https://textual.textualize.io/"
DOCS_WIDGETS_URL = DOCS_BASE_URL + "widgets/"

SRC_BASE_URL = "https://github.com/Textualize/textual/"
SRC_VERSION_PATH = f"blob/v{__version__}/"
SRC_WIDGETS_URL = SRC_BASE_URL + SRC_VERSION_PATH + "src/textual/widgets/"


@dataclass(frozen=True)
class WidgetDetails:
    docs_url: str
    source_url: str
    base_classes: list[str]
    module_widgets: list[str]
    default_css: str


_WIDGET_DETAILS_CACHE: dict[str, WidgetDetails] = {}


def get_widget_details(widget_class: str) -> WidgetDetails:
    if widget_class not in _WIDGET_DETAILS_CACHE:
        widget_snake_case = camel_to_snake(widget_class)

        docs_url = DOCS_WIDGETS_URL + widget_snake_case
        source_url = SRC_WIDGETS_URL + f"_{widget_snake_case}.py"

        module_path = f"._{widget_snake_case}"
        module = import_module(module_path, package="textual.widgets")
        class_ = getattr(module, widget_class)

        raw_default_css = class_.DEFAULT_CSS
        default_css = dedent(raw_default_css).strip()

        module_widgets: list[str] = []
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and issubclass(obj, Widget)
                and obj.__module__ == module.__name__
            ):
                module_widgets.append(name)

        base_classes: list[str] = []
        while True:
            base_classes.append(class_.__name__)
            for base in class_.__bases__:
                if issubclass(base, DOMNode):
                    class_ = base
                    break
            else:
                break

        base_classes.reverse()

        _WIDGET_DETAILS_CACHE[widget_class] = WidgetDetails(
            docs_url=docs_url,
            source_url=source_url,
            base_classes=base_classes,
            module_widgets=module_widgets,
            default_css=default_css,
        )

    return _WIDGET_DETAILS_CACHE[widget_class]


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
        super().__init__(text=DOCS_BASE_URL, url=DOCS_BASE_URL)

    def watch_widget_class(self, widget_class: str) -> None:
        widget_details = get_widget_details(widget_class)
        self.text = widget_details.docs_url
        self.url = widget_details.docs_url


class SourceCodeLink(Link):
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
        super().__init__(text=SRC_WIDGETS_URL, url=SRC_WIDGETS_URL)

    def watch_widget_class(self, widget_class: str) -> None:
        widget_details = get_widget_details(widget_class)
        self.text = widget_details.source_url
        self.url = widget_details.source_url


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

        widget_details = get_widget_details(widget_class)
        base_classes = widget_details.base_classes
        widget = self.root.add(base_classes[1], expand=True, allow_expand=False)
        for class_ in base_classes[2:]:
            widget = widget.add(class_, expand=True, allow_expand=False)

        self.cursor_line = self.last_line


class ModuleWidgetsList(OptionList):
    DEFAULT_CSS = """
    ModuleWidgetsList {
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

    def watch_widget_class(self, widget_class: str) -> None:
        self.clear_options()
        widget_details = get_widget_details(widget_class)
        self.add_options(
            [Option(widget, id=widget) for widget in widget_details.module_widgets]
        )


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
        widget_details = get_widget_details(widget_class)
        self.load_text(widget_details.default_css)


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

        module_widgets_list = ModuleWidgetsList()
        module_widgets_list.data_bind(TextualDissectApp.widget_class)
        module_widgets_list.border_title = "Module Widgets"

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
        with HorizontalGroup():
            yield inheritance_tree
            yield module_widgets_list
        yield default_css_view

    # NOTE: The CSS selector is needed in the `on` decorator below to
    # workaround a footgun in Textual where the event handler doesn't
    # differentiate the subclass from its parent widget.
    # https://github.com/Textualize/textual/issues/4968
    @on(WidgetsList.OptionHighlighted, "WidgetsList")
    def on_widgets_list_option_highlighted(
        self, event: WidgetsList.OptionHighlighted
    ) -> None:
        widget_class = event.option_id
        assert widget_class is not None
        self.widget_class = widget_class


def run() -> None:
    app = TextualDissectApp()
    app.run()
