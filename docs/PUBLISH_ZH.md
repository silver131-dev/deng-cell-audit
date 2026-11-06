# GitHub 發布操作單

專案名稱：**DENG Cell Audit**；作者／權利人署名：**ARiN**；已確認的 GitHub 帳號：`silver131-dev`。預備建立的倉庫識別為 `silver131-dev/deng-cell-audit`，名稱可用性仍須在實際建立時確認。本包未建立遠端、推送 commit、建立 tag 或發布 Release。

完整對照見[命名規則](NAMING.md)。本版下載包與預備 GitHub Release 附件統一命名為 `deng-cell-audit-v0.1.0-rc3.zip`；解壓根目錄維持 `deng-cell-audit/`。GitHub 帳號是存放倉庫的位置，不替代 LICENSE 中的 ARiN 署名。

## 先審閱這個候選

1. 查看 README、METHODS、DATA_CONTRACT 與 VALIDATION，確認公開主張與實際範圍。
2. 本版已採 MIT，權利人署名已確認為 ARiN；核對 `LICENSE`、`pyproject.toml` 與 `DATA_AND_THIRD_PARTY_RIGHTS.md` 的範圍一致。資料與第三方內容不因本工具採 MIT 而取得再散布權利。
3. 若改動任何檔案，更新明確的 `release-files.txt`，再以 `--refresh-manifest` 建立新的審閱版；不得把私人整個工作目錄加入。
4. 跑完以下檢查。此處命令只驗證及打包本機候選：

```bash
python -m pytest -q
python tools/verify_release.py
python -m build --no-isolation
python tools/build_release.py --out dist/deng-cell-audit-v0.1.0-rc3.zip
```

修改並審閱過檔案後，才使用：

```bash
python tools/build_release.py --refresh-manifest --out dist/deng-cell-audit-reviewed.zip
```

## 經決定後建立 GitHub 倉庫

以下是預備命令，**本次沒有執行**。先採 private 倉庫可核對遠端 CI，公開可見度另行決定。本候選已套用 MIT，但尚未發布至 GitHub；授權決定與遠端發布狀態應分別描述。

```bash
git init -b main
git add --pathspec-from-file=release-files.txt
git diff --cached --stat
git commit -m "Prepare DENG Cell Audit v0.1.0-rc3"
gh repo create silver131-dev/deng-cell-audit --private --source=. --remote=origin --push
```

使用本人既有 Git 身分設定與 GitHub 登入狀態；本包未代填個人電子郵件。若同名倉庫已存在，先核對其內容與遠端，不要強制覆寫。

遠端 CI 通過且具體版本已審閱後，才執行 tag／draft Release：

```bash
git tag -a v0.1.0-rc3 -m "DENG Cell Audit release candidate"
git push origin v0.1.0-rc3
gh release create v0.1.0-rc3 dist/deng-cell-audit-v0.1.0-rc3.zip --draft --prerelease --title "DENG Cell Audit v0.1.0-rc3" --notes-file RELEASE_NOTES.md
```

公開之前重新確認實際倉庫可見度、授權文字、Release 附件與該 commit 的 CI。這些步驟不需要重新執行已完成的私人 NTC900 原機重播。

