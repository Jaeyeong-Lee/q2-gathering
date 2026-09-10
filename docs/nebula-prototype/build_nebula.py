"""Synthetic-only presentation; previous atlas is read only for synthetic identities/layout."""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SEED = Path('/Users/winter/orca/workspaces/q2-gathering/auk/data/td_sample/people-atlas/synthetic-input.json')
# Each PJT has its own categories, task objects and explicitly linked capability evidence.
LOCAL = [
 [('병렬 테스트', '멀티사이트 실행 조건', '테스트 프로그램 분석', '병렬 실행 설계'), ('검증 누락 줄이기', '테스트 항목 검증 절차', '검증 항목 리뷰', '테스트 커버리지 분석'), ('실행 시간 최적화', '프로그램 병목 구간', '실행 로그 분석', '성능 모델링')],
 [('수율 변동 추적', '제품별 수율 변동', '통계적 공정관리', '변동 원인 모델링'), ('불량 패턴 진단', '반복 불량 패턴', '불량 로그 분류', '이상 탐지 모델 검증'), ('분석 재현성', '양산 분석 절차', '분석 스크립트 작성', '분석 환경 버전 관리')],
 [('열화 메커니즘', '온도별 열화 특성', '신뢰성 시험 운영', '수명 분포 해석'), ('시험 조건 설계', '사용 환경별 시험 조건', '시험 결과 비교', '가속 시험 설계'), ('장기 불량 재현', '장시간 시험의 불량 재현', '불량 시료 분석', '복합 스트레스 분석')],
 [('정비 시점 판단', '설비 정비 시점', '센서 이력 분석', '고장 예측 검증'), ('장비 편차 줄이기', '장비 간 설정 편차', '설비 조건 점검', '편차 보정 설계'), ('조작 절차 자동화', '반복 장비 조작', '장비 제어 스크립트', '자동 실행 복구 설계')],
 [('기록의 연결', '테스트·설비 공통 식별자', '데이터 파싱', '데이터 모델 설계'), ('데이터 품질', '수집 데이터의 정합성', '누락 데이터 검사', '데이터 품질 규칙 설계'), ('분석 기반 공유', '재사용 가능한 분석 환경', '분석 환경 운영', '공통 인터페이스 설계')],
 [('품질 전조 포착', '품질 이상 전조', '품질 이력 추적', '전조 탐지 평가'), ('원인 검증', '불량 원인 검증 절차', '원인 후보 비교', '인과 검증 실험 설계'), ('판정 기준 정교화', '품질 판정 기준', '검사 결과 분석', '측정 불확도 평가')],
 [('초기 검증 표준', '신제품 초기 검증', '초기 검증 운영', '검증 범위 설계'), ('변경 영향 추적', '제품 변경 영향', '변경 이력 관리', '영향 범위 분석'), ('전개 경험 재사용', '이전 제품의 검증 경험', '제품 전개 조율', '경험 이전 기준 설계')],
 [('기술 경험의 전수', '문제 해결 경험', '기술 사례 문서화', '지식 구조 설계'), ('투자 판단의 근거', '기술 투자 비교 기준', '운영 지표 분석', '불확실성 시나리오 분석'), ('기술 검증의 설계', '새 기술의 파일럿 검증', '검증 일정 조율', '실험 성공 기준 설계')]
]

def build():
    original = json.loads(SEED.read_text())
    people = [{k:p[k] for k in ('id','name','pjt','cl','x','y')} for p in original['people']]
    rng = random.Random(911)
    cats, tasks = [], []
    for pi, entries in enumerate(LOCAL):
        for ci,(name,obj,have,gap) in enumerate(entries):
            cats.append(dict(id=f'{pi}-{ci}',pjt=pi,name=name,object=obj,have=have,gap=gap))
    for p in people:
        p['text']=''
        for index in range(2+(p['id']%5==0)):
            ci=(p['id']+index)%3
            c=cats[p['pjt']*3+ci]
            horizon=rng.choices(['short','long','unknown'],[.43,.39,.18])[0]
            when={'short':'단기적으로는 ','long':'장기적으로는 ','unknown':''}[horizon]
            action=rng.choice(['를 개선하는 검증 사례를 만들고 싶다.','를 비교하고 팀에서 반복해서 쓸 수 있는 절차로 정리하고 싶다.','의 기준을 정교하게 만들고 현장 적용까지 확인하고 싶다.'])
            quote=when+c['object']+action
            skills=[]
            if (p['id']+index)%7!=0:
                skills.append(dict(kind='have',label=c['have'],quote=f"이 과제에는 기존에 수행했던 {c['have']} 경험을 활용하려 한다."))
            if (p['id']+index)%4!=0:
                skills.append(dict(kind='gap',label=c['gap'],quote=f"이를 추진하려면 {c['gap']} 역량을 추가로 확보할 필요가 있다."))
            if (p['id']+index)%6==0:
                skills.append(dict(kind='gap',label='현장 검증 설계',quote='이를 현장에 적용하기 위한 검증 설계 역량도 더 필요하다.'))
            task=dict(id=f"{p['id']}:{index}",person=p['id'],pjt=p['pjt'],category=c['id'],horizon=horizon,quote=quote,skills=skills,seed=rng.random())
            tasks.append(task)
            p['text']+=quote+'\n'+'\n'.join(s['quote'] for s in skills)+'\n\n'
    data=dict(people=people,tasks=tasks,categories=cats,pjts=original['pjts'],edges=original['edges'],synthetic=True)
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    html=(ROOT/'future-nebula.template.html').read_text().replace('__PAYLOAD__',payload)
    (ROOT/'future-nebula.html').write_text(html)
    (ROOT/'future-nebula.synthetic.json').write_text(json.dumps(data,ensure_ascii=False,indent=2))
    print(f"Created future-nebula.html: {len(people)} people / {len(tasks)} tasks / {len(cats)} local categories")

if __name__=='__main__':
    build()
