# 이웃 수 build-time config (PRD: K >= TOPN_MAX). 에고 뷰 인원은 Top-N 슬라이더를 따른다
K = 30              # neighbors.json 저장 이웃 수 (인당 상한)
TOPN_MAX = 10       # 전체 뷰 Top-N 슬라이더 상한 (에고 뷰 인원 상한 겸용)

assert K >= TOPN_MAX
