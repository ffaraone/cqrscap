import threading

from datetime import datetime

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable, Tree
from cqrscap.consumer import CQRSConsumer
import ujson
from textual.widgets.tree import TreeNode
from rich.text import Text


class CapturerApp(App):
    """A Textual app to manage stopwatches."""

    CSS_PATH = 'capturer.css'

    def __init__(self, cqrs_ids, hostname, port, username, password, exchange_name) -> None:
        super().__init__()
        self.data = {}
        self.consumer = CQRSConsumer(
            cqrs_ids,
            hostname,
            port,
            username,
            password,
            exchange_name,
            self.on_cqrs_message,
        )
        self.consumer_thread = threading.Thread(target=self.consumer.run)


    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("e", "expand_all", "Expand all nodes"),
        ("c", "collapse_all", "Collapse all nodes"),
        ("r", "reset", "Clear all cqrs messages"),
        ("q", "quit", "Quit"),
    ]

    # def run(self, *args, **kwargs):
    #     exit_code = super().run(*args, **kwargs)
    #     self.consumer.should_stop = True
    #     self.consumer_thread.join()
    #     return exit_code

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield DataTable()
        yield Tree("{}")
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark

    def action_expand_all(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand_all()

    def action_collapse_all(self) -> None:
        tree = self.query_one(Tree)
        tree.root.collapse_all()

    def action_reset(self) -> None:
        table = self.query_one(DataTable)
        table.clear()
        tree = self.query_one(Tree)
        tree.reset('{}')
        self.data = {}

    def action_quit(self) -> None:
        self.consumer.stop()
        self.consumer_thread.join()
        self.exit()


    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns('cqrs updated', 'signal type', 'cqrs id', 'instance id', 'cqrs revision')
        table.cursor_type = 'row'
        self.consumer_thread.start()
        
    def on_cqrs_message(self, message):

        table = self.query_one(DataTable)
        row_key = table.add_row(
            message['instance_data']['cqrs_updated'],
            message['signal_type'],
            message['cqrs_id'],
            message['instance_pk'],
            message['instance_data']['cqrs_revision'],

        )
        self.data[row_key] = message
        if table.row_count == 1:
            tree = self.query_one(Tree)
            tree.clear()
            self.add_json(tree.root, message)
            tree.root.expand()

    @classmethod
    def node_label(cls, json_data):
        return f"{json_data['cqrs_id']} {json_data['instance_pk']} r{json_data['instance_data']['cqrs_revision']}"

    @classmethod
    def add_json(cls, node: TreeNode, json_data: object) -> None:
        """Adds JSON data to a node.

        Args:
            node (TreeNode): A Tree node.
            json_data (object): An object decoded from JSON.
        """

        from rich.highlighter import ReprHighlighter

        highlighter = ReprHighlighter()

        def add_node(name: str, node: TreeNode, data: object) -> None:
            """Adds a node to the tree.

            Args:
                name (str): Name of the node.
                node (TreeNode): Parent node.
                data (object): Data associated with the node.
            """
            if isinstance(data, dict):
                node._label = Text(f"{{}} {name}")
                for key, value in data.items():
                    new_node = node.add("")
                    add_node(key, new_node, value)
            elif isinstance(data, list):
                node._label = Text(f"[] {name}")
                for index, value in enumerate(data):
                    new_node = node.add("")
                    add_node(str(index), new_node, value)
            else:
                node._allow_expand = False
                if name:
                    label = Text.assemble(
                        Text.from_markup(f"[b]{name}[/b]="), highlighter(repr(data))
                    )
                else:
                    label = Text(repr(data))
                node._label = label

        add_node(cls.node_label(json_data), node, json_data)
    
    def on_data_table_row_highlighted(self, message):
        message = self.data[message.row_key]
        tree = self.query_one(Tree)
        tree.clear()
        self.add_json(tree.root, message)
        tree.root.expand()
