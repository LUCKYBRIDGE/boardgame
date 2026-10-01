# AGENTS.md

## Repository purpose

This repository develops educational board games. For Animal-gorithm, maintain two intentionally separate tracks.

## Track A — faithful PLIX localization

Path: `games/animalgorithm-original-ko/`

Source priority:
1. `plix_llm-algorithm_arcade_game_guides_v1.pdf` — Animal-gorithm guide page
2. `plix-deck-animal-database.pdf` — animal cards, blank cards, Category Idea cards
3. Project documents under this track that explicitly fill source gaps

Rules:
- Preserve LEFT / RIGHT secret categories.
- Preserve prediction of which side the next animal belongs to.
- Preserve the choice to guess categories or add cards.
- Do not introduce TRUE/FALSE boards, Query tokens, Feature icons, scores, AND/OR rule levels, or other improved-version mechanics unless a document explicitly labels them as an optional experiment.
- Do not silently invent source facts. Anything absent from PLIX must be marked `PROJECT DEFAULT`.
- Korean localization may translate names and instructional text, but should not change the game loop.

## Track B — improved AI Detective

Path: `games/animalgorithm-ai-detective/`

This track may introduce explicit features, deterministic rule schemas, balancing, query-efficiency mechanics, classroom modes, and digital validation.

Do not back-port those changes into the faithful track without an explicit design decision.

## Source assets

Keep source-analysis notes separate from distributable assets. Do not assume source illustrations, layouts, or wording may be commercially redistributed merely because they are available in the reference PDFs.
