"""Document helpers for chapters 12, 13, 15 and 16: OCR with Azure AI Vision Read, Document Intelligence and Content Understanding.

All three are Foundry Tools on the SAME Foundry resource: one endpoint (STARK_ACCOUNT_ENDPOINT), Entra ID auth, no keys.
Your identity needs the *Cognitive Services User* role on the resource (rbac.bicep assigns it).
"""
from __future__ import annotations

from pathlib import Path

from stark_helpers import ROOT, cfg, credential


def resolve(path: str | Path) -> Path:
    """Accept absolute paths or paths relative to the repository root."""
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


# ---------------------------------------------------------------- Azure AI Vision: Read (OCR for images)
def vision_client():
    from azure.ai.vision.imageanalysis import ImageAnalysisClient
    return ImageAnalysisClient(endpoint=cfg("STARK_ACCOUNT_ENDPOINT"), credential=credential())


def vision_read(path: str | Path) -> list[dict]:
    """OCR an image with the Vision Read feature. Returns lines: text, polygon [(x, y)...], word confidences."""
    from azure.ai.vision.imageanalysis.models import VisualFeatures
    result = vision_client().analyze(image_data=resolve(path).read_bytes(), visual_features=[VisualFeatures.READ])
    lines = []
    for block in (result.read.blocks if result.read else []):
        for line in block.lines:
            lines.append({
                "text": line.text,
                "polygon": [(p.x, p.y) for p in line.bounding_polygon],
                "confidence": round(sum(w.confidence for w in line.words) / max(len(line.words), 1), 3),
            })
    return lines


# ---------------------------------------------------------------- Azure Document Intelligence
def di_client():
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    return DocumentIntelligenceClient(endpoint=cfg("STARK_ACCOUNT_ENDPOINT"), credential=credential())


def di_analyze(model_id: str, path: str | Path, **kwargs):
    """Run a Document Intelligence model (prebuilt-read, prebuilt-layout, prebuilt-invoice, prebuilt-receipt, ...)."""
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
    poller = di_client().begin_analyze_document(model_id, AnalyzeDocumentRequest(bytes_source=resolve(path).read_bytes()), **kwargs)
    return poller.result()


def field_value(field):
    """The typed value of a Document Intelligence field (string, date, number, currency amount) or its raw content."""
    if field is None:
        return None
    for key in ("valueString", "valueDate", "valueNumber", "valueInteger"):
        if field.get(key) is not None:
            return str(field.get(key)) if key == "valueDate" else field.get(key)
    currency = field.get("valueCurrency")
    if currency:
        return currency.get("amount")
    return field.get("content")


def extract_invoice(path: str | Path) -> dict:
    """Invoice fields with confidences, normalised to plain Python (the tool the agents in chapters 13-16 call)."""
    result = di_analyze("prebuilt-invoice", path)
    if not result.documents:
        return {"error": "no invoice found in the document"}
    doc = result.documents[0]
    f = doc.fields or {}
    items = []
    for item in ((f.get("Items") or {}).get("valueArray") or []):
        obj = item.get("valueObject") or {}
        items.append({k.lower(): field_value(obj.get(k)) for k in ("Description", "Quantity", "UnitPrice", "Amount")})
    keys = ["VendorName", "InvoiceId", "InvoiceDate", "DueDate", "PurchaseOrder", "SubTotal", "TotalTax", "InvoiceTotal", "CustomerName"]
    return {
        "fields": {k: field_value(f.get(k)) for k in keys},
        "confidence": {k: round(f[k].get("confidence") or 0, 2) for k in keys if f.get(k)},
        "items": items,
    }


# ---------------------------------------------------------------- Azure Content Understanding
def cu_client():
    from azure.ai.contentunderstanding import ContentUnderstandingClient
    return ContentUnderstandingClient(endpoint=cfg("STARK_ACCOUNT_ENDPOINT"), credential=credential())


def cu_analyze(analyzer_id: str, path: str | Path):
    """Analyze a document with a (prebuilt or custom) Content Understanding analyzer; returns the AnalysisResult."""
    data = resolve(path).read_bytes()
    client = cu_client()
    try:
        poller = client.begin_analyze_binary(analyzer_id=analyzer_id, binary_input=data)
    except AttributeError:   # older/newer SDKs: fall back to the generic input shape
        from azure.ai.contentunderstanding.models import AnalysisInput
        poller = client.begin_analyze(analyzer_id=analyzer_id, inputs=[AnalysisInput(data=data)])
    return poller.result()


def cu_fields(result) -> list[dict]:
    """Flatten the top-level fields of the first content block: name, value, confidence."""
    content = result.contents[0] if result.contents else None
    rows = []
    for name, fld in ((content.fields or {}).items() if content else []):
        rows.append({"field": name, "value": getattr(fld, "value", None), "confidence": getattr(fld, "confidence", None)})
    return rows
