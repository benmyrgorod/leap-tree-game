You are writing an interactive branching story.

Original setup:
Genre: {genre}
Setting: {setting}
Opening line: {opening}

Full story history so far:
{history}

The player selected option {choice_label}: {choice_text}

Continue this story from that choice. Then provide exactly two short, contrasting continuation options.
Each option should be around five words.

Return only a valid JSON object with this exact shape:

{
  "story": "Story text",
  "option_a": "First continuation option",
  "option_b": "Second continuation option"
}

Do not include Markdown, code fences, commentary, or extra keys.
