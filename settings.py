from os import environ

# 1. 세션 기본 설정 (에러 해결의 핵심)
SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, 
    participation_fee=0.00, 
    doc=""
)

# 2. 실제 실험 세션 설정
SESSION_CONFIGS = [
    dict(
        name='chat_experiment',
        display_name="AI 채팅 상호작용 연구", 
        app_sequence=['chat_experiment'],    
        num_demo_participants=2,
    ),
]

# 나머지 설정들
PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# 한국 피험자 대상이라면 'ko'로 변경을 추천합니다
LANGUAGE_CODE = 'ko' 

REAL_WORLD_CURRENCY_CODE = 'KRW'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# Railway 환경변수에서 값을 가져옵니다
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

# 보안을 위해 비밀키는 그대로 유지하세요
SECRET_KEY = '7414839561618'