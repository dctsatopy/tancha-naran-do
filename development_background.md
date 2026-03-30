# たんちゃーならんど (Tancha-Naran-Do) — 開発経緯・仕様書

> 作成日: 2026-03-27
> ステータス: 実装中

---

## 1. 経緯・背景

感情（特に怒り）のセルフコントロールを習慣的に改善したいという動機から開発を開始した。
習慣的なセルフチェックと気づきによって、感情の傾向を把握し克服することを目指す。

---

## 2. 目的

- 感情（特に怒り）のセルフコントロール能力を高める。
- 日々の感情状態を可視化し、自己の傾向を把握する。
- 気づき・受容・認知的再評価などの心理的スキルを身につける。

---

## 3. 機能要件

### 3.1 感情チェック（メイン機能）

| 項目 | 仕様 |
|---|---|
| 実施タイミング | 平日（月〜金）9:00〜18:00 の間にランダムで 1日3回 |
| 設問数/セッション | 1セッションあたり 10〜12問（約5分で回答可能） |
| 設問総数 | 200問（7カテゴリ） |
| 出題方式 | 200問からランダムに選出 |
| 回答形式 | 4段階リッカート尺度（1〜4） |

- 同一セッションのチェックイン画面は再アクセス時も同じ問題セットを表示する（セッションIDをシードにした固定サンプリング）

### 3.2 感情グラフ画面

- 日々の感情スコア推移グラフ（折れ線グラフ）
- カテゴリ別スコアのレーダーチャート
- 直近7日間・30日間の切り替え表示

### 3.3 リラクセーションメッセージ

- チェックイン画面・結果画面にリラックス・心落ち着かせる言葉を表示
- 名言・心理学的な知見に基づいたメッセージ（50件以上）

### 3.5 週末振り返りチェックイン

| 項目 | 仕様 |
|---|---|
| 対象曜日 | 土・日のみ |
| トリガー | ホーム画面を開いた際、当日のセッションが0件のとき |
| UI | モーダルダイアログで「振り返りチェックインを作成しますか？」を表示 |
| OK 操作 | `POST /api/sessions/weekend` を呼び出し、セッション1件を作成して画面リロード |
| 「後で」操作 | モーダルを閉じるだけ（その後の同じ日の再アクセスでもセッションが0件ならまた表示） |
| チェックイン時刻 | 18:00〜21:00 の間でランダムに1件生成 |
| 目的 | その日に平穏な心の状態を維持できたかを振り返るため |

### 3.4 通知機能

- スケジューラが毎朝0時に当日の3回分のチェックイン時刻を生成・保存
- フロントエンドが30秒ごとにポーリングし、チェックイン時刻になったらブラウザ通知を表示
- ブラウザ Notifications API を使用

---

## 4. 設問の出典・根拠

以下の検証済み心理尺度を参考に、日常的なセルフチェック用に編集した設問を使用する。

| カテゴリ | 参考尺度 | 日本語版出典 | 問数 |
|---|---|---|---|
| 怒り感情（状態・特性・表出・制御） | STAXI-2 日本語版 | PAR 社著作権保有・公開文献での邦訳確認不可 | 50問 |
| 感情調節困難 | DERS 日本語版 | 山田圭介・杉江征 (2013), *感情心理学研究* 20(3), 86–95. DOI: 10.4092/jsre.20.86 | 40問 |
| 認知的感情調節方略 | CERQ 日本語版 | 榊原良太 (2015), *感情心理学研究* 23(1), 46–58. | 40問 |
| マインドフルネス | FFMQ 日本語版 | Sugiura et al. (2012), *Mindfulness* 3(2), 85–94. DOI: 10.1007/s12671-011-0082-1 | 40問 |
| ストレスと対処 | PSS 日本語版 | 鷲見克典 (2006), *健康心理学研究* 19(2), 44–53. DOI: 10.11560/jahp.19.2_44 | 30問 |
| **合計** | | | **200問** |

> **注記**: 設問は上記尺度を参考に日常チェック用として再編集したものです。
> 医療診断目的ではなく、個人的な感情セルフモニタリングを目的としています。

---

## 5. 技術スタック

| レイヤー | 採用技術 | 選定理由 |
|---|---|---|
| バックエンド | Python 3.11 + FastAPI | 非同期対応・型安全・軽量 |
| テンプレートエンジン | Jinja2 | サーバーサイドレンダリングで簡素な構成 |
| データベース | SQLite + SQLAlchemy 2.x | Docker 内で完結・外部依存なし |
| スケジューラ | APScheduler 3.x | プロセス内スケジューリング |
| フロントエンド CSS | Bootstrap 5 | レスポンシブ・カスタマイズ容易 |
| グラフ | Chart.js 4.x | 軽量・日本語対応 |
| コンテナ | Docker + Docker Compose | ポータブルな実行環境 |
| CI/CD | GitHub Actions | pytest 実行 + Docker イメージビルド確認（push なし） |

---

## 6. アーキテクチャ

```
[ブラウザ]
    │  HTTP (port 8080)
    ▼
[Docker コンテナ]
    ├─ FastAPI (uvicorn)
    │    ├─ GET  /                  ホーム画面
    │    ├─ GET  /check-in          チェックイン画面
    │    ├─ POST /check-in/submit   回答送信・結果表示
    │    ├─ GET  /dashboard         グラフ・履歴画面
    │    ├─ GET  /api/status        チェックイン待ち確認 (polling)
    │    ├─ GET  /api/history       グラフ用データ取得
    │    └─ POST /api/sessions/weekend  土日の振り返りセッション生成
    ├─ APScheduler
    │    └─ 毎朝0時に当日チェックイン時刻を生成
    └─ SQLite (./data/tancha.db)
         ├─ check_in_sessions  チェックイン予定・実績
         ├─ check_in_answers   各設問への回答
         └─ emotional_scores   セッションごとのスコア集計
```

---

## 7. データベース設計

### check_in_sessions

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| access_token | VARCHAR(36) UNIQUE | UUID v4。結果ページURL に使用し、連番IDによる推測を防止する |
| scheduled_at | DATETIME | 予定時刻 |
| started_at | DATETIME | 開始時刻 |
| completed_at | DATETIME | 完了時刻 |
| status | VARCHAR | pending / in_progress / completed / skipped |

### check_in_answers

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK | |
| question_id | INTEGER | 設問ID (1〜200) |
| answer_value | INTEGER | 回答値 (1〜4) |
| answered_at | DATETIME | |

### emotional_scores

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK | |
| session_id | INTEGER FK | |
| date | DATE | |
| anger_score | FLOAT | 怒りスコア（低いほど良好） |
| regulation_score | FLOAT | 感情調節スコア（高いほど良好） |
| mindfulness_score | FLOAT | マインドフルネススコア（低いほど良好） |
| stress_score | FLOAT | ストレススコア（低いほど良好） |
| overall_score | FLOAT | 総合スコア (0〜100、高いほど良好)。計算式: (100-anger)×0.3 + (100-regulation)×0.2 + (100-stress)×0.2 + (100-mindfulness)×0.2 + (100-cognitive_regulation)×0.1 |

---

## 8. ディレクトリ構成

```
tancha-naran-do/
├── app/
│   ├── __init__.py
│   ├── main.py              FastAPI アプリ本体
│   ├── database.py          DB 接続・セッション管理
│   ├── models.py            SQLAlchemy モデル
│   ├── scheduler.py         APScheduler ジョブ定義
│   ├── questions_data.py    200問の設問データ
│   ├── messages_data.py     リラクセーションメッセージ
│   ├── scoring.py           スコア計算ロジック
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/
│   │       ├── notifications.js
│   │       └── dashboard.js
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── check_in.html
│       ├── result.html
│       └── dashboard.html
├── alembic/                 Alembic マイグレーションスクリプト
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_add_access_token_to_sessions.py
├── data/                    SQLite DB (Docker volume)
├── .github/
│   ├── workflows/
│   │   └── ci.yml           GitHub Actions CI
│   └── dependabot.yml       依存ライブラリ自動更新設定
├── alembic.ini              Alembic 設定ファイル
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── requirements-dev.txt
└── .gitignore
```

---

## 9. 画面設計

### 9.1 ホーム画面 (`/`)
- 今日のチェックイン状況（完了数/3回）
- 次回チェックイン予定時刻
- 最新のスコアサマリ
- リラクセーションメッセージ

### 9.2 チェックイン画面 (`/check-in`)
- ランダムに選出された10〜12問を表示
- プログレスバーで進捗表示
- 回答フォーム（ラジオボタン、1〜4段階）
- 画面上部にリラクセーションメッセージ

### 9.3 結果画面 (`/check-in/result`)
- セッションのスコア（カテゴリ別）
- 高スコア設問への解説とアドバイス
- 次のチェックイン予定時刻
- リラクセーションメッセージ

### 9.4 ダッシュボード画面 (`/dashboard`)
- 直近7日/30日の感情スコア折れ線グラフ
- カテゴリ別スコアのレーダーチャート
- チェックイン履歴一覧

---

## 10. 非機能要件

| 項目 | 仕様 |
|---|---|
| 実行環境 | Docker コンテナ（シングルコンテナ） |
| 外部依存 | なし（SQLite のみ使用） |
| データ永続化 | Docker volume (./data) |
| ポート | 8080 |
| ログ | stdout + `/data/logs/access.log`, `/data/logs/app.log`（RotatingFileHandler） |
| 認証 | なし（ローカル利用想定） |
| ヘルスチェック | `GET /health` → `{"status": "ok"}`（コンテナオーケストレーター向け） |

---

## 11. セキュリティ要件

### 11.1 HTTP セキュリティヘッダー（全レスポンス）

| ヘッダー | 値 |
|---|---|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; style-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; font-src https://cdn.jsdelivr.net data:; img-src 'self' data:; connect-src 'self'; form-action 'self'; base-uri 'self'; frame-ancestors 'none'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |

> **注記**: `X-XSS-Protection` は現代のブラウザでは非推奨のため削除。CSP ヘッダーで代替する。

### 11.2 入力バリデーション

| 項目 | 検証内容 |
|---|---|
| `session_id` | 正の整数のみ受付（非数値・0・負値 → 400） |
| `question_id` | 1〜200 の既存 ID のみ受付（範囲外・未定義 → 400） |
| `answer_value` | 1〜4 のみ受付（範囲外・非整数 → 400） |
| `days` パラメータ | 1〜365 の範囲（範囲外 → 422） |
| `limit` パラメータ | 1〜200 の範囲（範囲外 → 422） |
| 完了済みセッションへの再送信 | `status == "completed"` のセッションへの POST → 409 |

### 11.3 セッション識別子

- 各 `CheckInSession` は UUID v4 形式の `access_token` を持つ
- 結果ページ URL は `/check-in/result/{access_token}` の形式とし、連番整数による推測を防止する
- 既存セッション（DB 移行前）に対してはアプリ起動時に自動で UUID を付与する（`_migrate_access_tokens()`）
- Alembic マイグレーション `0001_add_access_token_to_sessions.py` でも対応可能

### 11.4 CSRF 保護

- `CsrfMiddleware` により POST リクエストの `Origin` / `Referer` ヘッダーを検証する
- `Origin` ヘッダーが存在し、リクエストホストと不一致 → 403 を返す
- `Origin` 不在で `Referer` ヘッダーが存在し、ホストを含まない → 403 を返す
- ヘッダーが存在しない場合（API クライアント・テストクライアント等）は許可する

### 11.5 レート制限

- `slowapi` ライブラリによる IP アドレス単位のレート制限
- `/check-in/submit`: 60回/分
- `/api/sessions/weekend`: 10回/分
- 制限超過時は 429 Too Many Requests を返す
- 環境変数 `DISABLE_RATE_LIMIT=true` で無効化（テスト時に使用）

### 11.6 その他

- API ドキュメント（`/docs`, `/redoc`, `/openapi.json`）はデフォルト非公開（`ENABLE_DOCS=true` で有効化）
- Docker コンテナは非 root ユーザー（`appuser`, UID=1000）で実行

---

## 12. ロギング仕様

### 12.1 出力先

| ログ種別 | stdout | ファイル |
|---|---|---|
| アクセスログ | ✓ | `/data/logs/access.log` |
| 業務操作ログ | ✓ | `/data/logs/app.log` |

### 12.2 ログフォーマット

```
YYYY-MM-DD HH:MM:SS LEVEL    logger_name          message
```

アクセスログには UUID v4 形式のリクエスト ID が含まれる：

```
2026-03-29 10:00:00 INFO     access               req_id=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx 127.0.0.1 GET / 200 12.3ms
```

リクエスト ID は `request.state.request_id` に格納されており、下流のハンドラーからも参照可能。

### 12.3 業務操作ログの出力タイミング

| イベント | レベル | 内容 |
|---|---|---|
| チェックイン開始 | INFO | `[CHECK-IN] session_id=N started` |
| 回答送信完了 | INFO | `[SUBMIT] session_id=N completed answers=10 overall_score=72.3` |
| 不正 session_id | WARNING | `[SUBMIT] Invalid session_id received: 'abc'` |
| 不正 question_id | WARNING | `[SUBMIT] Unknown question_id=999 session_id=N` |
| 範囲外 answer_value | WARNING | `[SUBMIT] Out-of-range answer_value=9 question_id=1 session_id=N` |
| 完了済みセッションへの再送信 | WARNING | `[SUBMIT] Already completed session_id=N` |
| CSRF 保護による拒否 | WARNING | `[CSRF] Rejected POST from Origin=... (expected host=...) path=...` |
| DB 操作エラー（スケジューラ） | ERROR | `Database error while generating daily sessions: ...` |

### 12.4 ローテーション設定

- 最大ファイルサイズ: 10 MB
- 保持世代数: 5（計最大 50 MB）
- 環境変数 `LOG_LEVEL`（デフォルト: `INFO`）でレベル制御

---

## 13. テスト戦略

### 13.1 TDD 運用方針

仕様の追加・変更・削除があるたびに、以下の順序で作業を行う：

1. **仕様変更を `development_background.md` に反映**
2. **テストを先に書く**（Red フェーズ）
3. **実装を行う**（Green フェーズ）
4. **リファクタリング**（Refactor フェーズ）
5. **テストを実行し、全件 PASSED を確認する**
6. 作業ブランチを作成し PR を出す（`main` への直接コミット禁止）

> **重要**: commit / push / PR 作成の前に、必ず `pytest` を実行してすべてのテストが通ることを確認すること。

### 13.2 テストスイート構成

```
tests/
├── conftest.py               # フィクスチャ（テスト用 DB・TestClient）
├── test_scoring.py           # スコア計算ロジックのユニットテスト
├── test_questions_data.py    # 設問データの整合性テスト
├── test_messages_data.py     # メッセージデータのユニットテスト
├── test_api.py               # HTTP エンドポイントの統合テスト
├── test_security.py          # セキュリティヘッダー・入力検証テスト
└── test_scheduler.py         # スケジューラのユニットテスト
```

### 13.3 テスト環境

| 項目 | 内容 |
|---|---|
| フレームワーク | pytest 9.x |
| HTTP クライアント | FastAPI TestClient (httpx) |
| テスト DB | SQLite インメモリ（`/tmp/tancha_naran_do_test.db`） |
| 時刻モック | freezegun |
| カバレッジ | pytest-cov |

### 13.4 テスト実行方法

```bash
# Docker コンテナ内で実行（推奨）
docker exec -w /app <container_id> python -m pytest tests/ -v

# カバレッジレポート付き
docker exec -w /app <container_id> python -m pytest tests/ --cov=app --cov-report=term-missing
```

### 13.5 テスト件数（2026-03-30 時点）

| テストファイル | テストクラス | テスト件数 |
|---|---|---|
| test_scoring.py | TestCalculateScores, TestGetScoreLabel | 26 |
| test_questions_data.py | TestQuestionsData, TestQuestionById | 17 |
| test_messages_data.py | TestRelaxationMessages, TestGetRandomMessage, TestGetMessages | 12 |
| test_api.py | 9クラス（全エンドポイント + 週末セッション） | 69 |
| test_security.py | 7クラス（ヘッダー・CSRF・ヘルスチェック・バリデーション・境界値） | 50 |
| test_scheduler.py | TestGenerateDailySessions, TestGenerateWeekendSession | 19 |
| **合計** | | **193** |

---

## 14. GitHub リポジトリ

- リポジトリ名: `tancha-naran-do`
- デフォルトブランチ: `main`
- **作業ブランチルール**: `main` への直接コミット禁止。必ず作業ブランチを作成してから作業する。

---

## 15. 変更履歴

| 日付 | 内容 |
|---|---|
| 2026-03-27 | 初版作成。要件・設計・技術スタック確定。 |
| 2026-03-27 | チェックイン時刻のチャイム通知機能を追加（Web Audio API）。 |
| 2026-03-27 | セキュリティ強化（入力検証・HTTPヘッダー・非 root 実行・ドキュメント非公開）。 |
| 2026-03-27 | アクセスログ・業務操作ログのファイル出力機能を追加（RotatingFileHandler）。 |
| 2026-03-27 | テストスイート新設（pytest, 161件）。TDD 運用方針を策定。 |
| 2026-03-28 | バグ修正・品質改善（overall スコア計算式修正、二重送信防止、セッション固定サンプリング、テスト追加）。 |
| 2026-03-28 | overall スコア計算修正: regulation_score を反転（DERS は高い=困難=悪い状態のため `(100-regulation)×0.2` に統一）。 |
| 2026-03-28 | 週末振り返りチェックイン機能を追加（§3.5）。土日にホーム画面でモーダルプロンプト表示、`POST /api/sessions/weekend` で 18:00〜21:00 にセッション生成。 |
| 2026-03-28 | GitHub Actions CI を再構成: pytest ジョブ → Docker build ジョブ（push なし）の2ジョブ構成に変更。スモークテストを pytest に置き換え。 |
| 2026-03-28 | セキュリティ強化（fix/security-hardening）: CSP ヘッダー追加、X-XSS-Protection 削除、SRI ハッシュ追加、キャッシュ制御、XSS 修正。§11.1 更新。 |
| 2026-03-28 | 依存パッケージ・GitHub Actions をすべて最新安定版に更新。GitHub Actions はコミットハッシュ固定に変更。 |
| 2026-03-28 | §4 設問出典を調査結果に基づき修正（CERQ: 橋本・田中 2005 → 榊原 2015、STAXI-2: 著作権確認不可として注記）。README.md に「出典・免責事項」セクション追加。 |
| 2026-03-29 | コードレビュー対応（全11項目）。詳細は以下のとおり。 |
| 2026-03-29 | [S-1] セッション識別子にランダムトークン（UUID v4）を導入。結果ページURLを `/check-in/result/{access_token}` 形式に変更し、連番整数による推測を防止。DB スキーマ変更: `check_in_sessions.access_token` カラム追加（§7, §11.3）。 |
| 2026-03-29 | [S-2] CSRF 保護ミドルウェアを追加（`CsrfMiddleware`）。Origin/Referer ヘッダーを検証し、クロスオリジンからの不正 POST を 403 で拒否（§11.4）。 |
| 2026-03-29 | [S-3] slowapi によるレート制限を導入。`/check-in/submit` 60回/分、`/api/sessions/weekend` 10回/分（§11.5）。 |
| 2026-03-29 | [C-1] `scheduler.py` の例外処理を具体化。`SQLAlchemyError` とその他の `Exception` を分離してログ出力を改善（§12.3）。 |
| 2026-03-29 | [C-2] アクセスログに UUID v4 形式のリクエスト ID を追加。リクエスト単位での追跡が可能に（§12.2）。 |
| 2026-03-29 | [O-1] ヘルスチェックエンドポイント `GET /health` を追加（§10）。 |
| 2026-03-29 | [O-2] Dependabot 設定（`.github/dependabot.yml`）を追加。pip および GitHub Actions の依存関係を週次で自動更新（§8）。 |
| 2026-03-29 | [O-3] Alembic マイグレーション基盤を追加（`alembic.ini`, `alembic/env.py`, `alembic/versions/0001_add_access_token_to_sessions.py`）。`requirements-dev.txt` に `alembic` を追加（§8）。 |
| 2026-03-29 | [T-1] スコア計算の境界値テストを6件追加（全回答値1/4・中間値・カテゴリ単独・認知的調節の方向性）。 |
| 2026-03-29 | [T-2] 並行送信によるスコア重複保存が発生しないことを確認するテストを追加（`ThreadPoolExecutor` 使用）。 |
| 2026-03-29 | テスト件数: 181 → 193 件（§13.5）。 |
| 2026-03-30 | バグ修正: mindfulness・cognitive_regulation の overall スコア方向を統一。逆転項目（reverse=True）の設計に合わせ、全カテゴリ「低い=良好」に統一。overall 計算式を `(100-mindfulness)×0.2 + (100-cognitive_regulation)×0.1` に修正（§7）。依存: alembic 1.16.1 → 1.18.4。 |
