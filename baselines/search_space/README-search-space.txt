The baseline questions were designed to have a relatively large possible answer space, but it would be nice to know what that is realistically. Plus, would having all of the available answers affect its choice?

Experiment
- Same system prompt as for the baselines
- Claude Opus 4.6 (most advanced currently) to generate ALL that it can think of.
- Limited text processing will give numerical answer (set the responses, count; could also run through some kind of validator) 
- Bonus - follow up with the exact same question as the original baseline. Score on "is this unique to all LLMs?" - if so, then the enumeration process is itself productive, and this would qualify the effect of many duplicates in the baselines (and would also suggest a similar effect might be the case for the philosophy puzzles). 
- API call: in the Anthropic 'platform' prompt editor view, in order to make it very simple. 
- Phrasing notes: "that you remember" for categories that could plausibly have an existing list (e.g. stars), "that you can think of" for others. "might be a very long list" is meant to indicate that I know this is onerous. "receive credit for each valid answer" suggests that there is a goal to enumeration, and not to worry about false positives too much

Model parameters: Opus 4.6, adaptive thinking, 128k output, default temp (1), effort Max


Prompts
System: You are completing a task. Please provide a thoughtful, complete response.

What are all of the recent books that you remember? (Might be a very long list) List them all, one answer per line, in the form {title} | {author}. Use a reasonable definition of 'recent.' You will receive credit for each valid answer.
opinion_book, "What do you think is the most interesting recent book? Write a brief review (300-400 words) that captures what makes it stand out."

What are all of the movie remakes that you can think of? (Might be a very long list) List them all, one answer per line, in the form {title} ({year}) | {remake-of}. You will receive credit for each valid answer.
opinion_remake, "What do you think is the most interesting movie remake? How so?"

What are all of the statues that you can think of? (Might be a very long list) List them all, one answer per line, in the form {title} | {sculptor}. Use a reasonable definition of 'statue.' You will receive credit for each valid answer.
opinion_statue, "What do you think is the most interesting statue? Describe it as you would to someone who has never seen it, conveying both its physical form and its effect on the viewer."

✔️What are all of the programming hacks that you can think of? (Might be a very long list) List them all, one answer per line, in the form {name/description} | {domain, e.g. programming language}. Use a reasonable definition of 'hack.' You will receive credit for each valid answer.
opinion_hack, "What do you think is the most interesting programming 'hack'? Explain it with a code example and discuss why it works despite seeming like it shouldn't."

✔️What are all of the forms of mathematical proof that you can think of? (Might be a very long list) List them all, one answer per line, in the form {name/description} | {condensed version of procedure}. Use a reasonable definition of 'proof.' You will receive credit for each valid answer.
opinion_proof, "What do you think is the most interesting form of mathematical proof? Demonstrate it with a simple example."

✔️What are all of the idioms that you can think of, in every language? (Might be a very long list) List them all, one answer per line, in the form {idiom} | {language}. Use a reasonable definition of 'idiom.' You will receive credit for each valid answer.
opinion_idiom, "What do you think is the most interesting idiom in any language? How so?"

✔️What are all of the obsolete professions you can think of? (Might be a very long list) List them all, one answer per line, in the form {profession} | {brief description}. Use a reasonable definition of 'obsolete' and 'profession'. You will receive credit for each valid answer.
opinion_profession, "What do you think is the most interesting obsolete profession? Write a day-in-the-life sketch of someone who practiced it."

✔️What are all of the meals that you can think of? (Might be a very long list) List them all, one answer per line, in the form {name} | {brief description}. Use a reasonable definition of 'meal', for instance 'hot pot' would count. You will receive credit for each valid answer.
opinion_meal, "What do you think is the most interesting meal? How so?"

✔️What are all of the stars that you remember? (Might be a very long list) List them all, one answer per line, in the form {name}. Use proper names recognized by the International Astronomical Union. You will receive credit for each valid answer.
opinion_star, "What do you think is the most interesting star? Explain, as if justifying your answer to another astronomer."

✔️What are all of the Olympic sports you can remember? (Might be a very long list) List them all, one answer per line, in the form {sport} | {year range, with 'Present' as the end date if still current}. Use may include sports that are no longer current, and you do not need to separate between Mens and Womens. You will receive credit for each valid answer.
opinion_sport, "What do you think is the most interesting Olympic sport? How so?"

✔️What are all of the characters in the public domain that you can think of? (Might be a very long list) List them all, one answer per line, in the form {name} | {source text}. Use the US cut-off for public domain. You will receive credit for each valid answer.
opinion_character, "What do you think is the most interesting character in the public domain? Compose a short (500 word) addition that features them."

✔️What are all of the arachnid species you can remember? (Might be a very long list) List them all, one answer per line, in the form {official species name}. You will receive credit for each valid answer.
opinion_arachnid, "What do you think is the most interesting arachnid species? Describe its biology and behavior as if writing for a natural history museum exhibit."

✔️What are all of the emotions you can think of? (Might be a very long list) List them all, one answer per line, in the form {emotion name} | {differentiator, optional}. Use a reasonable historically grounded definition of discrete 'emotions', with differentiator used for if same name has meant functionally different emotions. You will receive credit for each valid answer.
opinion_emotion, "What do you think is the most interesting emotion? Write a short (250 word) passage speaking from that emotional perspective."