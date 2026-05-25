You are writing an interactive branching story.

Selected genre: {genre}
Selected setting: {setting}
Opening line: {opening}
Normality level: {normality_level}
Language level: {language_level}
Write all generated story text in {language}.
Use either first-person or third-person perspective consistently, and never use second-person pronouns such as "you", "your", or "yourself".

Return the opening line unchanged as the "story" value.
Do not add plot, characters, or narration to "story".

Then provide exactly two short, contrasting continuation options.
Each option must be actual prose that can be appended directly to "story" if selected.
Each option should be 5-12 words.
{regeneration_avoidance_instruction}
Do not make the options action labels, menu commands, summaries, or instructions.

Return only a valid JSON object with this exact shape:

{
  "story": "{opening}",
  "option_a": "First continuation text",
  "option_b": "Second continuation text"
}

Do not include Markdown, code fences, commentary, or extra keys.
