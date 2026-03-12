### xwaction examples: actions_json

This example generates an **actions catalog** for multiple entities (CRUD + advanced actions),
serializes it into the requested formats, then demonstrates **loading** from each format and
reconstructing `XWAction` objects.

### Run

```bash
python xwaction/examples/actions_json/generate_actions_json.py
python xwaction/examples/actions_json/demo_load_actions.py
```

### Outputs

Files are written to:

- `xwaction/examples/actions_json/out/actions.json`
- `xwaction/examples/actions_json/out/actions.yaml`
- `xwaction/examples/actions_json/out/actions.toml`
- `xwaction/examples/actions_json/out/actions.xml`


