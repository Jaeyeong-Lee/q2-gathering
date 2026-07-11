# 이웃 수 3계층 build-time config (PRD: K >= EGO_DISPLAY_N >= TOPN_MAX)
K = 30              # neighbors.json 저장 이웃 수 (인당 상한)
EGO_DISPLAY_N = 10  # 에고 뷰 표시 이웃 수
TOPN_MAX = 10       # 전체 뷰 Top-N 슬라이더 상한

assert K >= EGO_DISPLAY_N >= TOPN_MAX
