"""Built-in list of service areas used for "type to suggest" pickers (onboarding, interests, profile services)."""
import re

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

# Everyday words customers type -> the service area they mean ("run ads for my shop" -> Digital marketing).
RELATED_WORDS: dict[str, list[str]] = {
    "Digital marketing": ["ads", "advertising", "advertise", "promote", "promotion", "marketing", "leads", "google ads",
                          "facebook ads", "online marketing", "more customers", "online sales", "grow business"],
    "Social media marketing": ["instagram", "facebook", "youtube", "reels", "followers", "influencer", "social media"],
    "SEO": ["seo", "google ranking", "search ranking", "website traffic", "rank on google"],
    "Website development": ["website", "web site", "online store", "ecommerce", "e-commerce", "landing page", "shopify", "wordpress"],
    "Mobile app development": ["app", "android", "ios", "mobile app", "play store"],
    "Branding & graphic design": ["logo", "branding", "poster", "graphic", "visiting card", "brochure"],
    "Content writing": ["blog", "article", "articles", "copywriting", "content"],
    "Health insurance": ["mediclaim", "medical insurance", "hospital bill", "health cover", "family floater", "cashless"],
    "Life insurance": ["life cover", "lic", "endowment", "child plan"],
    "Term insurance": ["term plan", "term cover"],
    "Motor insurance": ["car insurance", "bike insurance", "vehicle insurance", "two wheeler insurance"],
    "Insurance claims help": ["claim rejected", "claim", "claim settlement"],
    "Tax filing": ["income tax", "itr", "tax return", "tds", "tax refund", "tax notice"],
    "GST & accounting": ["gst", "bookkeeping", "accountant", "accounts", "audit", "ca"],
    "Loans & mortgages": ["loan", "home loan", "personal loan", "business loan", "emi", "mortgage"],
    "Mutual funds": ["sip", "mutual fund", "invest", "investment"],
    "Financial planning": ["savings", "wealth", "money planning", "investment plan"],
    "Retirement planning": ["retirement", "pension"],
    "Stock market advice": ["shares", "stocks", "trading", "demat"],
    "Legal advice": ["lawyer", "advocate", "court", "legal notice", "police complaint"],
    "Family law": ["divorce", "custody", "alimony", "marriage registration"],
    "Property legal check": ["property documents", "encumbrance", "title check", "patta"],
    "Company registration": ["start business", "startup", "register company", "llp", "private limited", "msme", "udyam"],
    "Trademark & IP": ["trademark", "brand name", "patent", "copyright"],
    "Real estate buying": ["buy house", "buy flat", "apartment", "plot", "land", "new home"],
    "Property rental": ["rent", "tenant", "lease", "rental agreement"],
    "Home interior design": ["interior", "modular kitchen", "wardrobe", "home decor"],
    "Construction & renovation": ["build house", "renovation", "contractor", "civil work", "house construction"],
    "Solar installation": ["solar", "solar panel", "rooftop solar"],
    "IT services": ["software", "computer", "it support", "laptop", "network"],
    "Cybersecurity": ["hacked", "hacking", "virus", "cyber"],
    "Human resources": ["hr", "hr policy", "employee issues"],
    "Recruitment": ["hiring", "hire", "staff", "candidates", "manpower"],
    "Payroll": ["salary", "pf", "esi", "payslip"],
    "Career coaching": ["job change", "resume", "cv", "interview", "career"],
    "Education counselling": ["admission", "college", "course selection"],
    "Study abroad": ["abroad", "ielts", "gre", "foreign university", "study in"],
    "Visa & immigration": ["visa", "passport", "immigration", "pr visa"],
    "Tuition & coaching": ["tuition", "tutor", "coaching", "exam preparation"],
    "Fashion design": ["dress design", "designer wear", "clothing"],
    "Boutique & tailoring": ["tailor", "stitching", "blouse", "alteration"],
    "Bridal makeup": ["bride", "wedding makeup", "makeup artist"],
    "Beauty salon": ["salon", "parlour", "parlor", "haircut", "facial", "waxing"],
    "Skin care": ["acne", "pimples", "skin", "dermatologist"],
    "Hair care": ["hair fall", "hair loss", "dandruff"],
    "Fitness training": ["gym", "personal trainer", "workout", "weight loss"],
    "Nutrition & diet": ["diet", "dietitian", "nutritionist", "weight loss", "diabetes diet"],
    "Mental health counselling": ["stress", "anxiety", "depression", "therapy", "counsellor", "therapist"],
    "Doctor consultation": ["doctor", "fever", "health checkup"],
    "Dental care": ["dentist", "tooth", "teeth", "braces"],
    "Wedding planning": ["wedding", "marriage function", "reception"],
    "Event management": ["event", "birthday party", "party", "corporate event"],
    "Photography": ["photo", "photographer", "photoshoot", "photo shoot"],
    "Videography": ["video shoot", "videographer", "drone"],
    "Travel planning": ["trip", "tour", "holiday", "honeymoon", "tour package"],
    "Car buying": ["buy car", "new car", "used car"],
    "Car service & repair": ["mechanic", "car repair", "car service", "bike repair"],
    "Home cleaning": ["cleaning", "deep cleaning", "maid", "sofa cleaning"],
    "Pest control": ["cockroach", "termite", "mosquito", "rats", "bed bugs"],
    "Plumbing": ["plumber", "water leak", "tap", "pipe"],
    "Electrical work": ["electrician", "wiring", "fan repair", "switch board"],
    "Pet care": ["dog", "cat", "pet", "vet", "grooming"],
}

# Filler words dropped from a search so "I need help to run ads for my shop" searches for "ads", "shop".
STOP_WORDS = {
    "a", "an", "the", "i", "me", "my", "we", "our", "us", "you", "your", "to", "for", "of", "in", "on", "at", "and",
    "or", "with", "is", "am", "are", "be", "need", "needs", "want", "wants", "looking", "look", "help", "get", "run",
    "do", "can", "please", "someone", "some", "who", "best", "good", "near", "about", "how", "what", "any", "service",
    "services", "expert", "experts", "company", "companies", "person", "from", "this", "that", "it", "there",
}

MAX_TERMS = 8


def search_terms(query: str) -> tuple[list[str], list[str]]:
    """Split a free-text search into meaningful words, plus the service areas those words point to."""
    lowered = query.lower()
    words: list[str] = []
    for word in re.findall(r"[a-z0-9&+]+", lowered):
        if len(word) < 2 or word in STOP_WORDS:
            continue
        if len(word) > 4 and word.endswith("s") and not word.endswith("ss"):
            word = word[:-1]
        if word not in words:
            words.append(word)
    services = [
        name
        for name, phrases in RELATED_WORDS.items()
        if any(re.search(rf"\b{re.escape(phrase)}\b", lowered) for phrase in phrases)
    ]
    return words[:MAX_TERMS], services[:MAX_TERMS]


def related_words_for(services: list[str], limit: int = 12) -> list[str]:
    """Search words to suggest to a provider who offers these services."""
    wanted = {name.lower() for name in services}
    suggestions = [word for name, phrases in RELATED_WORDS.items() if name.lower() in wanted for word in phrases]
    return list(dict.fromkeys(suggestions))[:limit]


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
    # "ads" -> Digital marketing: also offer areas whose everyday words start with what was typed.
    related = [
        name
        for name, phrases in RELATED_WORDS.items()
        if name not in matches and len(needle) >= 2
        and any(phrase.startswith(needle) or f" {needle}" in f" {phrase}" for phrase in phrases)
    ]
    return (sorted(matches, key=lambda name: (rank(name), len(name))) + related)[:limit]
