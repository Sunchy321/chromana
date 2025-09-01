import os
from pathlib import Path
import toml
from typing import TypedDict, List, Optional

SHADOW_DIR = "shadow"

class Symbol(TypedDict):
    name: str
    file: str
    ligature: list[str]
    category: Optional[str]
    overflow: bool
    add_shadow: bool
    variant: dict[str, str]
    style: dict[str, str]

class Category(TypedDict):
    name: str
    display_name: str

class Example(TypedDict):
    text: str

class Config(TypedDict):
    name: str
    code: str
    version: str
    example: Optional[List[Example]]
    categories: Optional[List[Category]]
    symbols: List[Symbol]

def read_config(config_path: Path) -> Config:
    with open(config_path, "r") as f:
        raw = toml.load(f)

    example = raw.get("example")

    categories = raw.get("categories")

    if categories is not None:
        categories = [Category(**cat) for cat in categories]

    symbols: list[Symbol] = []

    for sym in raw.get("symbols", []):
        name = sym["name"]
        file = sym["file"]

        ligature = sym.get("ligature", [])

        if isinstance(ligature, str):
            ligature = [ligature]

        category = sym.get("category")
        overflow = sym.get("overflow", False)
        add_shadow = sym.get("add-shadow", False)
        variant = sym.get("variant", {})
        style = sym.get("style", {})

        if add_shadow:
            style["shadow"] = SHADOW_DIR

        symbols.append(Symbol(
            name=name,
            file=file,
            ligature=ligature,
            category=category,
            overflow=overflow,
            add_shadow=add_shadow,
            variant=variant,
            style=style
        ))

    return Config(
        name=raw.get("name", ""),
        code=raw["code"],
        version=raw["version"],
        example=example,
        categories=categories,
        symbols=symbols
    )
