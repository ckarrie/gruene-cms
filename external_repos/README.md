# Git Submodules Cheatsheet

## Submodule hinzufügen

```
cd /path/to/respos/gruene-cms
git submodule add https://github.com/verdigado/sunflower external_repos/verdigado/sunflower
git submodule update --init --recursive
```

## Status

```
cd /path/to/respos/gruene-cms
git submodule status
```

## Einen bestimmten Tag auschecken

```
cd external_repos/verdigado/sunflower
git fetch --all --tags --prune
git checkout tags/v2.2.13
```

Dann commiten.

