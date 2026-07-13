# 실데이터 전처리 파이프라인 다이어그램 (sqlite 버전)

`data/roster.db`의 `roster` 테이블 하나가 로스터 + 파이프라인 상태의 단일 소스다.
각 단계는 행을 append하지 않고 **`seq` 기준 `UPDATE`**만 하므로, 중간에 끊겨도
재실행하면 이미 채워진 컬럼(배정 완료·정제 완료)은 자동으로 스킵된다.

```
┌────────────────────────────────────────────────────────────────────┐
│ 0단계: import_roster.py (1회성)                                      │
│                                                                      │
│  master.json ──▶ data/roster.db 의 roster 테이블 생성 + INSERT       │
│                    ┌──────────────────────────────────────┐        │
│                    │ seq(PK), name, pjt, part, cl_level,   │        │
│                    │ source_file, source_file_seq          │        │
│                    │ page_start/end, status: (아직 비어있음)│        │
│                    │ split_filename, normalized_filename    │        │
│                    └──────────────────────────────────────┘        │
│  ※ 이후 master.json 폐기, roster.db가 유일한 소스 (DB 툴로 직접 편집)│
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼  (같은 roster 테이블을 계속 재사용)
┌────────────────────────────────────────────────────────────────────┐
│ 1단계: split_md_by_person.py  (물리 파일별로 여러 번 실행)            │
│                                                                      │
│  cl2_y5-8_1.md ──▶ SELECT * FROM roster WHERE source_file=?         │
│  cl2_y5-8_2.md ──▶ (파일별로 따로, cat 금지)                         │
│         │                                                           │
│         ├──▶ [assign_pages] ──▶ 사람별 원문 파일                     │
│         │                        data/raw_sections/                 │
│         │                        <pjt>__<part>__<name>.md           │
│         │                                                           │
│         └──▶ UPDATE roster SET page_start, page_end,                │
│                                 status, split_filename               │
│                                 WHERE seq=?  (행 신규 생성 아님)      │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼  (roster 테이블 다시 읽음)
┌────────────────────────────────────────────────────────────────────┐
│ 2단계: normalize_person_text.py                                     │
│                                                                      │
│  SELECT * FROM roster                                               │
│    → status=='정상' AND normalized_filename 비어있는 행만 필터(파이썬)│
│    → split_filename md 읽어서 LLM(gpt-oss, internal) 호출             │
│    → data/raw_sections/xxx.normalized.md 저장                       │
│                                                                      │
│  UPDATE roster SET normalized_filename=? WHERE seq=?  (행별 개별)    │
└────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼  (roster 테이블 다시 읽음)
┌────────────────────────────────────────────────────────────────────┐
│ 3단계: merge_persons.py                                             │
│                                                                      │
│  SELECT * FROM roster                                               │
│    → normalized_filename 채워진 행만 대상                           │
│    → text = split_filename md (원문, 임베딩·워드클라우드·태그용)      │
│    → normalized_text = .normalized.md (정제본, 상세 패널 표시용)      │
│    → {id, name, pjt, part, cl_level, text, normalized_text, tags:[]}│
│                                                                      │
│  ▶ data/persons.json 최종 산출                                       │
└────────────────────────────────────────────────────────────────────┘
```

## 실행 명령 요약

```bash
# 0단계 (1회만)
python scripts/import_roster.py <master.json 경로>

# 1단계 (물리 md 파일마다 반복, cat 금지)
python scripts/split_md_by_person.py <md 파일 경로>

# 2단계 (내부망, TEXT_PROVIDER=internal 등 env 세팅 후)
python scripts/normalize_person_text.py

# 3단계
python scripts/merge_persons.py
```

## 막혔을 때

- `status='이상'` 행 확인: `sqlite3 data/roster.db "SELECT name, page_start, page_end FROM roster WHERE status='이상'"`
- 정제 안 된 사람 확인: `sqlite3 data/roster.db "SELECT name FROM roster WHERE status='정상' AND (normalized_filename IS NULL OR normalized_filename='')"`
- 어떤 단계든 재실행 안전 — 이미 채워진 행은 건너뛰고 빈 행만 다시 처리한다.
