from __future__ import annotations

import inspect
from dataclasses import dataclass
from enum import Enum
from importlib import import_module
from textwrap import dedent

import tree_sitter_scss
from textual import __version__, on
from textual.app import App, ComposeResult
from textual.case import camel_to_snake
from textual.containers import HorizontalGroup
from textual.content import ContentType
from textual.dom import DOMNode
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import Link, OptionList, TabbedContent, TabPane, TextArea, Tree
from textual.widgets.option_list import Option
from tree_sitter import Language


class WidgetType(Enum):
    CORE_WIDGET = 1
    CONTAINER = 2
    BASE_CLASS = 3


WIDGET_CLASSES = {
    WidgetType.CORE_WIDGET: [
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
    ],
    WidgetType.CONTAINER: [
        "Container",
        "ScrollableContainer",
        "Vertical",
        "VerticalGroup",
        "VerticalScroll",
        "Horizontal",
        "HorizontalGroup",
        "HorizontalScroll",
        "Center",
        "Right",
        "Middle",
        "CenterMiddle",
        "Grid",
        "ItemGrid",
    ],
    WidgetType.BASE_CLASS: [
        "Widget",
        "ScrollView",
    ],
}

DOCS_BASE_URL = "https://textual.textualize.io/"
DOCS_WIDGETS_URL = DOCS_BASE_URL + "widgets/"
DOCS_CONTAINERS_URL = DOCS_BASE_URL + "api/containers/#textual.containers"

SRC_BASE_URL = f"https://github.com/Textualize/textual/"
SRC_VERSION_PATH = f"blob/v{__version__}/"
SRC_WIDGETS_URL = SRC_BASE_URL + SRC_VERSION_PATH + "src/textual/widgets/"
SRC_CONTAINERS_URL = SRC_BASE_URL + SRC_VERSION_PATH + "src/textual/containers.py"


@dataclass(frozen=True)
class WidgetDetails:
    docs_url: str
    source_url: str
    base_classes: list[str]
    child_widgets: list[str]
    default_css: str


_WIDGET_DETAILS_CACHE: dict[str, WidgetDetails] = {}


def get_widget_details(
    widget_class: str,
    widget_type: WidgetType,
) -> WidgetDetails:
    if widget_class not in _WIDGET_DETAILS_CACHE:
        widget_snake_case = camel_to_snake(widget_class)
        if widget_type == WidgetType.CORE_WIDGET:
            docs_url = DOCS_WIDGETS_URL + widget_snake_case

            if widget_class == "MarkdownViewer":
                # The `MarkdownViewer` is a special case as the module only
                # exports the class defined in `_markdown.py`, for some reason?
                module_path = f"._markdown"
                source_url = SRC_WIDGETS_URL + "_markdown.py"
            else:
                module_path = f"._{widget_snake_case}"
                source_url = SRC_WIDGETS_URL + f"_{widget_snake_case}.py"

            module = import_module(module_path, package="textual.widgets")

        elif widget_type == WidgetType.CONTAINER:
            module = import_module(".containers", package="textual")

            docs_url = DOCS_CONTAINERS_URL + f".{widget_class}"
            source_url = SRC_CONTAINERS_URL

        elif widget_type == WidgetType.BASE_CLASS:
            module = import_module(f".{widget_snake_case}", package="textual")

            docs_url = DOCS_BASE_URL + f"api/{widget_snake_case}"
            source_url = (
                SRC_BASE_URL + SRC_VERSION_PATH + f"src/textual/{widget_snake_case}.py"
            )

        class_ = getattr(module, widget_class)

        raw_default_css = class_.DEFAULT_CSS
        default_css = dedent(raw_default_css).strip()

        child_widgets: list[str] = []
        if widget_type != WidgetType.CONTAINER:
            for name, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, Widget)
                    and obj.__module__ == module.__name__
                    and obj != class_
                ):
                    child_widgets.append(name)

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
            child_widgets=child_widgets,
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

    def __init__(self, widget_type: WidgetType) -> None:
        super().__init__(
            *[Option(widget, id=widget) for widget in WIDGET_CLASSES[widget_type]],
        )
        self.widget_type = widget_type


class DocumentationLink(Link):
    DEFAULT_CSS = """
    DocumentationLink {
        width: 1fr;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            text-style: bold underline;
            border: solid $border;
            border-title-color: $text;
            border-title-style: bold;
        }
    }
    """

    def __init__(self) -> None:
        super().__init__(DOCS_BASE_URL, url=DOCS_BASE_URL)
        self.border_title = "Documentation"


class SourceCodeLink(Link):
    DEFAULT_CSS = """
    SourceCodeLink {
        width: 1fr;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            text-style: bold underline;
            border: solid $border;
            border-title-color: $text;
            border-title-style: bold;
        }
    }
    """

    def __init__(self) -> None:
        super().__init__(text=SRC_BASE_URL, url=SRC_BASE_URL)
        self.border_title = "Source Code"


class InheritanceTree(Tree[str]):
    DEFAULT_CSS = """
    InheritanceTree {
        height: 7;
        width: 1fr;
        background: $background;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            border: solid $border;
            border-title-color: $text;
            border-title-style: bold;
        }
    }
    """

    base_classes: var[list[str]] = var([], init=False)

    def __init__(self) -> None:
        super().__init__("DOMNode")
        self.show_root = False
        self.border_title = "Inheritance Tree"

    def watch_base_classes(self) -> None:
        assert len(self.base_classes) > 1

        self.clear()

        widget = self.root.add(
            label=self.base_classes[1],
            data=self.base_classes[1],
            expand=True,
            allow_expand=False,
        )
        for class_ in self.base_classes[2:]:
            widget = widget.add(
                label=class_, data=class_, expand=True, allow_expand=False
            )

        self.cursor_line = self.last_line


class ChildWidgetsList(OptionList):
    DEFAULT_CSS = """
    ChildWidgetsList {
        height: 7;
        width: 1fr;
        background: $background;
        border: solid $foreground 50%;
        padding: 0 1;

        &:focus {
            border: solid $border;
            border-title-color: $text;
            border-title-style: bold;
        }

        &:disabled {
            hatch: right $foreground 25%;
        }
    }
    """

    child_widgets: var[list[str]] = var([])

    def __init__(self) -> None:
        super().__init__()
        self.border_title = "Child Widgets"

    def watch_child_widgets(self) -> None:
        self.clear_options()
        self.disabled = not self.child_widgets
        self.add_options(
            [Option(widget, id=widget) for widget in self.child_widgets],
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
        background: $background;
        padding: 0 1;
        scrollbar-gutter: stable;

        &:focus {
            border: solid $border;
            border-title-color: $text;
            border-title-style: bold;
        }
    }
    """

    def __init__(self) -> None:
        super().__init__(read_only=True)
        self.border_title = "Default CSS"
        self.register_language("tcss", _TCSS_LANGUAGE, _TCSS_HIGHLIGHT_QUERY)
        self.language = "tcss"


class WidgetDetailsPane(TabPane):
    widget_details: var[WidgetDetails | None] = var(None, init=False)

    def __init__(self, title: ContentType, widget_type: WidgetType, id: str):
        super().__init__(title, id=id)
        self.widget_type = widget_type

    def compose(self) -> ComposeResult:
        yield WidgetsList(self.widget_type)

        yield DocumentationLink()
        yield SourceCodeLink()
        with HorizontalGroup():
            yield InheritanceTree()
            yield ChildWidgetsList()
        yield DefaultCSSView()

    def watch_widget_details(self, widget_details: WidgetDetails) -> None:
        assert widget_details is not None

        documentation_link = self.query_one(DocumentationLink)
        documentation_link.text = widget_details.docs_url
        documentation_link.url = widget_details.docs_url

        source_code_link = self.query_one(SourceCodeLink)
        source_code_link.text = widget_details.source_url
        source_code_link.url = widget_details.source_url

        inheritance_tree = self.query_one(InheritanceTree)
        inheritance_tree.base_classes = widget_details.base_classes

        child_widgets_list = self.query_one(ChildWidgetsList)
        child_widgets_list.child_widgets = widget_details.child_widgets

        default_css_view = self.query_one(DefaultCSSView)
        default_css_view.load_text(widget_details.default_css)

    @on(WidgetsList.OptionHighlighted, "WidgetsList")
    def on_widgets_list_option_highlighted(
        self, event: WidgetsList.OptionHighlighted
    ) -> None:
        assert isinstance(event.control, WidgetsList)
        widget_type = event.control.widget_type
        widget_class = event.option_id
        assert widget_class is not None

        self.widget_details = get_widget_details(widget_class, widget_type)


class TextualDissectApp(App):
    AUTO_FOCUS = "WidgetsList"

    def compose(self) -> ComposeResult:
        with TabbedContent():
            yield WidgetDetailsPane(
                "Core Widgets",
                WidgetType.CORE_WIDGET,
                id="core-widgets",
            )
            yield WidgetDetailsPane(
                "Containers",
                WidgetType.CONTAINER,
                id="containers",
            )
            yield WidgetDetailsPane(
                "Base Classes",
                WidgetType.BASE_CLASS,
                id="base-classes",
            )

    @on(InheritanceTree.NodeSelected, "InheritanceTree")
    def on_inheritance_tree_node_selected(
        self, event: InheritanceTree.NodeSelected
    ) -> None:
        assert isinstance(event.control, InheritanceTree)
        selected_widget = event.node.data
        assert isinstance(selected_widget, str)

        tab_pane_id: str | None = None
        for widget_type, widget_classes in WIDGET_CLASSES.items():
            if selected_widget in widget_classes:
                if widget_type == WidgetType.CORE_WIDGET:
                    tab_pane_id = "core-widgets"
                elif widget_type == WidgetType.CONTAINER:
                    tab_pane_id = "containers"
                elif widget_type == WidgetType.BASE_CLASS:
                    tab_pane_id = "base-classes"
                break

        if tab_pane_id is not None:
            tabbed_content = self.query_one(TabbedContent)
            tab_pane = tabbed_content.get_pane(tab_pane_id)

            widgets_list = tab_pane.query_one(WidgetsList)
            option_index = widgets_list.get_option_index(selected_widget)
            if (
                tabbed_content.active_pane != tab_pane
                or widgets_list.highlighted != option_index
            ):
                widgets_list.highlighted = option_index
                # Focusing the widget list will automatically switch tab
                widgets_list.focus()


def run() -> None:
    app = TextualDissectApp()
    app.run()
