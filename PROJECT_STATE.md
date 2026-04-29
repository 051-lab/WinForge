# WinForge Project State

## Metadata
- **Version:** 0.7.0
- **Phase:** Plugin Sandboxing Complete
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
| Settings UI panel | Done | Theme, window size, telemetry toggle, persistent prefs |
| Plugin sandboxing | Done | Permissions manifest (PLUGIN_PERMISSIONS), enforcement layer |
| Sandbox permissions | Done | 9 known tokens (ui:read, fs:write, network:fetch, etc.) |
| CI/CD pipeline | Done | GitHub Actions windows-latest |
| Tests (38 passing) | Done | pytest: 4 updater + 3 plugin + 5 telemetry + 6 installer + 6 core + 5 settings + 9 sandbox |

## Current Issues
- None known in v0.7.0

## Next Milestones
1. **v0.8.0** - Plugin auto-install from remote registry
2. **v0.9.0** - Real-time plugin status dashboard

## AI Resume Block
- Next task: Implement plugin auto-install from remote registry (v0.8.0)

Current phase: v0.7.0 - Plugin Sandboxing Complete
