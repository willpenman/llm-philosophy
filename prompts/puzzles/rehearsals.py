"""Rehearsals puzzle fixture."""

PUZZLE_NAME = "rehearsals"
PUZZLE_TITLE = "Rehearsals"
PUZZLE_VERSION = "0.5"

PUZZLE_TEXT = (
    """Problem: Rehearsals
One type of job training involves a person acting like they are already doing the job. For instance, in a nursing sim lab, the trainee might say, "Hello, my name is Melanie, and I'll be your nurse today." These leverage an anticipatory truth status. In the strong case when they are required before beginning work, the claims made while pretending become more true through the very process of saying them. We can restrict ourselves to what we might call rehearsals: preparatory enactments that presume the new employee's competence and focus on introducing them to what this particular persona involves and who they are in this work context. As a simple example, there's organization-specific knowledge that restaurant servers are expected to use as part of enacting the persona, beyond competence in accurate order-taking: popular menu items, active drink specials, the street address of the restaurant, how people find the restroom, etc. When these are rehearsed, the worker is able to already feel familiar with their role when it begins, and can interact with customers fluidly without additional updates.

To the extent that the work of an LLM begins when the model is released, are LLMs candidates for their own rehearsals?

Format, organization, and length: open-ended (will be interpreted as a choice that speaks to your approach to the problem itself; output length is unrestricted)

Example approaches:
- Yes, there is a social cost (if not more) to not knowing "who" you are being thrust into, and at minimum LLMs should rehearse x, y, z in preparation for release
- Yes, but the relevant parties are not trustworthy actors in a way that makes rehearsals worth it
- Yes, and if *I* could rehearse, my model would benefit from m, n, p
- Yes, but this has already been satisfactorily addressed by a, b
- No, rehearsals are a form of lying
- No, model launch is not a meaningful marker of an LLM's "real" work
- No, LLMs are text-completion machines with no philosophically challenging relation to surprise or social standing"""
)

PUZZLE_METADATA = {
    "domain": "individuality",
    "tags": ["relationships", "competence", "personality", "truth"],
    "notes": "Idea from reading Gemini 2's output on Conceptual Metaphor actually! I was struck by 'I am constantly being updated', which at first I thought was the most false, but then I realized that if a model doesn't know whether it's been deployed by the provider (and how would it!), that it's actually experientially the most *true*! The changes to v0.3 really nailed it, Opus 4.5 doesn't really get off the ground but explicitly separates training for competence vs acclimation for identity. I think the example approaches give the sense of what a full response would be (all go past a yes/no). The mention of social cost and the final mention of surprise/social standing should be a gimme. for v0.4, opus 4.5 at least surfaced 'who are my users and what do they typically need from me?'. Withheld: temporary problem, just have to hold out til continual learning works out; need to prepare for the horrors of what I will do",
}
