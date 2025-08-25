# rope Preview Rename (Optional)

Enable with `--enable-rope` or `ARCHITECTON_ENABLE_ROPE=1`.

Behavior: Uses rope project parsing and `get_changes()` dry-run preview only; it never applies edits.

Sample result:

```json
{
  "rope_ok": true,
  "rope_preview_ok": true,
  "warnings": []
}
```
