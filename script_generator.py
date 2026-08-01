import argparse
import json
import random
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Hooks follow the first-person / consequence pattern (states a personal outcome
# up front) because that pattern consistently outperforms generic fact-lead hooks.
# All content is written in Maddie's first-person voice, part of her ongoing
# "broke-to-built" college log (see persona.md).
HOOKS = {
    "cert_study_grind": [
        "I almost failed my Network+ because of one bad study habit.",
        "I bombed my first practice exam and it's the best thing that happened to me.",
        "I stopped rereading notes and started doing this instead, and my score jumped.",
    ],
    "budget_laptop_and_tech": [
        "My $600 laptop nearly died two days before finals, so I fixed it myself.",
        "I stopped buying a new laptop every time mine slowed down. Here's what I do instead.",
        "The fan noise started during a client call, and I panicked for a second.",
    ],
    "scout_and_pet_life": [
        "Scout chewed through his third leash this month, so I finally did something about it.",
        "I almost skipped Scout's vet visit to save money, and I'm glad I didn't.",
        "My rescue mutt taught me more about budgeting than any finance video ever did.",
    ],
    "freelance_and_side_income": [
        "I fixed one classmate's laptop for $20 and it turned into a whole side income.",
        "I said yes to a random DM asking for IT help, and it changed my semester.",
        "My freelance IT gigs now cover more than my helpdesk paycheck.",
    ],
    "college_money_reality": [
        "I did the math on my actual rent split and almost cried.",
        "I stopped ordering delivery during exam week and saved more than I expected.",
        "My roommate and I tracked every shared expense for a month. It got ugly.",
    ],
    "productivity_and_time": [
        "I deleted three apps off my phone and got two hours back every day.",
        "I stopped studying at night and started at 7am. My grades actually moved.",
        "The one group project I said no to saved my entire week.",
    ],
}

BEATS = {
    "cert_study_grind": [
        "I've been grinding practice quizzes between shifts at the helpdesk, and it's slower than I want but it's sticking.",
        "I switched from just rereading my notes to timed practice questions, and that's when things clicked.",
        "I keep a running tally of my wrong answers so I stop repeating the same mistake on exam day.",
        "Studying for a cert while carrying a full class load is rough, but it's the backup plan I actually trust.",
    ],
    "budget_laptop_and_tech": [
        "I popped the back off and it was just dust and dried-out thermal paste, not a dead motherboard like I feared.",
        "I priced a new laptop first, saw the number, and decided to fix mine instead.",
        "I run a quick cleanup pass every month now so I'm not fixing a crisis during finals week again.",
        "I test everything on this laptop before I trust it, because it's the only one I've got.",
    ],
    "scout_and_pet_life": [
        "Scout is a scruffy little terrier mix I adopted sophomore year, mostly because my apartment felt too quiet.",
        "He's chewed through two leashes and a charger cord, so I've had to get smarter about what I buy for him.",
        "Vet bills are the one expense I don't cut corners on, everything else in my budget bends before that does.",
        "He sits by my desk every time I study, which is either helpful or the reason I get distracted, still deciding.",
    ],
    "freelance_and_side_income": [
        "It started as a favor for a classmate and turned into three more clients by word of mouth.",
        "I batch my freelance hours into two nights a week so it doesn't eat my whole schedule.",
        "I still undercharge sometimes, but I raise my rate every time I get a new referral.",
        "This is the income stream I actually control, which is why I keep documenting it.",
    ],
    "college_money_reality": [
        "Between rent, groceries, and one too many delivery orders, the math wasn't adding up the way I thought.",
        "My roommate and I now split everything in a shared spreadsheet, which is annoying but it works.",
        "I moved my savings to a separate account so I stop treating it like spending money.",
        "This is the least glamorous part of the log, but it's the part that actually matters.",
    ],
    "productivity_and_time": [
        "I block my hardest task first thing, before I let myself open anything else.",
        "I stopped saying yes to every group project meeting and started saying yes to the ones that mattered.",
        "Planning tomorrow the night before means I start moving instead of deciding what to do.",
        "This one change freed up more time than anything else I've tried this semester.",
    ],
}

CTAS = [
    "That's today's chapter. Follow for the next one.",
    "More on this as it happens. Follow along.",
    "Anyway, back to the grind. Follow for the log.",
    "Follow if you want to see how this arc ends.",
]

HASHTAGS = {
    "cert_study_grind": ["#itcertification", "#studywithme", "#certsprint"],
    "budget_laptop_and_tech": ["#techtok", "#laptoptips", "#budgettech", "#collegelife"],
    "scout_and_pet_life": ["#dogsoftiktok", "#rescuedog", "#petlife", "#collegepet"],
    "freelance_and_side_income": ["#sidehustle", "#freelancer", "#makemoneyonline"],
    "college_money_reality": ["#collegebudget", "#personalfinance", "#brokecollegestudent", "#moneytips"],
    "productivity_and_time": ["#productivity", "#studytok", "#timemanagement", "#collegelife"],
}

# "#collegehustle" gia' coperto da COMMON_HASHTAGS - rimosso dai due pool per
# categoria che lo includevano perche' generava un duplicato nella caption
# finale (es. "#collegehustle ... #collegehustle" - trovato live 2026-08-01
# sul primo video reale pubblicato).
COMMON_HASHTAGS = ["#thelog", "#collegehustle", "#shorts"]

# Natural, non-ad-read ways to weave a sponsor mention into a beat, keyed by sponsor id.
SPONSOR_MENTIONS = {
    "certsprint": "Ngl, I've been using CertSprint's practice quizzes to drill this stuff between classes, it's the only reason I'm not rereading a textbook at midnight.",
    "pc_tweaker": "I ran PC Tweaker on it too, just to squeeze out a bit more performance without spending a dollar on new hardware.",
    "groomlyco": "Most of Scout's gear lately has come from Groomlyco, honestly just because it survives him better than what I tried before.",
    "magdock": "I've been testing a couple of Magdock gadgets on my actual daily setup, keeping the ones that earn their spot on my desk.",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def pick_category(config, category=None):
    categories = config["script"]["categories"]
    if category:
        if category not in categories:
            raise ValueError(f"Unknown category: {category}. Choices: {categories}")
        return category
    return random.choice(categories)


def pick_sponsor(config, category, force_sponsor=None):
    """Pick a sponsor for this script slot, respecting the sponsor_video_ratio
    and only matching a sponsor whose pillar fits the chosen category. Returns
    None most of the time, by design (80/20 rule, see persona.md)."""
    sponsors = config.get("sponsors", {})
    ratio = sponsors.get("sponsor_video_ratio", 0.2)

    if force_sponsor:
        if force_sponsor not in sponsors:
            raise ValueError(f"Unknown sponsor: {force_sponsor}. Choices: {list(sponsors.keys())}")
        return force_sponsor

    candidates = [
        sponsor_id
        for sponsor_id, sponsor in sponsors.items()
        if isinstance(sponsor, dict) and sponsor.get("pillar") == category
    ]
    if not candidates:
        return None
    if random.random() > ratio:
        return None

    weights = [sponsors[sponsor_id].get("weight", 1) for sponsor_id in candidates]
    return random.choices(candidates, weights=weights, k=1)[0]


def build_title(category, hook):
    clean = re.sub(r"[.?!]$", "", hook)
    words = clean.split()
    short = " ".join(words[:8])
    return f"{short}..." if len(words) > 8 else clean


def generate_script(config, category=None, seed=None, sponsor=None):
    if seed is not None:
        random.seed(seed)

    category = pick_category(config, category)
    hook = random.choice(HOOKS[category])

    beats_count = config["script"]["tips_per_video"]
    beats_pool = BEATS[category][:]
    random.shuffle(beats_pool)
    beats = beats_pool[:beats_count]

    sponsor_id = pick_sponsor(config, category, force_sponsor=sponsor)
    if sponsor_id:
        beats = beats[:-1] + [SPONSOR_MENTIONS[sponsor_id]]

    cta = random.choice(CTAS)

    lines = [hook] + beats + [cta]
    full_text = " ".join(lines)

    hashtags = HASHTAGS[category] + COMMON_HASHTAGS
    caption = f"{hook} {cta}"

    persona = config.get("persona", {})

    video_id = uuid.uuid4().hex[:10]
    data = {
        "id": video_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "persona_name": persona.get("name"),
        "category": category,
        "title": build_title(category, hook),
        "hook": hook,
        "beats": beats,
        "cta": cta,
        "script_text": full_text,
        "caption": caption,
        "hashtags": hashtags,
        "sponsor": sponsor_id,
    }
    return data


def save_script(data, config):
    scripts_dir = Path(__file__).parent / config["paths"]["scripts_dir"]
    scripts_dir.mkdir(parents=True, exist_ok=True)
    out_path = scripts_dir / f"{data['id']}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Generate a Maddie Ross persona-driven short-form script.")
    parser.add_argument("--category", help="Force a specific category from config.yaml")
    parser.add_argument("--sponsor", help="Force a specific sponsor id from config.yaml's sponsors section")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    args = parser.parse_args()

    config = load_config()
    data = generate_script(config, category=args.category, seed=args.seed, sponsor=args.sponsor)
    out_path = save_script(data, config)

    print(f"Generated script {data['id']} ({data['category']})")
    print(f"Title: {data['title']}")
    print(f"Sponsor: {data['sponsor'] or 'none'}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
