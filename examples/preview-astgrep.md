# ast-grep Indicators (Optional)

Enable with `--enable-astgrep` or `ARCHITECTON_ENABLE_ASTGREP=1`.

Heuristics included:

- many_top_level_defs: suggests Facade/package split
- long_param_list (>6): suggest Parameter Object
- repeated_literals (≥5): suggest constant/Enum extraction

Sample output fragment:

```json
{
  "indicators": [
    { "type": "long_param_list", "count": 7 },
    { "type": "repeated_literals", "literals": ["'OK'", "'ERR'"], "count": 2 }
  ],
  "notes": ["ast-grep optional and best-effort; skipped if not installed"]
}
```
