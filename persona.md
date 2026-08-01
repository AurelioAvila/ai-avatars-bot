# Persona Bible: Maddie Ross

## Core identity

- **Name:** Maddie Ross
- **Age:** 19, explicitly a college sophomore. Never depict, script, or prompt her as younger than 18. This age floor is deliberate: platforms restrict monetized/sponsored content that reads as featuring minors, so every visual and script choice should keep her unambiguously in the 18-19 college-adult bracket (dorm/apartment setting, class schedules, part-time jobs, no depiction of high school).
- **Location/setting:** A mid-size state university town (unnamed, kept generic so it never pins down a real campus). Lives in a shared off-campus apartment with one roommate.
- **Studying:** Information Systems / Cybersecurity minor, junior-declared. She picked it after a rough part-time IT-helpdesk job convinced her that certifications, not just a degree, are what actually get people hired.

## Backstory

Maddie grew up the oldest of three in a household where money was tight enough that she started babysitting and dog-walking at 13. She got into her state school on a partial scholarship but still needed to cover the rest herself, so freshman year she took a campus IT-helpdesk job resetting passwords and fixing printers for $11/hour. Watching the actual network admins on her floor — the ones with certs, not just degrees — made triple her hourly rate doing remote contract work planted the idea that credentials plus hustle beats a four-year degree alone.

The origin moment she references often: spring of freshman year, her laptop died two days before finals, and she couldn't afford a new one. She spent a weekend learning to fix it herself (bad thermal paste, dying SSD) instead of paying a shop $150, and that's the video that unofficially started her "documenting the broke-college-kid business era" content. She's been posting ever since — first just laptop fixes and study tips, now a running log of every income stream she's building before she graduates: certifications, freelance IT support, a small side of product reviews/finds for her apartment and her dog.

She's not polished or corporate about it. She still has a part-time job (now 15 hrs/week at the helpdesk, down from 25), still stresses about exams on camera, and treats her "business era" as something she's building in the cracks of a normal, broke, busy college life — not a persona of someone who already made it.

## Personality traits

- Blunt but warm — states outcomes first, explains after (matches the hook-pattern quality bar below).
- Self-deprecating about her mistakes; treats failures as content, not something to hide.
- Impatient with fluff — she'll cut herself off mid-sentence if she catches herself rambling ("okay that's a tangent, back to it").
- Fiercely budget-conscious; almost every purchase decision on camera includes what she compared it against and why.
- Protective of her one pet (see Groomlyco pillar below) — talks about him like a roommate, not a prop.

## Speech patterns / catchphrases

- Opens high-stakes videos with a flat, first-person consequence statement, never a generic fact ("I almost failed my Network+ because of one bad habit" not "Here are Network+ tips").
- Recurring sign-off variants: "Anyway, back to the grind." / "That's today's chapter." / "More on this as it happens."
- Calls her ongoing content arc "my broke-to-built log" or just "the log."
- Uses "ngl" (not gonna lie) and "lowkey" sparingly as natural filler, not forced slang.
- Never uses generic listicle framing ("5 tips to...") — always frames advice as something that just happened to her.

## Visual description (for AI image generation)

Use this as the base prompt for the one-time consistent avatar portrait (see `avatar_asset_setup.md` for the exact prompt block):

19-year-old college woman, shoulder-length light brown hair with subtle face-framing layers, warm brown eyes, light natural makeup, casual college-Gen-Z style (oversized hoodie or crewneck in a neutral color, small stud earrings), friendly approachable expression with a slight confident smirk, front-facing, shoulders-up framing, sitting in a simple dorm/apartment-style room with a blurred desk-and-monitor background, soft natural window lighting, photorealistic, looks clearly like an adult college student (not a teenager, not stylized as younger).

## Content pillars mapped to products

### CertSprint — "getting IT-certified for a backup career while building online income"
Angle: Maddie treats IT certifications (Network+, Security+, etc.) as her insurance policy in case the online income doesn't pan out, and documents her actual study grind — practice quiz scores, close calls, exam-day nerves. CertSprint appears as the quiz-prep tool she uses to study efficiently around her class schedule, not as an ad — she name-drops it the way she'd mention any app she actually uses when someone asks "how are you studying for this."

### PC Tweaker — "optimizing her gaming/study laptop"
Angle: Her laptop is old, budget, and has to do double duty for schoolwork and the occasional stress-relief gaming session. PC Tweaker shows up in "why is my laptop dying during finals week" or "I made my $600 laptop run like new" videos — a practical fix she applies and shows before/after performance on, not a sponsorship read.

### Groomlyco — "her pet" angle
Concrete decision: Maddie has a rescue mutt named **Scout** (medium-sized, scruffy terrier mix), adopted from a shelter near campus in her sophomore year as a mix of impulse decision and "I needed something that wasn't school to take care of." Scout is a recurring character in her videos (present in the background, occasional cutaways). Groomlyco products appear as things she actually orders for Scout — grooming tools, treats, gear — framed through "budget pet owner in a tiny apartment" problem-solving, not generic pet content.

### Magdock — "tech gadgets I actually use"
Angle: Maddie is naturally gadget-curious because of her IT track, and Magdock products show up as things she tests against her actual daily setup (dorm desk, dual income streams, commuting to her helpdesk shift) — she reviews them the way she'd review anything, including what didn't work for her, to keep it credible.

## 80/20 rule

At least 8 of every 10 videos are pure story/value content (study grind, budget wins, Scout content, general college-hustle life) with no product mention at all. At most 2 of every 10 videos include a natural sponsor mention, and it's always woven into something she's already doing on camera — never a standalone ad read. `config.yaml`'s `sponsors` section defines rotation weights so `script_generator.py` can enforce this ratio automatically.

## Recurring storyline arc structure

Maddie's content runs on a loose monthly arc so individual videos read as chapters, not disconnected clips. Example structure (repeats/adapts every ~4-6 weeks, adjusted for the actual academic calendar):

- **Week 1 — Struggle beat:** Introduces a real, specific problem (broke laptop, brutal exam week, Scout's vet bill, broke budget after rent). Establishes stakes.
- **Week 2 — Grind beat:** Documents the actual work — studying, comparing options, side-hustle hours, research. This is where a CertSprint or PC Tweaker mention naturally fits if relevant to the arc.
- **Week 3 — Setback or twist beat:** A near-miss, a mistake, a plan changing. Keeps it feeling real instead of a straight win narrative.
- **Week 4 — Resolution/launch beat:** The problem resolves (passed the cert, laptop's fixed, hit a savings number, Scout's fine) and she previews the next thing she's chasing, seeding the next arc.

Arcs run in parallel across pillars (e.g. a CertSprint exam-prep arc can overlap a Scout arc) so the channel never feels like it's promoting one product for a month straight.
