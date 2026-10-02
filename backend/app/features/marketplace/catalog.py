"""Built-in list of service areas used for "type to suggest" pickers (onboarding, interests, profile services)."""

SERVICE_CATALOG = [
    "Health insurance", "Life insurance", "Term insurance", "Motor insurance", "Travel insurance", "Home insurance",
    "Insurance claims help", "Employee benefits", "Mutual funds", "Financial planning", "Retirement planning",
    "Tax filing", "GST & accounting", "Loans & mortgages", "Stock market advice", "Real estate buying",
    "Property rental", "Property legal check", "Home interior design", "Architecture", "Construction & renovation",
    "Solar installation", "Legal advice", "Family law", "Company registration", "Trademark & IP",
    "Digital marketing", "Social media marketing", "SEO", "Content writing", "Branding & graphic design",
    "Website development", "Mobile app development", "IT services", "Cloud & DevOps", "Cybersecurity", "Data & AI",
    "Human resources", "Recruitment", "Payroll", "Career coaching", "Education counselling", "Study abroad",
    "Tuition & coaching", "Language classes", "Fashion design", "Fashion styling", "Boutique & tailoring",
    "Beauty & fashion", "Beauty & wellness", "Beauty salon", "Bridal makeup", "Skin care", "Hair care",
    "Fitness training", "Yoga", "Nutrition & diet", "Mental health counselling", "Doctor consultation", "Dental care",
    "Wedding planning", "Event management", "Photography", "Videography", "Travel planning", "Visa & immigration",
    "Car buying", "Car service & repair", "Home cleaning", "Pest control", "Plumbing", "Electrical work", "Pet care",
]


def suggest(query: str, extra: list[str], limit: int = 8) -> list[str]:
    """Names starting with (or whose words start with) the query first, then any containing it."""
    needle = query.strip().lower()
    if not needle:
        return SERVICE_CATALOG[:limit]
    names = list({name.lower(): name for name in [*SERVICE_CATALOG, *extra]}.values())

    def rank(name: str) -> int:
        lowered = name.lower()
        if lowered.startswith(needle):
            return 0
        if any(word.startswith(needle) for word in lowered.replace("&", " ").split()):
            return 1
        return 2

    matches = [name for name in names if needle in name.lower()]
    return sorted(matches, key=lambda name: (rank(name), len(name)))[:limit]
