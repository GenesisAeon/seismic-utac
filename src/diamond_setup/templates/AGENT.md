# AGENT.md – GenesisAeon Release & Metadata Rules

## Bei jeder relevanten Änderung (Version Bump, Feature, Bugfix, Docs):

1. **.zenodo.json**
   - Aktualisiere `version`, `description`, `keywords`, `related_identifiers`
   - Beschreibung muss die aktuelle Funktion des Packages klar beschreiben
   - Immer den Whitepaper-DOI (10.5281/zenodo.19645351) als `isPartOf` oder `isDocumentedBy` eintragen

2. **README.md**
   - Aktualisiere Whitepaper-Badge auf aktuelle Version
   - Aktualisiere @software BibTeX-Eintrag (version, publisher=Zenodo, DOI)
   - Füge Package-Number-Badge ein (z.B. Package 17)

3. **Versionierung**
   - pyproject.toml und __init__.py müssen synchron auf dieselbe Version sein
   - Tags immer als annotated Tag (`git tag -a vX.Y.Z`)

4. **Commit-Message**
   - Beginne mit "release:", "feat:", "fix:", "docs:" oder "chore:"

5. **Nach jedem neuen Tag**
   - Release-Pipeline (PyPI + Zenodo) wird automatisch ausgelöst

Diese Regeln sind bindend für alle Claude-Code-Runs und zukünftige Agents in GenesisAeon-Repos.
