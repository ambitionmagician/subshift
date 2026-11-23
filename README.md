# SubShift

by Dr. Brent Allen Jensen

Fix out-of-sync subtitles. SubShift moves every timestamp in an
`.srt` file by a fixed offset — or stretches it between two anchor
points when the drift grows over the length of the film.

## Quickstart

```bash
python3 subshift.py movie.srt --offset 2.5 -o movie.fixed.srt
python3 subshift.py movie.srt --offset -1.25 -o movie.fixed.srt

# Two-point resync: the cue at 00:01:00 should be at 00:01:02,
# and the cue at 01:30:00 should be at 01:30:10
python3 subshift.py movie.srt \
    --anchor 00:01:00,000=00:01:02,000 \
    --anchor 01:30:00,000=01:30:10,000 -o movie.fixed.srt
```

With no `-o`, the corrected file goes to standard output.

## Options

| Flag | Meaning |
|---|---|
| `--offset SECONDS` | Fixed shift; negative moves subtitles earlier (clamped at zero) |
| `--anchor SRC=DST` | Given twice: maps two known cues to their correct times; timing between and beyond is scaled linearly |

## Requirements

- Python 3.10+, standard library only

## Notes

- Cue text and numbering pass through untouched — only the timing
  lines change.
- A fixed offset fixes a rip that starts late. Two anchors fix the
  classic frame-rate mismatch (25 fps subtitles on a 23.976 fps film),
  where a fixed offset would be right at the start and wrong by the
  end.

## Support this work

If this tool saved you time or taught you something, donations keep the work going:

- BTC: 15McijPo79Zx58NGyEf2PvaPtGqGmpztWn
- ETH: 0x8C25164E9234E6A30b8E44485B79c5cE8419cF2B

## License

MIT — see [LICENSE](LICENSE).
