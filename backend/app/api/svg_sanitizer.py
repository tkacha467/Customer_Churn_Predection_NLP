"""
Enterprise Hardened SVG Sanitizer Module for VRAJA AI Multi-Tenant SaaS Platform.
Guards against:
- Stored Cross-Site Scripting (Stored XSS)
- CSS escape sequence and comment obfuscation bypasses
- XML External Entity (XXE) injection
- XML Entity Expansion (Billion Laughs / quadratic blowup)
- Nested SVG / HTML / JS data URI attacks
- SMIL and SVG animation / scripting execution (<animate>, <set>)
- XML Processing Instruction injections
- Excessive nesting and element count denial of service
- Server-Side Request Forgery (SSRF) and external tracking
"""

import base64
import binascii
import hashlib
import re
from typing import Set, Optional
import xml.etree.ElementTree as std_ET

import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException, DTDForbidden, EntitiesForbidden

# Limits
MAX_SVG_SIZE_BYTES = 2 * 1024 * 1024       # 2 MiB raw upload limit
MAX_DATA_URI_SIZE_BYTES = 500 * 1024       # 500 KiB embedded raster limit
MAX_ELEMENT_COUNT = 2000                   # Max elements per SVG
MAX_ELEMENT_DEPTH = 30                     # Max XML tree nesting depth

# Allowed raster image MIME types in data URIs
ALLOWED_RASTER_MIMES = {
    "image/png",
    "image/jpeg",
    "image/webp",
}

# Standard XML / SVG Namespaces
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"

std_ET.register_namespace("", SVG_NAMESPACE)
std_ET.register_namespace("xlink", XLINK_NAMESPACE)

# Explicit SVG element allowlist for safe, static logos
ALLOWED_ELEMENTS: Set[str] = {
    "svg",
    "g",
    "defs",
    "clippath",
    "mask",
    "pattern",
    "title",
    "desc",
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "lineargradient",
    "radialgradient",
    "stop",
    "filter",
    "fedropshadow",
    "fegaussianblur",
    "feoffset",
    "feblend",
    "fecolormatrix",
    "femerge",
    "femergenode",
    "feflood",
    "fecomposite",
    "femorphology",
    "text",
    "tspan",
    "style",
    "symbol",
    "use",
    "image",
}

# Elements that must be rejected outright due to active content, animation, or security risk
FORBIDDEN_ELEMENTS: Set[str] = {
    # Active HTML & plugin containers
    "foreignobject",
    "iframe",
    "embed",
    "object",
    "applet",
    "audio",
    "video",
    "canvas",
    "link",
    "meta",
    "base",
    "form",
    "input",
    "button",
    "textarea",
    "select",
    # Scripting & animation / SMIL
    "script",
    "animate",
    "animatetransform",
    "animatemotion",
    "set",
    "discard",
    "handler",
    "listener",
    "cursor",
    # Interactive navigation & external filter sources
    "a",
    "feimage",
}

# Graphical renderable elements ensuring SVG contains real visual content
GRAPHICAL_ELEMENTS: Set[str] = {
    "path",
    "rect",
    "circle",
    "ellipse",
    "line",
    "polyline",
    "polygon",
    "text",
    "tspan",
    "image",
}

# Safe CSS property allowlist for inline style attributes and <style> blocks
SAFE_CSS_PROPERTIES: Set[str] = {
    "fill",
    "fill-opacity",
    "fill-rule",
    "stroke",
    "stroke-width",
    "stroke-linecap",
    "stroke-linejoin",
    "stroke-miterlimit",
    "stroke-dasharray",
    "stroke-dashoffset",
    "stroke-opacity",
    "opacity",
    "stop-color",
    "stop-opacity",
    "font-family",
    "font-size",
    "font-weight",
    "font-style",
    "letter-spacing",
    "text-anchor",
    "dominant-baseline",
    "display",
    "visibility",
    "clip-path",
    "mask",
    "filter",
    "transform",
    "color",
    "width",
    "height",
}

FORBIDDEN_CSS_KEYWORDS: Set[str] = {
    "expression",
    "javascript",
    "vbscript",
    "-moz-binding",
    "behavior",
    "@import",
    "@font-face",
    "@keyframes",
    "@namespace",
    "@charset",
}

# Regex to validate internal fragment ID format
VALID_ID_REF = re.compile(r"^#[a-zA-Z0-9_\-\.\:]+$")

# Regex to parse data URIs
DATA_URI_PATTERN = re.compile(
    r"^data:([^;,]+)(?:;charset=[^;,]+)?(;base64)?,(.*)$",
    re.IGNORECASE | re.DOTALL,
)


def _get_local_name(tag_or_attr: str) -> str:
    """Extracts the local tag/attribute name, stripping XML namespace prefixes."""
    return tag_or_attr.split("}")[-1].lower() if "}" in tag_or_attr else tag_or_attr.lower()


def normalize_css(css_text: str) -> str:
    """
    Normalizes CSS by removing comments and decoding CSS backslash escape sequences.
    Prevents evasion techniques such as `\\65 xpression` or `exp/*comment*/ression`.
    """
    if not css_text:
        return ""
    # 1. Strip CSS comments (/* ... */)
    no_comments = re.sub(r"/\*.*?\*/", "", css_text, flags=re.DOTALL)

    # 2. Decode hex escapes: \65 or \000065
    def decode_hex(m: re.Match) -> str:
        code = int(m.group(1), 16)
        if code == 0 or code > 0x10FFFF:
            return ""
        return chr(code)

    unescaped = re.sub(r"\\([0-9a-fA-F]{1,6})\s?", decode_hex, no_comments)

    # 3. Decode non-hex character escapes: \( -> (, \" -> ", etc.
    unescaped = re.sub(r"\\([^\r\n\f])", r"\1", unescaped)
    return unescaped


def validate_css_content(css_text: str, is_inline: bool = True) -> None:
    """
    Validates CSS rules against injection keywords, external URLs, and property allowlists.

    Raises:
        ValueError: If CSS contains forbidden keywords, external links, or unallowed properties.
    """
    normalized = normalize_css(css_text)
    lower_norm = normalized.lower()

    # Check for dangerous keywords
    for kw in FORBIDDEN_CSS_KEYWORDS:
        if kw in lower_norm:
            raise ValueError(f"SVG contains unsafe CSS: forbidden keyword or expression '{kw}'")

    # Check all url(...) occurrences: only local fragments (#id) permitted
    for url_match in re.finditer(r"url\s*\((.*?)\)", normalized, flags=re.IGNORECASE):
        raw_target = url_match.group(1).strip().strip("\"'")
        if not raw_target.startswith("#") or not VALID_ID_REF.match(raw_target):
            raise ValueError(f"SVG contains unsafe CSS: url() must reference local fragment (#), got: '{raw_target}'")

    if is_inline:
        # Validate individual declarations in inline style
        for decl in normalized.split(";"):
            decl = decl.strip()
            if not decl:
                continue
            if ":" not in decl:
                raise ValueError("Malformed CSS declaration in style attribute.")
            prop, val = decl.split(":", 1)
            prop = prop.strip().lower()
            if prop not in SAFE_CSS_PROPERTIES:
                raise ValueError(f"SVG contains unsafe CSS: unsupported property '{prop}'")
    else:
        # In <style> blocks, inspect declaration blocks inside { ... }
        for block_match in re.finditer(r"\{([^}]*)\}", normalized):
            block_content = block_match.group(1)
            for decl in block_content.split(";"):
                decl = decl.strip()
                if not decl:
                    continue
                if ":" not in decl:
                    continue
                prop, val = decl.split(":", 1)
                prop = prop.strip().lower()
                if prop not in SAFE_CSS_PROPERTIES:
                    raise ValueError(f"SVG contains unsafe CSS: unsupported property '{prop}'")


def validate_data_uri(val: str) -> None:
    """
    Strictly validates embedded data URIs.
    Only base64-encoded raster images (PNG, JPEG, WebP) with valid magic bytes are accepted.
    Nested SVG, HTML, JavaScript, and unencoded payloads are rejected.

    Raises:
        ValueError: If the data URI is malformed, uses an unapproved MIME type, or fails signature checks.
    """
    clean_val = re.sub(r"\s+", "", val)
    m = DATA_URI_PATTERN.match(clean_val)
    if not m:
        raise ValueError("Invalid or disallowed data URI format. Only base64 raster images are permitted.")

    mime_type = m.group(1).lower()
    is_base64 = bool(m.group(2))
    raw_payload = m.group(3)

    if mime_type not in ALLOWED_RASTER_MIMES:
        raise ValueError(
            f"Disallowed data URI MIME type: '{mime_type}'. Only raster images (image/png, image/jpeg, image/webp) are permitted."
        )

    if not is_base64:
        raise ValueError("Data URI must be base64-encoded.")

    try:
        decoded_bytes = base64.b64decode(raw_payload, validate=True)
    except (binascii.Error, ValueError) as e:
        raise ValueError("Malformed base64 payload in data URI.") from e

    if len(decoded_bytes) > MAX_DATA_URI_SIZE_BYTES:
        raise ValueError(
            f"Embedded data URI payload ({len(decoded_bytes)} bytes) exceeds maximum limit of 500 KiB."
        )

    # Magic byte verification
    if mime_type == "image/png" and not decoded_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("Data URI declared image/png but file header signature is invalid.")
    elif mime_type == "image/jpeg" and not decoded_bytes.startswith(b"\xff\xd8\xff"):
        raise ValueError("Data URI declared image/jpeg but file header signature is invalid.")
    elif mime_type == "image/webp":
        if not (decoded_bytes.startswith(b"RIFF") and len(decoded_bytes) >= 12 and decoded_bytes[8:12] == b"WEBP"):
            raise ValueError("Data URI declared image/webp but file header signature is invalid.")


def _enforce_structure_limits(elem: std_ET.Element, current_depth: int = 1, counter: Optional[list] = None) -> None:
    """Recursively validates maximum nesting depth and element counts to prevent DoS."""
    if counter is None:
        counter = [0]
    counter[0] += 1

    if counter[0] > MAX_ELEMENT_COUNT:
        raise ValueError(f"SVG exceeds maximum permitted XML element count ({MAX_ELEMENT_COUNT}).")

    if current_depth > MAX_ELEMENT_DEPTH:
        raise ValueError(f"SVG exceeds maximum permitted XML element nesting depth ({MAX_ELEMENT_DEPTH}).")

    for child in elem:
        _enforce_structure_limits(child, current_depth + 1, counter)


def sanitize_svg(raw_content: bytes) -> bytes:
    """
    Sanitizes raw SVG byte content and returns safe, standardized XML bytes.

    Audited Security Guarantees:
    - Enforces 2 MiB file size ceiling before parsing.
    - Prohibits all XML DTD declarations and external entities (XXE).
    - Blocks recursive entity expansion (Billion Laughs / quadratic blowup).
    - Prohibits XML Processing Instructions (e.g. <?xml-stylesheet ...?>).
    - Enforces element count (<= 2,000) and tree depth limits (<= 30) against DoS.
    - Rejects unsupported active/animated elements (<animate>, <set>, <foreignObject>, <a>, etc.).
    - Strips all <script> elements and inline on* event handler attributes.
    - Normalizes CSS and strictly validates properties, preventing escape/comment bypasses.
    - Strictly restricts data: URIs to validated base64 PNG/JPEG/WebP payloads; rejects nested SVG/HTML.
    - Prohibits dangerous URI schemes (javascript:, vbscript:, etc.).
    - Prohibits external network resource links (http:, https:, ftp:, //) to prevent SSRF and tracking.
    - Ensures valid root <svg> tag and presence of renderable graphical elements.
    - Re-validates serialized output before returning.

    Raises:
        ValueError: If the SVG is malformed, prohibited, or fails security validation.
    """
    if not raw_content or len(raw_content) < 10:
        raise ValueError("SVG file is empty or corrupted.")

    if len(raw_content) > MAX_SVG_SIZE_BYTES:
        raise ValueError(
            f"SVG file size ({len(raw_content)} bytes) exceeds maximum allowed limit of 2 MiB ({MAX_SVG_SIZE_BYTES} bytes)."
        )

    # Reject prohibited XML Processing Instructions (only standard <?xml ...?> at start is allowed)
    for pi_match in re.finditer(rb"<\?([a-zA-Z0-9_\-]+)", raw_content):
        pi_name = pi_match.group(1).lower()
        if pi_name != b"xml":
            raise ValueError(
                f"SVG contains prohibited XML processing instruction: <?{pi_name.decode('latin1', errors='ignore')} ...?>"
            )

    # 1. Parse with defusedxml (defense against XXE and Billion Laughs)
    try:
        root = ET.fromstring(
            raw_content,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except (DefusedXmlException, DTDForbidden, EntitiesForbidden) as e:
        raise ValueError("XML external entities and DTD declarations are forbidden in SVG uploads.") from e
    except Exception as e:
        raise ValueError("Malformed or unparseable SVG XML content.") from e

    root_tag = _get_local_name(root.tag)
    if root_tag != "svg":
        raise ValueError(f"Root element of SVG must be <svg>, got <{root_tag}>.")

    # 2. Enforce element count and nesting depth limits
    _enforce_structure_limits(root)

    # 3. Build parent map for safe node removals
    parent_map = {c: p for p in root.iter() for c in p}
    elements_to_remove = []

    # 4. Inspect all elements and attributes
    for elem in list(root.iter()):
        if not isinstance(elem.tag, str):
            continue

        # Enforce SVG namespace
        if "}" in elem.tag:
            ns = elem.tag.split("}")[0].lstrip("{").lower()
            if ns not in (SVG_NAMESPACE, ""):
                raise ValueError(f"SVG contains prohibited element namespace: '{ns}'")

        local_tag = _get_local_name(elem.tag)

        # Reject forbidden active or animated elements immediately
        if local_tag in FORBIDDEN_ELEMENTS:
            if local_tag == "script":
                # Strip script elements
                parent = parent_map.get(elem)
                if parent is not None:
                    elements_to_remove.append((parent, elem))
                continue
            raise ValueError(f"SVG contains forbidden active element: <{local_tag}>")

        # Inspect and validate attributes across all elements
        for k in list(elem.attrib.keys()):
            attr_name = _get_local_name(k)
            val = elem.attrib[k]

            # Strip inline event handlers (onload, onclick, onbegin, etc.)
            if attr_name.startswith("on"):
                del elem.attrib[k]
                continue

            # Validate style attributes with CSS unescape and allowlist
            if attr_name == "style":
                validate_css_content(val, is_inline=True)
                continue

            # Inspect URI schemes and references
            normalized_val = normalize_css(val)
            clean_val = re.sub(r"[\s\x00-\x1f\x7f]+", "", normalized_val).lower()

            if (
                "javascript:" in clean_val
                or "vbscript:" in clean_val
                or "data:text/html" in clean_val
                or "data:application/javascript" in clean_val
            ):
                raise ValueError("SVG contains dangerous URI scheme (javascript:).")

            if attr_name in ("href", "src") or k.endswith("href"):
                if clean_val.startswith(("http:", "https:", "ftp:", "//")):
                    raise ValueError(f"SVG contains forbidden external resource reference: {val}")

                if clean_val.startswith("data:"):
                    if local_tag != "image":
                        raise ValueError(f"Data URIs are only permitted on <image> elements, not <{local_tag}>.")
                    validate_data_uri(val)
                elif local_tag in ("use", "lineargradient", "radialgradient", "pattern", "clippath", "filter"):
                    if not VALID_ID_REF.match(val.strip()):
                        raise ValueError(f"SVG <{local_tag}> {attr_name} must reference a local fragment ID (#id), got: '{val}'")

        # Strip unallowed elements
        if local_tag not in ALLOWED_ELEMENTS:
            parent = parent_map.get(elem)
            if parent is not None:
                elements_to_remove.append((parent, elem))
            continue

        # Inspect <style> elements for dangerous CSS
        if local_tag == "style" and elem.text:
            validate_css_content(elem.text, is_inline=False)

    # Remove stripped elements
    for parent, child in elements_to_remove:
        try:
            parent.remove(child)
        except ValueError:
            pass

    # 5. Verify presence of legitimate renderable graphical content
    has_graphics = any(
        isinstance(elem.tag, str) and _get_local_name(elem.tag) in GRAPHICAL_ELEMENTS
        for elem in root.iter()
    )
    if not has_graphics:
        raise ValueError("SVG contains no valid renderable graphical content after sanitization.")

    # 6. Serialize to standardized XML
    try:
        serialized = std_ET.tostring(root, encoding="utf-8")
        # Validate that output re-parses cleanly through defusedxml
        ET.fromstring(serialized, forbid_dtd=True, forbid_entities=True, forbid_external=True)
    except Exception as e:
        raise ValueError("Failed to serialize sanitized SVG XML.") from e

    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + serialized
