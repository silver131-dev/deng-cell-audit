# Project names and attribution

Canonical names for release candidate v0.1.0-rc3, recorded 2026-11-06.

| Role | Canonical value | Where it is used |
| --- | --- | --- |
| Project display name | DENG Cell Audit | README titles and release titles |
| Author and public copyright-holder name | ARiN | LICENSE, package authors, and attribution |
| Software license | MIT | LICENSE and package SPDX metadata |
| Repository name | `deng-cell-audit` | Intended GitHub repository and source directory |
| Python distribution name | `deng-cell-audit` | `pyproject.toml` project name and package installation |
| Python import/module name | `deng_cell_audit` | Imports and `python -m deng_cell_audit` |
| Console command | `deng-cell-audit` | Installed CLI entry point |
| GitHub account namespace | `silver131-dev` | Intended repository owner account, not the author field |
| Intended repository identifier | `silver131-dev/deng-cell-audit` | Prepared repository-creation command; not a claim that a remote exists |
| Python package version | `0.1.0rc3` | Package metadata and `__version__` |
| Release tag/display version | `v0.1.0-rc3` | Prepared Git tag and release title |
| Download/release ZIP filename | `deng-cell-audit-v0.1.0-rc3.zip` | Review download and prepared GitHub Release asset |
| Directory inside the ZIP | `deng-cell-audit/` | Extraction root and README `cd` command |

**DENG Cell Audit is the project name; ARiN is the confirmed author/copyright-holder attribution.** These names identify different roles. `silver131-dev` is the GitHub account namespace and is not a substitute copyright-holder name. Preserve the capitalization `ARiN` in prose and metadata.

Use hyphens in the distribution, repository, and CLI names, and underscores in Python imports. Built distribution filenames may use the packaging tool's normalized underscore form, such as `deng_cell_audit-0.1.0rc3-py3-none-any.whl`; that is the same distribution, not a separate project.

The `DENG_` schema prefix and existing `DENG-RESEARCH-` evidence identifiers are technical project namespaces. This naming clarification does not rename existing schemas, identifiers, Python imports, or CLI commands. Historical artifacts and study IDs keep their original identifiers so that existing evidence remains traceable.

Release status is separate from naming: preparing a repository identifier, tag, or ZIP does not create a remote repository, run remote CI, or publish a Release. Actual local checks and remote status are recorded in [VALIDATION.md](VALIDATION.md).

## 中文命名規則

對外統一寫作：**DENG Cell Audit — by ARiN**。專案名稱與作者／權利人署名分別為 **DENG Cell Audit** 與 **ARiN**；GitHub 帳號維持 `silver131-dev`。

套件、倉庫與指令使用 `deng-cell-audit`；Python 模組使用 `deng_cell_audit`。發布 tag 使用 `v0.1.0-rc3`，Python 套件版本使用 `0.1.0rc3`。下載包與預備發布附件統一為 `deng-cell-audit-v0.1.0-rc3.zip`。這些格式差異各有用途，不應全域取代成同一字串。
