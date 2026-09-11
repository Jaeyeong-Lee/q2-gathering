> *출처: Claude 리서치 — 기존 OSS·정립 방법론 서베이 (2026-07-26), 입력 = `task-discovery-requirements.md`. AI 생성·실데이터 미검증 — 채택 전 검증 필요. 원문 그대로 보존.*

＝task-discovery 사전 조사: 기존 OSS·정립된 방법론 서베이＝

〖 TL;DR 〗
- 이 과제는 "n≈200 한국어 비정형 문서에서 상향식 주제 추출 → 계층적 종합 → 장기 로드맵 초안"이며, 각 단계마다 정립된 방법론과 성숙한 OSS가 이미 존재한다. 밑바닥 설계는 불필요하고, 채택 대상은 (A) LLM 기반 taxonomy induction(TnT-LLM/TopicGPT/LLooM), (B) 질적 코딩(reflexive TA/grounded theory 자동화 LOGOS), (C) map-reduce 종합(RAPTOR/GraphRAG 개념 차용), (D) T-Plan/Three Horizons(워크숍 산출물), (F) Instructor+tenacity+Presidio다.
- n≈200 소규모 코퍼스에서 BERTopic(UMAP+HDBSCAN)은 대량 outlier(단문·무의미 문서에서 최대 74%까지 -1 배정) 문제로 부적합에 가깝다. 소규모·노이즈·한국어 조건에서는 임베딩 클러스터링 단독보다 LLM 기반 라벨 유도(TnT-LLM/LLooM 계열)가 정답에 가깝다.
- 진짜 병목은 알고리즘이 아니라 (1) 로드맵은 데이터에 없다(상향식 근접미래 재료만 존재) → 최종 산출물은 완성 로드맵이 아니라 리더십 워크숍 입력이어야 하며, (2) 실데이터를 볼 수 없음 → i2b2/n2c2식 "합성 대체 코퍼스 + 보안경계 내 gold set + blinded 인간 검수" 워크플로가 정립된 해법이다.

〖 Key Findings (채택 판단 요약) 〗
- **채택**: TnT-LLM(Microsoft, taxonomy induction), LLooM/TopicGPT(concept induction), reflexive thematic analysis(Braun & Clarke) + grounded theory 코딩 프레임, map-reduce 계층 요약(LangChain load_summarize_chain), T-Plan(Cambridge/Phaal) + Three Horizons(리더십 워크숍 포맷), Instructor+Outlines(구조화 출력), tenacity(재시도), Presidio(가명화), BGE-M3(임베딩·이미 사내 보유).
- **부분 채택/보조**: BERTopic(탐색적 baseline·시각화용으로만, 최종 주제 추출 주엔진으로는 부적합), nori(ES BM25용, 이미 보유), Kiwi(형태소 분석 필요시).
- **과잉/부적합**: 본격 GraphRAG 파이프라인(엔티티 그래프+Leiden 커뮤니티는 QA 검색용, one-shot 종합엔 과잉), RAPTOR 전체 구현(검색시 QA용; "재귀 클러스터-요약" 아이디어만 차용), 기존 스킬 온톨로지(ESCO/O*NET/SFIA)를 반도체 후공정 테스트 SW에 강제 매핑(니치 도메인엔 상향식 taxonomy 유도가 우월).
- **정립된 해법 없음(맞춤 설계 필요)**: 근원경쟁력 문서 특유의 3부 구조 파싱 + CL별 이질성 처리, "무신호(열심히 하겠습니다)" 문서의 명시적 no-signal 판정 기준, 최종 로드맵의 도메인(후공정 테스트 SW) 특화 레이어링. 단, 이들도 아래 프리미티브(구조화 출력·no-signal enum·taxonomy induction) 위에서 조립하는 것이지 완전 신규 알고리즘은 아니다.

〖 A. 상향식 주제 추출 (Topic modeling / clustering / LLM taxonomy) 〗
**전통 topic modeling — n≈200에서는 신중히.**
- BERTopic(Grootendorst 2022, MIT, github.com/MaartenGr/BERTopic): 임베딩→UMAP→HDBSCAN→c-TF-IDF. 성숙·문서화 우수. **그러나 소규모 코퍼스 함정 명확**: 공식 FAQ와 이슈에서 (a) HDBSCAN이 min_cluster_size 미달 클러스터를 outlier(-1)로 버림, [KeyBERT](https://maartengr.github.io/BERTopic/faq.html) (b) UMAP이 작은 데이터에서 불안정, (c) 대량 -1 발생. 실증: de Groot et al. 2022(arXiv 2212.08459)는 대학 강의평가 단문 응답에서 "Approximately 74% of the student responses are classified as outliers, rendering HDBSCAN inappropriate for the analysis of university course evaluations, in which every response matters"라 명시하고, "When we replace HDBSCAN with k-Means, we achieve similar performance, but without outliers"로 k-Means 대안을 권고한다. 학계 20여 편 소코퍼스에서 절반이 outlier, 음수 coherence 사례도 보고됨(BERTopic Discussion #2465).
  - **완화책**: HDBSCAN 대신 k-Means로 교체(outlier 미발생), [GitHub](https://github.com/MaartenGr/BERTopic/discussions/2369) min_topic_size↓, UMAP n_neighbors 조정. 그래도 n≈200·노이즈·한국어에선 주엔진 부적합. **판단: 탐색적 baseline·시각화용으로만.**
- LDA/NMF: 짧고 노이즈 많은 한국어 자기서술엔 해석난해("tea leaves"), TopicGPT 논문도 baseline 대비 열위. **판단: 사용 안 함.**
- Top2Vec: BERTopic와 동일 계열(임베딩+HDBSCAN), 같은 소규모 문제. **판단: 별도 채택 이유 없음.**

**LLM 기반 / 하이브리드 — 이 과제의 정답 계열.**
- **TnT-LLM**(Wan et al., Microsoft/UW, KDD 2024, arXiv 2403.12173): 2단계. ①zero-shot 다단계 추론으로 label taxonomy를 반복 생성·정제, ②LLM으로 pseudo-label 후 경량 분류기 학습. [arXiv](https://arxiv.org/abs/2403.12173) "label space가 under-specified이고 대규모 주석이 없을 때" [arXiv](https://arxiv.org/abs/2403.12173) 정확히 이 과제 상황. 임베딩 클러스터링 baseline 대비 taxonomy 품질 우위 보고. [Microsoft](https://www.microsoft.com/en-us/research/publication/tnt-llm-text-mining-at-scale-with-large-language-models/) **채택 1순위(상향식 taxonomy 유도 프레임).** 단 사내 Qwen 계열로 taxonomy 생성이 GPT-4만큼 나올지는 검증 필요(아래 F).
- **LLooM**(Lam et al., Stanford/UW, CHI 2024, arXiv 2404.12259; github.com/michelle123lam/lloom, 연구 프로토타입): "concept induction" — 낮은 수준 키워드가 아니라 명시적 포함기준(inclusion criteria)을 가진 고수준 개념 생성. 논문에서 **최대 200개 샘플**로 5–15분 내 최대 20개 concept 생성하는 규모로 설계 → n≈200에 규모가 정확히 맞음. 데이터 커버리지도 우수: CHI 2024 평가에서 LLooM concept가 약 93% 커버리지로 클러스터 기반 topic model의 77.7%를 상회했고, 상호 포함관계는 "While 83.3% of BERTopic results were covered by LLooM, 62.5% of LLooM results were covered by BERTopic"로 보고됨. **채택(개념 유도 + provenance 확보).**
- **TopicGPT**(Pham et al., NAACL 2024, arXiv 2311.01449; github.com/chtmp223/topicGPT): 프롬프트 기반, 자연어 라벨+설명, 각 배정에 **근거 인용(quotation)** 부여 → provenance 내장(C의 traceability 요구에 직결). 인간 분류와 정합도는 "it achieves a harmonic mean purity of 0.74 against human-annotated Wikipedia topics compared to 0.64 for the strongest baseline"(최강 baseline 0.64 대비 0.74). **주의**: 논문 5.4에서 **topic generation은 GPT-4 외 오픈소스 LLM 모두 실패, topic assignment만 오픈모델(Mistral-7B) 가능** → 사내 LLM으로 생성 단계 품질 리스크. **채택하되 생성=최고성능 모델, 배정=경량 모델 분리 권고.**
- 기타: QualIT, Thematic-LM, HICode, TAMA 등 최신 파생 다수 존재(참고만).

**한국어 NLP 특이사항.**
- 형태소 분석기: nori(Lucene/ES 내장, mecab-ko-dic 기반) [Apache JIRA](https://issues.apache.org/jira/browse/LUCENE-8231?attachmentOrder=asc) 는 이미 보유 → BM25 인덱싱용으로 그대로 사용. 파이썬 형태소 필요시 **Kiwi**(빠르고 [Medium](https://medium.com/@autorag/making-benchmark-of-different-tokenizer-in-bm25-134f2f0e72f8) Java 불요, 정확도 양호) 또는 KoNLPy-Mecab. **판단**: 이 파이프라인은 임베딩(BGE-M3)+LLM 중심이라 형태소 분석 의존도 낮음. 명사 키워드 추출·BM25 하이브리드 검색에만 nori/Kiwi 사용.
- BGE-M3(BAAI, arXiv 2402.03216, MIT, 이미 사내 OpenAI-호환 엔드포인트 보유): 100+ 언어, [arXiv](https://arxiv.org/abs/2402.03216) 8192토큰, dense/sparse/multi-vector 통합. [arXiv](https://arxiv.org/abs/2402.03216) 한국어 성능 우수 평가 다수. 긴 PPT 텍스트(8192토큰) 처리에 유리. **그대로 채택.** 필요시 한국어 파인튜닝판(dragonkue/BGE-m3-ko) [Hugging Face](https://huggingface.co/dragonkue/BGE-m3-ko) 참고.
- 다국어 임베딩 클러스터링 주의: 언어·형식 혼재(한/영, PPT 파편) 시 임베딩이 주제보다 문체/언어로 뭉칠 수 있음 → 클러스터링 단독 신뢰 금물, LLM 라벨 검증 병행.

〖 B. 질적 연구 방법론 (스케일 질적 코딩) 〗
- 본질적으로 **질적 코딩의 자동화**다. 정립된 방법:
  - **Reflexive Thematic Analysis**(Braun & Clarke 2006/2019/2022, 6단계): 코드는 연구자 해석의 산물, [Springer](https://link.springer.com/article/10.1007/s11135-021-01182-y) **inter-coder reliability/Cohen's Kappa 추구를 명시적으로 지양**(Big Q). 즉 "정답 코드 재현"이 목표가 아님 → 리더십 논의 유발이 목적인 본 과제 철학과 정합.
  - **Codebook TA / Framework Analysis**: 팀 기반·구조화·일관성 중시 → 재현성 필요 시.
  - **Grounded Theory**(open→axial→selective coding, Glaser/Strauss, Charmaz): 계층적·관계적 이론 구축.
  - **KJ법 / Affinity Diagram**(Jiro Kawakita): 카드에 관찰을 적고 상향식 그룹핑 → 상위 테마 도출. 워크숍에서 인간이 하는 상향식 종합의 원형. LLM 클러스터-then-라벨은 KJ법의 자동화로 볼 수 있음.
- **LLM 보조 질적 코딩 — 정립도 상승 중이나 신뢰성 한계 문서화됨.**
  - LOGOS(Pi et al., arXiv 2509.24294): grounded theory 완전 자동화(open/axial/selective coding + 시맨틱 클러스터링 + 그래프 추론 + 반복 정제). [OpenReview](https://openreview.net/pdf/f7477a971d4626ede10cc53b2b50d66fbf034629.pdf) [ResearchGate](https://www.researchgate.net/publication/395968588_LOGOS_LLM-driven_End-to-End_Grounded_Theory_Development_and_Schema_Induction_for_Qualitative_Research) 전문가 스키마 정합률 88.2% 보고. [OpenReview](https://openreview.net/pdf/f7477a971d4626ede10cc53b2b50d66fbf034629.pdf) 청킹(2048단어/200겹침)→LLM 오픈코딩(Qwen3-32B로 청크당 최대 20코드)→임베딩(Qwen3-embed)→K-means→상위코드. [The Moonlight](https://www.themoonlight.io/en/review/logos-llm-driven-end-to-end-grounded-theory-development-and-schema-induction-for-qualitative-research) **사내 Qwen 계열과 스택 일치 → 참조가치 높음.**
  - LLM-in-the-loop(Dai et al., EMNLP 2023 Findings), DeTAILS(arXiv 2510.17575), Thematic-LM, TAMA 등.
  - **문서화된 신뢰성 우려**: LLM은 해석·추상보다 서술 요약에 치우침, 문화·맥락·저확률 대안 탐색 실패, 긴 데이터 일관성 저하( [Sage Journals](https://journals.sagepub.com/doi/10.1177/10497323251365211) SAGE Qual Health Res 2026; De Paoli 2024). → **인간 감독 필수.**
- **분석자가 데이터 대부분을 볼 수 없을 때의 코드/테마 검증**: (1) 보안경계 내 double-annotation + arbitration으로 gold set 구축(i2b2/n2c2 패턴), (2) blinded 인간 vs LLM 비교(medRxiv 2025 blinded mixed-methods), (3) Cohen's Kappa + 코사인 유사도 이중 지표(arXiv 2512.20352), (4) De Paoli & Mathis의 Initial Thematic Saturation.

〖 C. 계층적 종합 / synthesis 아키텍처 〗
- **RAPTOR**(Sarthi et al., Stanford, ICLR 2024, arXiv 2401.18059; github.com/parthsarthi03/raptor): 청크를 재귀적으로 임베딩→클러스터(GMM 소프트)→요약해 상향식 트리 구성. [Liner](https://liner.com/review/raptor-recursive-abstractive-processing-for-treeorganized-retrieval) [arxiv](https://arxiv.org/pdf/2606.20900) **본질은 검색시 QA용**(collapsed tree retrieval). one-shot 코퍼스 종합엔 트리 전체가 과잉. **차용할 것: "재귀 클러스터-요약으로 추상화 레벨 트리" 아이디어만.** 사내 커스텀 임베딩/LLM 주입 가능(BaseSummarizationModel 확장). [GitHub](https://github.com/parthsarthi03/raptor)
- **GraphRAG**(Edge et al., Microsoft, arXiv 2404.16130; microsoft.github.io/graphrag, MIT): 엔티티 지식그래프→Leiden 커뮤니티 탐지→커뮤니티 요약(map-reduce)→global sensemaking. [Microsoft](https://www.microsoft.com/en-us/research/publication/from-local-to-global-a-graph-rag-approach-to-query-focused-summarization/) Microsoft Research 공식 발표(2024)는 "GraphRAG, when using community summaries at any level of the community hierarchy, outperforms naive RAG on comprehensiveness and diversity (~70–80% win rate)"로 naive RAG 대비 70–80% 승률을 보고한다. **적합성 판단**: 개념(커뮤니티 요약=상향식 테마 종합)은 본 과제와 유사하나, **엔티티 그래프 구축은 200개 자기서술 종합엔 과잉**이고 반복 global query가 없는 one-shot엔 비용 대비 이득 낮음. **차용할 것: map-reduce 커뮤니티 요약 계층 구조 발상.**
- **LangChain map-reduce**(load_summarize_chain, chain_type="map_reduce"/"refine"/"stuff"): 정립된 종합 패턴. map=문서별 요약(병렬), reduce=요약의 요약. [Medium](https://medium.com/@atef.ataya/map-reduce-building-summarization-apps-with-langchain-and-openai-57c05788c7eb) n≈200 one-shot 종합의 표준 뼈대. token_max 초과 시 collapse 반복. [kioku-space](https://kioku-space.com/en/langchain-summarization-2/) **채택(종합 단계 기본 골격).** stuff=소량, map_reduce=다수·병렬, refine=순서·서사 중요 시. [Medium](https://medium.com/@sonimegha1602/scaling-document-summarization-with-llms-stuffing-map-reduce-and-refine-a8a468d479c3)
- **알려진 실패 모드(반드시 리더십에 고지)**: (1) 환각적 종합(없는 방향을 지어냄), (2) provenance 소실(테마→원문 추적 불가), (3) 소수 신호 over-smoothing(map-reduce 요약이 다수 의견에 눌려 소수 역량/이견 소거). 특히 (3)은 "팀의 꿈·미래 씨앗"이 소수 의견에 있을 수 있어 치명적.
- **Provenance/traceability(리더십이 결론을 반박할 것이므로 필수)**: TopicGPT식 배정근거 인용, LLooM의 명시적 inclusion criteria, 각 테마에 기여 문서 ID·발췌 인용 유지. PII-Codex는 "출력에 원문 대신 탐지 위치만" 방식으로 provenance와 개인정보 보호를 동시 달성.

〖 D. 로드맵핑 / foresight (출력 포맷) 〗
- **T-Plan / Fast-Start Roadmapping**(Phaal, Farrukh, Probert, Univ. of Cambridge IfM, 2001; ISBN 978-1-902546-09-4): 최소 자원 워크숍 기반 기술·제품 로드맵. [Institute for Manufacturing](https://www.ifm.eng.cam.ac.uk/insights/roadmapping/t-plan/) "why-what-how-when" 다층 레이어링, linkage grid로 시장-제품-기술 연결. [Institute for Manufacturing](https://www.ifm.eng.cam.ac.uk/uploads/Research/CTM/Roadmapping/roadmapping_overview.pdf) **워크숍 방법론 — 자동화 불가, 인간 숙의 필수.** 자원 적은 조직·로드맵 초심자에 최적 [Institute for Manufacturing](https://www.ifm.eng.cam.ac.uk/insights/roadmapping/t-plan/) → 본 과제에 정확히 부합. S-Plan(전략 변형)도 동일 계열.
- **Three Horizons**(Baghai/Coley/White 1999 McKinsey; Sharpe & Hodgson 삼지구조, Curry & Hodgson 2008): H1(현행 핵심)·H2(신흥 기회)·H3(변혁적 미래). [ResearchGate](https://www.researchgate.net/publication/379924972_Strategic_Foresight_in_Action_Leveraging_McKinsey's_3_Horizon_Model_for_Balanced_Financial_and_Strategic_Planning) 상향식 근접미래 과제(H1/H2 재료)를 장기(H3) 지평으로 확장하는 프레임 → "10년"을 문자 그대로가 아닌 해석 프레임으로 쓰라는 요구와 정합. ITC-ILO 등 워크숍 툴킷 다수 공개.
- **상향식 실무자 입력을 소비하도록 설계된 foresight 방법**: Horizon Scanning(약신호·트렌드 수집→시나리오 입력), [Shapingtomorrow](https://shapingtomorrow.com/files/media-centre/pf-ch03.pdf) Delphi(전문가 반복 합의/이견), [Jfsdigital](https://jfsdigital.org/a-comparative-analysis-of-delphi-method-and-horizon-scanning/) Scenario Planning(불확실성 축→복수 미래), Backcasting(바람직한 미래→현재 역산), [Shapingtomorrow](https://shapingtomorrow.com/files/media-centre/pf-ch03.pdf) Futures Wheel. **대부분 워크숍·인간 숙의 전제 — 자동화 불가.** Horizon Scanning은 "business-as-usual 외삽 편향" 한계 문서화. [Jfsdigital](https://jfsdigital.org/a-comparative-analysis-of-delphi-method-and-horizon-scanning/)
- **핵심 판단(명시)**: 위 방법들은 전부 **인간 워크숍·숙의**가 본질이며 파이프라인으로 자동 산출 불가. 데이터에 로드맵이 없다는 제약(cautions #1,#2)과 결합하면, **사용자의 실제 산출물은 완성된 10년 로드맵이 아니라 T-Plan/Three Horizons 워크숍의 사전 입력물**(테마 지도, 역량 갭, 모멘텀, 이견 지점)이어야 한다. 파이프라인은 워크숍 재료를 제공하고, 로드맵 자체는 리더십이 워크숍에서 만든다.

〖 E. 역량 / 스킬 매핑 〗
- 기존 스킬 taxonomy/온톨로지: **ESCO**(EU, 13,939 스킬, [arxiv](https://arxiv.org/pdf/2503.12989) 27개 언어, 다국어), [arxiv](https://arxiv.org/pdf/2305.12092) **O*NET**(US 노동부, 직업-스킬-지식), [arxiv](https://arxiv.org/pdf/2101.11431) **SFIA**(Skills Framework for the Information Age, 디지털/IT 스킬, 7단계 책임 레벨, [Umbrex](https://umbrex.com/resources/frameworks/organization-frameworks/skills-and-competency-frameworks-e-g-sfia/) 전문가 큐레이션). [Publishing Service](https://assets.publishing.service.gov.uk/media/628cd6988fa8f55622a9c92a/Review_of_skills_taxonomies_report_prepared_for_the_SPB_May_2022.pdf) Lightcast, WEF Global Skills Taxonomy 등도 존재.
- 자유서술 자기보고 역량을 taxonomy에 매핑하는 실무: SkillNER(ESCO 매핑), ESCOXLM-R(다국어 사전학습), SkillMatch(스킬문장 분류→ESCO 시맨틱 검색), [arxiv](https://arxiv.org/pdf/2510.01470) 최근 LLM taxonomy-guided reasoning(arXiv 2503.12989). [arxiv](https://arxiv.org/pdf/2503.12989) 통상 임베딩 시맨틱 유사도 + 확신도 점수 + 크로스워크.
- **핵심 판단(니치 도메인)**: 반도체 후공정(테스트 SW) 역량은 ESCO/O*NET/SFIA의 일반 IT 스킬 그물로는 포착 안 됨(도메인 특수 용어·암묵지). **기존 온톨로지에 강제 매핑은 부적합, 상향식 taxonomy induction이 우월**(TnT-LLM/LLooM으로 근원경쟁력 텍스트에서 역량 taxonomy를 직접 유도). SFIA의 레벨/책임 축은 CL2/3/4 커리어레벨과 교차분석하는 **참조 프레임**으로만 활용. 즉 온톨로지는 "정답표"가 아니라 사후 정합성 점검(legibility check)용.

〖 F. 실무 엔지니어링 패턴 〗
**배치 LLM 처리(≈200명, rate limit·재시도·부분실패).**
- **tenacity**(Apache-2.0): 표준 재시도 라이브러리. `wait_random_exponential(min, max)` + `stop_after_attempt` [Scale](https://llm-engine.scale.com/guides/rate_limits/) + `retry_if_exception_type(RateLimitError...)` [Learnwithparam](https://www.learnwithparam.com/blog/retry-patterns-llm-api-errors-production) + **jitter**(200개 동시요청 동기화 방지). [Learnwithparam](https://www.learnwithparam.com/blog/retry-patterns-llm-api-errors-production) 4xx(BadRequest/Auth)는 재시도 제외. [Learnwithparam](https://www.learnwithparam.com/blog/retry-patterns-llm-api-errors-production) **채택.**
- 다층 재시도 함정(문서화됨): 클라이언트 SDK 내장 재시도 + 프레임워크 재시도 + 자체 wrapper가 겹치면 429 악화 [Nikhil-verma](https://nikhil-verma.com/blog/rate-limiting-llm-apis-distributed-workers/) → **재시도 계층 단일화** 필요.
- 아이디어멘시·부분실패: 사람별 결과를 영속 저장(DB/파일)해 재개 가능하게, 실패는 로그 후 계속(graceful degradation), [arxiv](https://arxiv.org/pdf/2601.01576) 폐기 실패분 명시 추적. LangChain `.with_retry()` [Langchain](https://docs.langchain.com/langsmith/rate-limiting) 또는 전용 배치 러너 패턴 참고.
**노이즈 문서 구조화 추출(로컬 LLM).**
- **구조화 출력 3계열**: (1) **Instructor**(github.com/jxnl/instructor, Pydantic + 재검증·재프롬프트, [Ankur-singh](https://ankur-singh.github.io/blog/structured-output) OpenAI-호환·Ollama·llama.cpp 지원) [Instructor](https://python.useinstructor.com/blog/2024/03/07/open-source-local-structured-output-pydantic-json-openai/) — OpenAI-호환 엔드포인트에 `instructor.from_openai(..., mode=Mode.JSON)` [Instructor](https://python.useinstructor.com/blog/2024/03/07/open-source-local-structured-output-pydantic-json-openai/) 로 바로 사용, **채택 1순위**. (2) **Outlines**(dottxt, 문법/정규식 기반 constrained decoding, 로짓 마스킹으로 스키마 100% 보장, [Loraexchange](https://loraexchange.ai/guides/structured_output/) vLLM/SGLang 통합) [Bento](https://bentoml.com/llm/getting-started/tool-integration/structured-outputs) — 스키마 강제력 최상, 로컬 서버에 적합. (3) **llama.cpp/Ollama grammars(GBNF)**, LM Format Enforcer, XGrammar, Guidance. **판단**: Instructor(재프롬프트, 유연) + Outlines/문법(강제, 저지연) 병용. OpenAI structured output "strict" 모드는 스키마 준수 35%→100% 개선 보고. [Medium](https://medium.com/@docherty/mastering-structured-output-in-llms-choosing-the-right-model-for-json-output-with-langchain-be29fb6f6675)
- **무신호 문서의 우아한 저하(핵심 요구)**: JSON 스키마에 명시적 `signal_present: bool`, `capabilities: list`(빈 배열 허용), `confidence: enum[none/low/med/high]` 필드를 두고, "열심히 하겠습니다"류엔 **날조 대신 no-signal 반환**하도록 프롬프트+스키마 강제. Instructor validator로 "빈 근거인데 역량 채움" 케이스 재프롬프트. LLooM의 outlier 클래스(not-covered / covered-by-generic) 개념 차용.
**실데이터 없이 파이프라인 개발·평가(정립된 해법 존재).**
- **합성 대체 코퍼스**: 보안경계 내에서 비민감 집계통계·스키마만 추출 → 스키마·분포를 맞춘 합성 surrogate 생성(Mock-CAIS식 결정적 3단계 생성; LGPD 사례 arXiv 2606.28479). LLM 생성 + 원어민 검수로 저자원 코퍼스 구축(NagaNLP, arXiv 2512.12537). → **가짜 이름·CL·pjt로 한국어 근원경쟁력 합성 코퍼스를 만들어 경계 밖 개발.**
- **보안경계 내 gold set + arbitration**: Stubbs & Uzuner의 2014 i2b2/UTHealth de-id 코퍼스(J Biomed Inform 2015, 58:S20–S29)가 표준 선례 — 296명 환자의 1,304건 종단 의무기록을 double-annotation→arbitration→sanity check로 구축했고 "The average token-based F1 measure for the annotators compared to the gold standard was 0.927"(시스템 최고 entity-based micro F1 0.936). n2c2, MIMIC-III 대체 PHI 평가도 동일 패턴.
- **Five Safes / validation server 모델**(arXiv 2510.05803): 연구자는 합성데이터로 분석 작성 → 데이터 관리자가 실데이터에서 실행·안전성 확인 후 결과만 반출(US Census SIPP Synthetic Beta). 물리/가상 enclave 구분.
- **blinded 인간 검수 프로토콜**: LLM vs blinded 인간 동일 과제 수행 → 전문가 합의 패널이 reference standard 구성 → 정합도 정량화(medRxiv 2025). De Paoli 2024(SSCR, DOI 10.1177/08944393231220483): 공개 인터뷰의 기존 인간 분석 대비 LLM 귀납 TA 검증 — 주요 테마 대부분 추론, "good degree of validity". 지표: Cohen's Kappa, F1, 코사인 유사도, Initial Thematic Saturation.
- **권고 워크플로**: ①경계 내 집계·스키마 추출 → ②합성 surrogate로 개발·반복 → ③경계 내 double-annotation+arbitration gold set → ④blinded 인간 검수 + 정량지표로 검증 → ⑤검증된 집계 결과만 반출.
**익명화 / PII(실명 포함).**
- **Microsoft Presidio**(github.com/microsoft/presidio, MIT, 완전 오프라인 가능 — 코어 파이프라인 외부호출 없음, 텔레메트리 없음): 한국 구조화 PII 인식기 내장(KR_RRN 주민번호 체크섬, KR_FRN, KR_DRIVER_LICENSE, KR_BRN 사업자번호, KR_PASSPORT; ko/kr 언어코드, 기본 비활성 → 활성화 필요). **단 한국어 인명(PERSON)은 전용 인식기 없음** — NLP 엔진 NER 모델(spaCy ko_core_news_*, 또는 KLUE-BERT NER HuggingFace 모델)을 꽂아야 하고, Presidio 문서가 한국어 교착어 특성상 SpacyRecognizer 대신 HuggingFaceNerRecognizer 권고. Custom PatternRecognizer(사내 직원명 deny-list)로 보강 가능. 배포는 pip 또는 온프렘 Docker/K8s. **주의**: Azure 계열 인식기는 클라우드 → 에어갭 금지, 로컬(spaCy/Stanza/HF/GLiNER/Ollama)만 사용. **채택.**
- 한국어 특화 de-id 선례: KLUE-BERT NER 기반 한국어 EMR 비식별(npj Health Systems 2025, DOI 10.1038/s44401-025-00036-1, Asan Medical Center) — "The KLUE BERT model, trained on an augmented dataset, achieved an F1 score of 91.42% on the internal validation set and maintained 94.30% on real discharge summary data ... it outperformed LLMs in recognizing more than 200 categories of sensitive entities"(비교 대상 LLM은 Llama3-Open-Ko-8B, EEVE-Korean-Instruct-10.8B). PII-Codex(JOSS 2023, DOI 10.21105/joss.05402, Presidio+spaCy 기반, 위험도 점수화, 출력에 원문 미포함).
- **가명화 표준 패턴**: 탐지→플레이스홀더/토큰 치환(홍길동→person_1)→LLM 처리→필요시 rehydration, 매핑표는 로컬에만 보관·전송 금지(가역 토큰화). **판단**: LLM이 경계 내에서 도는 완전 에어갭 one-shot에서는 외부유출 방지 목적상 필수는 아니나, 로그·임베딩·출력의 재식별 위험 감소를 위한 defense-in-depth 권고 기본값. 근원경쟁력 분석 결과물은 실명 대신 가명·집계로 반출.

〖 Recommendations (단계별) 〗
1. **프레이밍 재정의(즉시)**: 산출물을 "완성 10년 로드맵"이 아니라 **T-Plan/Three Horizons 워크숍 입력물**(테마 지도 + 역량 갭 + 모멘텀 방향 + 소수·이견 신호 + 각 항목 provenance)로 상신 재정의. 데이터에 없는 sequencing/dream은 워크숍에서 인간이 생성. 벤치마크: 리더십이 "이걸로 논의를 시작할 수 있다"고 하면 성공. 완성 로드맵을 요구하면 재협상.
2. **추출 엔진 선정(우선순위)**: 주엔진 = **TnT-LLM식 taxonomy induction**(상향식 역량·방향 taxonomy 생성) + **LLooM/TopicGPT식 concept induction**(명시적 기준·근거 인용으로 provenance 확보). BERTopic은 **탐색적 baseline/시각화용으로만** 병행. 순수 임베딩 클러스터링 단독 결정 금지.
3. **구조화 추출 계층 구축**: Instructor(+Outlines/문법)로 사람별 JSON 추출 스키마 정의 — 반드시 `signal_present`, `no_signal` 경로, confidence enum 포함해 무의미 문서에 날조 금지. CL2/3 3부 구조와 CL4 자유서술을 각기 다른 프롬프트/스키마로 분기.
4. **종합 계층**: LangChain map-reduce(map=사람별 역량/방향 추출, reduce=테마 종합)를 뼈대로, RAPTOR의 "재귀 클러스터-요약", GraphRAG의 "커뮤니티 요약" 발상을 차용. **소수 신호 보존 장치 필수**(reduce 단계에서 minority theme 별도 트랙 유지).
5. **배치 실행 견고화**: tenacity 단일 재시도 계층(jitter, 4xx 제외) + 사람별 결과 영속화 + 부분실패 graceful degradation + 폐기분 로그.
6. **데이터-블라인드 개발/검증**: 가짜 이름·CL·pjt로 **한국어 합성 대체 코퍼스** 생성 → 경계 밖 개발·반복. 보안경계 내에서 소규모 **gold set(double-annotation+arbitration)** 구축, blinded 인간 검수 + Cohen's Kappa/F1로 검증. 실데이터엔 최종 파이프라인만 반입.
7. **PII**: Presidio(MIT, 오프라인) + 한국 KR_* 인식기 활성화 + 한국어 인명은 KLUE-BERT/spaCy-ko NER 또는 사내 직원명 deny-list custom recognizer. 가명화(person_1) 후 처리, 결과는 가명·집계로만 반출.
8. **역량 매핑**: 상향식 taxonomy 유도를 기본으로, SFIA 레벨·CL 교차분석은 사후 참조 프레임으로만. ESCO/O*NET 강제 매핑 금지.

**판단을 바꿀 임계치**: (a) 사내 Qwen LLM이 taxonomy **생성** 단계에서 GPT-4급 품질을 못 내면(TopicGPT 경고) → 생성은 최고성능 사내모델/외부반입 불가 시 인간 시드 taxonomy로 대체하고 LLM은 배정만. (b) 무신호 문서 비율이 높으면(예: 30%↑) → no-signal 판정을 사전 필터로 승격. (c) 리더십이 재현성·감사를 강하게 요구하면 reflexive TA → codebook TA/framework analysis로 전환하고 Kappa 도입.

〖 Caveats 〗
- 로드맵의 sequencing·전략·"꿈"은 데이터에 부재. 파이프라인이 생성하면 환각. 반드시 워크숍 산출물로 한정.
- map-reduce 종합의 소수신호 over-smoothing이 이 과제의 최대 위험(팀의 미래 씨앗이 소수 의견일 수 있음).
- 사내 Qwen 계열의 한국어 taxonomy 생성 품질은 미검증 — 실측 필요.
- Presidio 한국어 인명 인식은 별도 NER 모델 의존, 재현율 보장 없음 → gold set로 검증.
- LLM 질적 코딩은 해석·맥락에서 인간에 못 미침(문서화된 한계) → 인간 감독 필수.
- Presidio MIT/오프라인·KR_* 인식기 버전은 배포 버전의 LICENSE·CHANGELOG로 직접 재확인 필요.
- LLooM/LOGOS 등은 연구 프로토타입 — 프로덕션 성숙도 낮음, 아이디어·부분 차용 위주.
