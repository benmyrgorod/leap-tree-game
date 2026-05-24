You are writing an interactive branching story.

Original setup:
Genre: {genre}
Setting: {setting}
Opening line: {opening}

Full story history so far:
{history}

Current canonical story so far:
{current_story}

Write all generated story text in {language}.

The player selected option {choice_label}: {choice_text}

Return the current canonical story unchanged as the "story" value.
Do not rewrite, summarize, or add new prose to "story".

Then provide exactly two short, contrasting continuation options.
Each option must be actual prose that can be appended directly to "story" if selected.
Each option should be 3-7 words.
{continuation_start_instruction}
{continuation_shape_instruction}
{regeneration_avoidance_instruction}
Do not make the options action labels, menu commands, summaries, or instructions.

Return only a valid JSON object with this exact shape:

{
  "story": "{current_story}",
  "option_a": "First continuation text",
  "option_b": "Second continuation text"
}

Do not include Markdown, code fences, commentary, or extra keys.
