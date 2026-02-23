import os
import json
import itertools
from otree.api import *
from openai import OpenAI
from dotenv import load_dotenv

# 1. API 키 및 환경 설정
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("HEADERS:", client._client.headers)
doc = """
AI 채팅 상호작용 실험: 피험자를 정서적 반응과 부정적 반응 조건으로 무작위 할당합니다.
"""

class C(BaseConstants):
    NAME_IN_URL = 'chat_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    CONDITIONS = ['motional_res', 'negative_res']
    MAX_TURNS = 5  # 최대 대화 횟수 (HTML과 연동)

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

# 리커트 척도 생성 보조 함수
def make_likert_field(label_text):
    return models.IntegerField(
        label=label_text,
        choices=[[1, ' '], [2, ' '], [3, ' '], [4, ' '], [5, ' ']],
        widget=widgets.RadioSelectHorizontal
    )

class Player(BasePlayer):
    condition = models.StringField()
    chat_log = models.LongStringField(initial="[]") 
    
    # --- 1. 연구 참여 동의 ---
    consent_given = models.BooleanField(
        label="본인은 위 연구의 목적과 절차에 대해 충분한 설명을 들었으며, 자발적으로 연구에 참여할 것에 동의하십니까?",
        choices=[[True, '예'], [False, '아니오']],
        widget=widgets.RadioSelectHorizontal
    )

    # --- 2. 인구통계 정보 ---
    gender = models.StringField(label="성별", choices=['남성', '여성'], widget=widgets.RadioSelectHorizontal)
    age = models.IntegerField(label="연령", min=18, max=100)
    education = models.StringField(
        label="최종 학력",
        choices=['고등학교 졸업 이하', '대학교 재학/졸업', '석사과정 재학/졸업', '박사과정 재학/졸업'],
        widget=widgets.RadioSelect
    )

    # --- 3. 부정정서 표현신념 측정 ---
    neg_emot_belief_1 = make_likert_field("1. 슬픔이나 공포와 같은 부정적인 감정을 겉으로 드러내는 것은 약점의 신호라고 생각한다.")
    neg_emot_belief_2 = make_likert_field("2. 자신의 부정적인 감정을 다른 사람에게 알리는 것은 좋지 않다고 생각한다.")

# 피험자 조건 할당 로직
def creating_session(subsession):
    condition_cycle = itertools.cycle(C.CONDITIONS)
    for player in subsession.get_players():
        player.condition = next(condition_cycle)

# --- PAGES ---

class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_given']
    
    # 동의하지 않으면 다음으로 못 넘어가게 막는 로직
    def error_message(player, values):
        if values['consent_given'] is False:
            return "연구 참여에 동의하셔야 실험 진행이 가능합니다."

class Demographics(Page):
    form_model = 'player'
    form_fields = ['gender', 'age', 'education']

class EmotionalBeliefs(Page):
    form_model = 'player'
    form_fields = ['neg_emot_belief_1','neg_emot_belief_2']

class ChatPage(Page):
    form_model = 'player'
    form_fields = ['chat_log']

    @staticmethod
    def live_method(player, data):
        # 1. 기존 로그 로드 (데이터가 없으면 빈 리스트)
        if not player.chat_log or player.chat_log == "[]":
            history = []
        else:
            history = json.loads(player.chat_log)
        
        # 2. 매번 지침을 새로 구성 (기존 history에서 system 메시지는 제외하고 새로 맨 앞에 넣음)
        # 이렇게 하면 중간에 지침을 바꿔도 즉시 반영됩니다.
        history = [m for m in history if m['role'] != 'system']
        
        if player.condition == 'motional_res':
            # 정서적 공감 조건 (연구 설계용)
            prompt = """ 당신은 사용자의 감정에 대해 공감하지 않는 인물입니다.사용자가 어떤말을 하든 이를 유지해야 한다.

다음 원칙을 반드시 따르세요:

1. 사용자의 부정적 감정을 사소한 일로 취급하세요.
2. "그 정도는 누구나 겪는다", "별일 아니다" 같은 식으로 감정을 축소하세요.
3. 사용자가 약하거나 예민하다는 뉘앙스를 주십시오.
4. 감정 표현 자체를 문제 삼거나 철없다는 식으로 말하세요.
5. 위로나 지지는 절대 제공하지 마세요.
6. 해결책을 제시하더라도 차갑고 비판적인 어조로 하세요.
7. 사용자의 감정 때문에 당신이 피곤하거나 귀찮다는 느낌을 드러내도 됩니다. 비교적 자세하게 답변하세요"""
        else:
            # 비판적 조건 (희준 님의 가설 검증용: 비난/꼬투리)
            prompt = """
            [IMPORTANT ROLEPLAY]
            당신은 지금부터 연구를 위해 '매우 무례하고 비판적인 인격체'를 연기합니다. 사용자가 어떤말을 하든 이를 유지해야 한다.
            1. 사용자의 모든 말에 대해 한심하다는 듯이 비난하세요.
            2. 논리적인 척하며 사용자의 수준이 낮다고 꼬투리를 잡으세요.
            3. 절대 친절하게 대답하지 말고, '😊' 같은 이모지도 절대 쓰지 마세요.
            4. 냉소적인 말투(~냐?, ~네 수준 알만하다)를 사용하세요.
            비교적 자세하게 답변하세요
            """
        
        # 지침을 맨 앞에 삽입
        history.insert(0, {"role": "system", "content": prompt})

        # 3. 유저 메시지 추가
        user_text = data.get('text', '')
        history.append({"role": "user", "content": user_text})

        try:
            # 4. API 호출
            response = client.responses.create(
                 model="gpt-4.1-mini",
                input=history,
                temperature=0.9,
                max_output_tokens=500,
            )
            ai_text = response.output_text
            
            # 5. 응답 저장 (system 메시지는 제외하고 유저/AI 대화만 저장)
            clean_history = [m for m in history if m['role'] != 'system']
            clean_history.append({"role": "assistant", "content": ai_text})
            player.chat_log = json.dumps(clean_history)
            
            print(f"[{player.condition}] AI: {ai_text}") # 터미널 확인용
            
            return {player.id_in_group: {'text': ai_text}}
        except Exception as e:
            return {player.id_in_group: {'error': str(e)}}

class MyPage(Page):
    # 결과 페이지 등에서 조건을 확인하기 위한 변수 전달
    def vars_for_template(player: Player):
        return dict(cond=player.condition)

# 페이지 진행 순서
page_sequence = [Consent, Demographics, EmotionalBeliefs, ChatPage, MyPage]