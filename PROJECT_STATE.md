# WinForge Project State

## Metadata
- **Version:** 0.5.0
- **Phase:** Plugin Install/Uninstall Complete
- **Last Updated:** 2026-04-29
- **Tech Stack:** Python 3.11 + CustomTkinter + loguru + tufup + PyInstaller
- **Repo:** https://github.com/051-lab/WinForge

## Feature Status
| Feature | Status | Notes |
|---------|--------|-------|
| Main window | Done | CustomTkinter dark mode |
| Config system | Done | JSON-based settings + feature flags |
| Plugin loader | Done | Dynamic plugin discovery via pkgutil |
| Auto-updater | Done | Real GitHub Releases API checker |
| Update UI button | Done | Threaded check, green/yellow result label |
| Plugin Marketplace UI | Done | Tabbed UI, scrollable cards, Refresh button |
| Bundled Hello plugin | Done | plugins/hello - example with full metadata |
| Telemetry opt-in system | Done | Privacy-first, UUID install_id, opt-in toggle |
| Privacy tab UI | Done | CTkSwitch toggle, status label, consent saved |
| Plugin enable/disable | Done | Per-plugin toggle with registry persistence |
| Plugin uninstall | Done | Archives plugin folder, removes from registry |
| Installer UI | Done | Enable/Disable + Uninstall buttons per card |
| CI/CD pipeline | Done | GitHub Actions windows-latest |
| Tests (24 passing) | Done | pytest: 4 updater + 3 plugin + 5 telemetry + 6 installer + 6 core |

## Current Issues
- None known in v0.5.0

## Next Milestones
1. **v0.6.0** - Settings UI panel with persistent user preferences
2. **v0.7.0** - Plugin sandboxing and permissions model

## Dependencies
```
customtkinter>=5.2
loguru>=0.7
tufup>=0.10
pyinstaller>=6.0
```

## AI Resume Block
- Next task: Implement Settings UI panel with persistent user preferences (v0.6.0)
