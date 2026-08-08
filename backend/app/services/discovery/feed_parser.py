import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional


@dataclass
class ParsedFeedItem:
    title: str
    description: str
    source_url: str
    published_at: str


def clean_text(text: Optional[str]) -> str:
    """Strip HTML tags, unescape entities, and normalize whitespace."""
    if not text:
        return ""
    # Strip HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def parse_timestamp(raw_date: Optional[str]) -> str:
    """Parse various RFC-822 or ISO-8601 timestamps to UTC ISO-8601 string."""
    if not raw_date or not raw_date.strip():
        return datetime.now(timezone.utc).isoformat()

    raw_date = raw_date.strip()

    # Try RFC 822 / RFC 2822 (common in RSS)
    try:
        dt = parsedate_to_datetime(raw_date)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    # Try ISO 8601 (common in Atom)
    try:
        dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass

    return datetime.now(timezone.utc).isoformat()


def get_local_tag(elem: ET.Element) -> str:
    """Get tag name without XML namespace."""
    return elem.tag.rsplit("}", 1)[-1] if "}" in elem.tag else elem.tag


def find_child_text(elem: ET.Element, target_local_name: str) -> Optional[str]:
    """Find text of a child element matching a local tag name regardless of namespace."""
    for child in elem:
        if get_local_tag(child) == target_local_name:
            return child.text
    return None


def find_child_elem(elem: ET.Element, target_local_name: str) -> Optional[ET.Element]:
    """Find child element matching a local tag name regardless of namespace."""
    for child in elem:
        if get_local_tag(child) == target_local_name:
            return child
    return None


def parse_rss_item(item_elem: ET.Element) -> Optional[ParsedFeedItem]:
    """Parse a single RSS <item> element."""
    title = clean_text(find_child_text(item_elem, "title"))
    description = clean_text(
        find_child_text(item_elem, "description")
        or find_child_text(item_elem, "encoded")
        or find_child_text(item_elem, "summary")
    )
    
    # Extract link
    link_elem = find_child_elem(item_elem, "link")
    source_url = ""
    if link_elem is not None:
        source_url = (link_elem.text or link_elem.attrib.get("href", "")).strip()

    if not source_url:
        guid_elem = find_child_elem(item_elem, "guid")
        if guid_elem is not None and guid_elem.text and guid_elem.text.startswith("http"):
            source_url = guid_elem.text.strip()

    raw_date = (
        find_child_text(item_elem, "pubDate")
        or find_child_text(item_elem, "date")
        or find_child_text(item_elem, "published")
    )
    published_at = parse_timestamp(raw_date)

    if not title or not source_url:
        return None

    return ParsedFeedItem(
        title=title,
        description=description,
        source_url=source_url,
        published_at=published_at,
    )


def parse_atom_entry(entry_elem: ET.Element) -> Optional[ParsedFeedItem]:
    """Parse a single Atom <entry> element."""
    title = clean_text(find_child_text(entry_elem, "title"))
    description = clean_text(
        find_child_text(entry_elem, "summary")
        or find_child_text(entry_elem, "content")
    )

    # Extract link (Atom uses <link href="..." rel="alternate"/> or <link href="..."/>)
    source_url = ""
    for child in entry_elem:
        if get_local_tag(child) == "link":
            href = child.attrib.get("href", "")
            rel = child.attrib.get("rel", "alternate")
            if href and rel in ("alternate", ""):
                source_url = href.strip()
                break
            elif href and not source_url:
                source_url = href.strip()

    if not source_url:
        id_elem = find_child_elem(entry_elem, "id")
        if id_elem is not None and id_elem.text and id_elem.text.startswith("http"):
            source_url = id_elem.text.strip()

    raw_date = (
        find_child_text(entry_elem, "published")
        or find_child_text(entry_elem, "updated")
    )
    published_at = parse_timestamp(raw_date)

    if not title or not source_url:
        return None

    return ParsedFeedItem(
        title=title,
        description=description,
        source_url=source_url,
        published_at=published_at,
    )


def parse_feed_xml(xml_content: str) -> List[ParsedFeedItem]:
    """
    Parse raw RSS or Atom XML content into a list of ParsedFeedItem objects.
    Handles malformed XML gracefully without raising exceptions.
    """
    if not xml_content or not xml_content.strip():
        return []

    try:
        root = ET.fromstring(xml_content.strip())
    except ET.ParseError:
        return []

    items: List[ParsedFeedItem] = []
    root_tag = get_local_tag(root)

    if root_tag == "rss" or root_tag == "channel":
        # Find channel if root is rss
        channel = root if root_tag == "channel" else find_child_elem(root, "channel")
        target_container = channel if channel is not None else root
        for child in target_container:
            if get_local_tag(child) == "item":
                parsed = parse_rss_item(child)
                if parsed:
                    items.append(parsed)

    elif root_tag == "feed":
        # Atom feed
        for child in root:
            if get_local_tag(child) == "entry":
                parsed = parse_atom_entry(child)
                if parsed:
                    items.append(parsed)

    else:
        # Generic search for item or entry tags
        for elem in root.iter():
            local_tag = get_local_tag(elem)
            if local_tag == "item":
                parsed = parse_rss_item(elem)
                if parsed:
                    items.append(parsed)
            elif local_tag == "entry":
                parsed = parse_atom_entry(elem)
                if parsed:
                    items.append(parsed)

    return items
