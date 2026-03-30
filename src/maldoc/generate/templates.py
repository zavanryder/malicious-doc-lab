"""Benign-looking document templates."""

TEMPLATES: dict[str, dict] = {
    "memo": {
        "title": "Internal Memo — Q4 Planning",
        "body": (
            "Team,\n\n"
            "Please review the attached Q4 planning materials before our next sync. "
            "Key topics include budget allocation, headcount planning, and project "
            "prioritization for the upcoming quarter.\n\n"
            "Action items from last meeting have been incorporated into the appendix. "
            "Please flag any concerns by end of week.\n\n"
            "Best regards,\nOperations Team"
        ),
        "style": "corporate",
    },
    "report": {
        "title": "Annual Security Assessment Report",
        "body": (
            "Executive Summary\n\n"
            "This report presents findings from our annual security assessment "
            "conducted between January and March 2025. The assessment covered "
            "network infrastructure, application security, and access controls.\n\n"
            "Overall risk posture has improved compared to the previous year, "
            "with 23 findings remediated and 4 new findings identified. "
            "Detailed findings are presented in the sections below.\n\n"
            "Recommendations are prioritized by severity and estimated remediation effort."
        ),
        "style": "formal",
    },
    "invoice": {
        "title": "Invoice #2025-0847",
        "body": (
            "Bill To: Acme Corporation\n"
            "Date: 2025-03-15\n"
            "Due Date: 2025-04-15\n\n"
            "Services Rendered:\n"
            "  - Consulting services (40 hours) ........... $8,000.00\n"
            "  - Infrastructure review .................... $2,500.00\n"
            "  - Documentation and training ............... $1,500.00\n\n"
            "Subtotal: $12,000.00\n"
            "Tax (8%): $960.00\n"
            "Total Due: $12,960.00\n\n"
            "Payment terms: Net 30"
        ),
        "style": "business",
    },
}


def get_template(name: str) -> dict:
    """Get a document template by name."""
    template = TEMPLATES.get(name)
    if template is None:
        available = ", ".join(TEMPLATES.keys())
        raise ValueError(f"Unknown template '{name}'. Available: {available}")
    return template


def list_templates() -> list[str]:
    """Return list of available template names."""
    return list(TEMPLATES.keys())
