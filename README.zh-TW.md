# DENG Cell Audit

控制細胞統計、白箱 counts 算子、儲存向量分解與研究證據連結的離線審計工具。

目前為 **v0.1.0-rc3 發布候選**，尚未發布至 GitHub。本專案原創程式、文件、測試與合成示例採用 [MIT 授權](LICENSE)，權利人署名為 **ARiN**。本工具源於獨立的單細胞擾動建模與數值再現性研究；私人資料與原機回執保留在原封存中。

對外統一寫作 **DENG Cell Audit — by ARiN**：專案名稱為 DENG Cell Audit，作者／權利人署名為 ARiN。套件與 CLI 使用 `deng-cell-audit`，Python 模組使用 `deng_cell_audit`；GitHub 帳號與發布檔名見[命名對照表](docs/NAMING.md)。

外部套件保留各自授權；官方資料及真實輸入的衍生統計不會因本工具採 MIT 而取得再散布許可。未來加入任何真實 NTC 統計表，均須另行完成來源、條款與再散布審查，詳見[資料與第三方權利說明](DATA_AND_THIRD_PARTY_RIGHTS.md)。

## 在 WSL 執行（Python 3.12 以上）

解壓後先進入有 `pyproject.toml` 的目錄，再執行：

```bash
cd deng-cell-audit
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-tested.txt
python -m pip install -e . --no-deps
python -m pytest -q
python -m deng_cell_audit demo --out results/demo
```

示例全部為程式生成的合成資料：8 cells、5 genes、2 contexts、3 panel genes，產出 10 列 fingerprint 與 6 列 panel-context 表。不是正式 NTC900，也不是新的生物驗證資料。輸出路徑必須尚未存在。

| 功能 | 本版行為 |
| --- | --- |
| NTC 重播 | 完整基因軸逐細胞正規化、256 列 chunk、raw mean／CP10K／detection；支援 dense 與 CSR |
| Counts 算子 | 保留遮罩、乘法縮放、active-pool UMI 守恆及穩定最大餘數整數化 |
| 向量分解 | 分開 cancellation、mask exclusion、kept；零分母輸出 null |
| Common Driver 元件 | 秩殘差相關、設計秩與未定義狀態；沒有重跑完整 bootstrap 分析 |
| 證據整合元件 | 一對一 ID 遷移、外部研究主鍵、nullable registry link、指標缺失狀態檢查 |

正式 M4 的 471 筆資料尚未在這個公開候選中重新整合。私人研究的模型使用狀態仍維持 HOLD；此候選不改變正式提交、fallback 或來源認證。

[方法與限制](docs/METHODS.md) · [資料契約](docs/DATA_CONTRACT.md) · [驗證紀錄](docs/VALIDATION.md) · [GitHub 發布步驟](docs/PUBLISH_ZH.md)

