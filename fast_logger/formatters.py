import json
from typing import Any

try:
    from rich.json import JSON
    from rich.syntax import Syntax
    from rich.console import Console

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def format_sql(query: str) -> Any:
    """
    Format SQL queries. If rich is available, returns a Syntax object for syntax highlighting.
    Otherwise, returns the query string.
    """
    if RICH_AVAILABLE:
        # A simple normalization before highlighting
        query = " ".join(query.split())
        return Syntax(query, "sql", theme="monokai", word_wrap=True)
    return query


def format_json(data: dict[str, Any]) -> Any:
    """
    Format JSON dictionaries. If rich is available, returns a rich JSON object.
    Otherwise, returns an indented JSON string.
    """
    if RICH_AVAILABLE:
        # rich.json.JSON requires a string
        return JSON(json.dumps(data))
    return json.dumps(data, indent=2)


def format_http(req_resp: Any) -> Any:
    """
    Takes an HTTP payload, dict, or standard object (like requests.Response or httpx.Response)
    and formats it into a readable structure.
    """
    # Check if it's a httpx or requests Response
    if hasattr(req_resp, "status_code") and hasattr(req_resp, "text"):
        method = (
            getattr(req_resp.request, "method", "GET")
            if hasattr(req_resp, "request")
            else "UNKNOWN"
        )
        url = getattr(req_resp, "url", "UNKNOWN")
        status = req_resp.status_code

        headers = dict(getattr(req_resp, "headers", {}))

        header_str = "\n".join(f"{k}: {v}" for k, v in headers.items())

        formatted = f"HTTP {status} | {method} {url}\n\nHeaders:\n{header_str}\n\nBody:\n{req_resp.text}"

        if RICH_AVAILABLE:
            from rich.panel import Panel

            return Panel(formatted, title="HTTP Response", expand=False)
        return formatted

    # If it's a dict holding request data
    if isinstance(req_resp, dict):
        if RICH_AVAILABLE:
            from rich.panel import Panel

            return Panel(format_json(req_resp), title="HTTP Payload", expand=False)
        return format_json(req_resp)

    return str(req_resp)


def format_inspect(obj: Any) -> Any:
    """
    Format object introspection beautifully, categorizing properties and methods.
    """
    class_name = obj.__class__.__name__
    properties = []
    methods = []

    for attr_name in dir(obj):
        if attr_name.startswith("_"):
            continue
        try:
            attr_value = getattr(obj, attr_name)
            if callable(attr_value):
                methods.append(attr_name)
            else:
                properties.append((attr_name, attr_value))
        except Exception:
            pass

    if RICH_AVAILABLE:
        from rich.console import Group
        from rich.text import Text
        from rich.table import Table
        from rich.panel import Panel

        items: list[Any] = [Text(class_name, style="bold cyan")]

        if properties:
            prop_table = Table(show_header=False, box=None, padding=(0, 2))
            for k, v in properties:
                prop_table.add_row(Text(k, style="bold yellow"), str(v))
            items.append(prop_table)

        if methods:
            items.append(Text("\nMethods", style="bold magenta"))
            meth_table = Table(show_header=False, box=None, padding=(0, 2))
            for m in methods:
                meth_table.add_row(Text(f"{m}()", style="green"))
            items.append(meth_table)

        return Panel(Group(*items), border_style="blue", expand=False)

    out = [f"{class_name}"]
    for k, v in properties:
        out.append(f"{k}\n{v}")
    if methods:
        out.append("\nMethods")
        for m in methods:
            out.append(f"{m}()")
    return "\n".join(out)


def format_diff(old: Any, new: Any) -> Any:
    """
    Format a diff of two dictionaries or strings.
    Supports nested dictionary differences natively.
    """
    if isinstance(old, dict) and isinstance(new, dict):

        def _dict_diff(
            d1: dict[Any, Any], d2: dict[Any, Any], path: str = ""
        ) -> list[tuple[str, str, Any]]:
            diffs = []
            for k in d1:
                p = f"{path}.{k}" if path else str(k)
                if k not in d2:
                    diffs.append((p, "Removed", d1[k]))
                elif isinstance(d1[k], dict) and isinstance(d2[k], dict):
                    diffs.extend(_dict_diff(d1[k], d2[k], p))
                elif d1[k] != d2[k]:
                    diffs.append((p, "Changed", (d1[k], d2[k])))
            for k in d2:
                p = f"{path}.{k}" if path else str(k)
                if k not in d1:
                    diffs.append((p, "Added", d2[k]))
            return diffs

        diffs = _dict_diff(old, new)

        if not diffs:
            return "No differences found."

        if RICH_AVAILABLE:
            from rich.table import Table
            from rich.text import Text

            table = Table(title="Differences", show_lines=True)
            table.add_column("Key Path", style="cyan")
            table.add_column("Status", style="bold")
            table.add_column("Value / Change")

            for path, status, val in diffs:
                if status == "Added":
                    table.add_row(path, Text("Added", style="bold green"), str(val))
                elif status == "Removed":
                    table.add_row(path, Text("Removed", style="bold red"), str(val))
                else:  # Changed
                    old_v, new_v = val
                    table.add_row(
                        path,
                        Text("Changed", style="bold yellow"),
                        f"{old_v} -> {new_v}",
                    )
            return table

        else:
            lines = ["Differences:"]
            for path, status, val in diffs:
                if status == "Changed":
                    lines.append(f"  {status} {path}: {val[0]} -> {val[1]}")
                else:
                    lines.append(f"  {status} {path}: {val}")
            return "\n".join(lines)

    # Fallback to string diff
    import pprint
    import difflib

    old_str = pprint.pformat(old) if not isinstance(old, str) else old
    new_str = pprint.pformat(new) if not isinstance(new, str) else new

    if RICH_AVAILABLE:
        from rich.text import Text

        differ = difflib.ndiff(old_str.splitlines(), new_str.splitlines())
        text = Text()
        for line in differ:
            if line.startswith("- "):
                text.append(line + "\n", style="red")
            elif line.startswith("+ "):
                text.append(line + "\n", style="green")
            elif line.startswith("? "):
                text.append(line + "\n", style="yellow")
            else:
                text.append(line + "\n", style="dim")
        return text
    else:
        differ = difflib.ndiff(old_str.splitlines(), new_str.splitlines())
        return "\n".join(differ)
