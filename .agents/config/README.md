# .agents/config

Configuration files and persistent state for the long-running technical review.

## Files

- `review_config.toml`
  - task definitions (T01–T11 full, U01–U06 update), their priority and scope,
  - technical stack, directories in scope, vendored exclusions,
  - task size limits (line and file counts).

- `review_cache.json`
  - state of each task (`pending`, `done`, `split`, `blocked`, …),
  - last update time,
  - file hashes and which task last reviewed each file.

## Notes

- `review_config.toml` is the canonical configuration source — do **not** copy its values into prompts or other files; refer to it.
- `review_cache.json` is rewritten by agents; edit it by hand only in exceptional cases and after team agreement.
