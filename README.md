# Open Environments Index

A catalogue of open RL environments for language-model agents, filed under the ISCED-F 2013 fields of education and training, by [Renaissance Labs](https://renaissancelabs.eu). Live at https://practice.renaissancelabs.eu.

For each environment: what the agent does, how it is rewarded, what it is good for and how to run it. Static site: plain HTML, CSS and a little JavaScript, no backend.

## Layout

- `data/isced_f.json`: the taxonomy (11 broad, 29 narrow, 80 detailed fields).
- `data/hub.json`: Hugging Face Hub metadata for each repository (downloads, likes, licence, dates, tags).
- `data/records/*.json`: one record per environment, read from the publisher's card to a fixed schema (summary, field, reward, interface, task count, run command). `data/records/curated.json` holds tasksets that do not carry the `rl-environment` tag, written by `tools/add_curated.py`.
- `data/overrides.json` (optional): corrections by `id`; these win over the records. `{"id": "...", "_remove": true}` hides an entry.
- `tools/build.py`: writes `index.html`, `env/<slug>/`, `fields/<code>/`, `about/`, `data/environments.json`, `environments.csv`, `sitemap.xml`, `llms.txt`.

## Build

```bash
python3 tools/build.py
python3 -m http.server 8794    # preview
```

## Corrections

Records are spot-checked, not audited, and the environments have not been run by us. The publisher's card is the authority. To correct or add an environment, open an issue or tell us on [Discord](https://discord.gg/6JUezWZbAm).

## Licence

Code: MIT. Index data in `data/` and `environments.csv`: CC BY 4.0, please credit "Open Environments Index by Renaissance Labs". Each environment keeps its own licence.
