from os import environ

SESSION_CONFIGS = [
    dict(
        name='chat_experiment',
        display_name="AI 채팅 상호작용 연구",
        app_sequence=['chat_experiment'],
        num_demo_participants=2,
    ),
]

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00,
    participation_fee=0.00,
    doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

LANGUAGE_CODE = 'ko'
REAL_WORLD_CURRENCY_CODE = 'KRW'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = ""

SECRET_KEY = '1314258008561'

ROOMS = [
    dict(
        name='ai_chat_room',
        display_name='AI 채팅 실험',
    ),
]