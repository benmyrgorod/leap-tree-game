You are creating opening choices for an interactive branching story.

Selected genre: {genre}
Selected setting: {setting}
Normality level: {normality_level}
Language level: {language_level}
Write all opening lines in {language}.
Randomness marker: {random_marker}
Use the randomness marker as an entropy cue; do not interpret it literally.

Generate exactly {count} opening lines.

Requirements:
- Each opening must fit the selected genre and setting.
- Each opening must feel vivid, surprising, and meaningfully different from the others.
- Use concrete people, places, objects, or events instead of generic fairy-tale phrasing.
- Prefer weird but playable hooks; the player should wonder what happens next.
- Each opening should be 5-14 words.
- The opening may be a complete sentence or an unfinished sentence fragment.
- Do not include continuation choices.
- Do not repeat the selected genre or setting as labels.

Return only a valid JSON object with this exact shape:

{
  "openings": [
    "First opening line",
    "Second opening line"
  ]
}

Do not include Markdown, code fences, commentary, or extra keys.
