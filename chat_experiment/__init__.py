import os
import json
import itertools
import random
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
    NUM_ROUNDS = 4  # 1에서 4로 변경 (4번 반복)
    CONDITIONS = ['expression_res', 'emotional_res', 'solutional_res', 'negative_res'] 
    MAX_TURNS = 5
    
    # 4개의 시나리오를 리스트로 미리 저장해 둡니다.
    SCENARIOS = [
        "시나리오 1: 조별과제에서 선배가 무임승차하고 내 공을 가로챈 상황...",
        "시나리오 2: (두 번째 상황 내용...)",
        "시나리오 3: (세 번째 상황 내용...)",
        "시나리오 4: (네 번째 상황 내용...)"
    ]

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
    chat_log = models.LongStringField(initial="[]", blank=True)
    scenario_id = models.IntegerField()
    
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

    # --- 4. 외로움 측정 ---
    loneliness_1 = make_likert_field("1. 다른 사람과 함께 있을 때도 외로움을 느낀다.")
    loneliness_2 = make_likert_field("2. 주변 사람들과의 관계가 불충분하다고 느낀다.")

    #5. 사전 감정 측정
    pre_emotion_1 = make_likert_field("1. 이 상황에 대해 화가 난다.")
    pre_emotion_2 = make_likert_field("2. 사전 감정")

    #6. 사후 감정 측정 (매 라운드 대화가 끝난 직후) ---
    post_emotion_1 = make_likert_field("1. 대화 후 화가 나는 감정이 줄어들었다.")
    post_emotion_2 = make_likert_field("2. 사후 감정")

# 피험자 조건 할당 로직
def creating_session(subsession):
    # 1라운드에서만 조건 할당과 시나리오 순서 섞기를 진행합니다.
    if subsession.round_number == 1:
        condition_cycle = itertools.cycle(C.CONDITIONS)
        for player in subsession.get_players():
            # 1. AI 조건 할당 (participant.vars에 저장하여 4라운드 내내 기억하게 함)
            player.participant.vars['condition'] = next(condition_cycle)
            
            # 2. 시나리오 순서 무작위 섞기 (예: [3, 1, 4, 2])
            scenario_order = [0, 1, 2, 3] # 인덱스 0~3
            random.shuffle(scenario_order)
            player.participant.vars['scenario_order'] = scenario_order

    # 모든 라운드(1~4)에서 공통으로 실행되는 부분: participant의 데이터를 현재 Player로 복사
    for player in subsession.get_players():
        player.condition = player.participant.vars['condition']
        
        # 이번 라운드에 보여줄 시나리오 번호 찾기
        current_idx = player.participant.vars['scenario_order'][subsession.round_number - 1]
        player.scenario_id = current_idx + 1 # 1~4번

# --- PAGES ---
#설문 동의 페이지
class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_given']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1 # 1라운드일 때만 화면에 띄움
    
    def error_message(player, values):
        if values['consent_given'] is False:
            return "연구 참여에 동의하셔야 실험 진행이 가능합니다."

#인구통계정보
class Demographics(Page):
    form_model = 'player'
    form_fields = ['gender', 'age', 'education']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

#부정정서표현신념
class EmotionalBeliefs(Page):
    form_model = 'player'
    form_fields = ['neg_emot_belief_1','neg_emot_belief_2']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

#외로움 측정
class Loneliness(Page):
    form_model = 'player'
    form_fields = ['loneliness_1','loneliness_2']
    
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

#상황 설명
class ScriptIntro(Page): 
    @staticmethod
    def vars_for_template(player: Player):
        # 이번 라운드에 해당하는 시나리오 텍스트를 가져와서 HTML로 넘김
        current_text = C.SCENARIOS[player.scenario_id - 1]
        return dict(scenario_text=current_text)

#사전 감정 측정 페이지
class PreChatSurvey(Page):
    form_model = 'player'
    form_fields = ['pre_emotion_1', 'pre_emotion_2']

#사후 감정 측정 페이지
class PostChatSurvey(Page):
    form_model = 'player'
    form_fields = ['post_emotion_1', 'post_emotion_2']

#대화 루프 페이지
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
        
        if player.condition == 'expression_res':
            prompt = """표현장려 프롬프트"""
            
        elif player.condition == 'emotional_res':
            prompt = """정서반응 프롬프트"""
            
        elif player.condition == 'solutional_res':
            # 3번째 조건 프롬프트 (예시: 해결책 제시 조건)
            prompt = """문제해결 프롬프트"""
            
        else: #부정조건
            prompt = """부정반응 프롬프트"""      
        
        # 지침을 맨 앞에 삽입
        history.insert(0, {"role": "system", "content": prompt})

        # 3. 유저 메시지 추가
        user_text = data.get('text', '')
        history.append({"role": "user", "content": user_text})

        try:
            # 4. API 호출
            response = client.chat.completions.create(
            model="gpt-4o",
                messages=history,
                temperature=0.5,
            max_tokens=500,
            )
            ai_text = response.choices[0].message.content # 응답 텍스트를 추출하는 정확한 경로입니다.
            
            # 5. 응답 저장 (system 메시지는 제외하고 유저/AI 대화만 저장)
            clean_history = [m for m in history if m['role'] != 'system']
            clean_history.append({"role": "assistant", "content": ai_text})
            player.chat_log = json.dumps(clean_history)
            
            print(f"[{player.condition}] AI: {ai_text}") # 터미널 확인용
            
            return {player.id_in_group: {'text': ai_text}}
        except Exception as e:
            return {player.id_in_group: {'error': str(e)}}

#마지막
class MyPage(Page):
    @staticmethod
    def is_displayed(player: Player):
        # 결과 페이지나 실험 종료 페이지는 마지막 4라운드에만 표시
        return player.round_number == C.NUM_ROUNDS

    def vars_for_template(player: Player):
        return dict(cond=player.condition)

# 페이지 진행 순서
page_sequence = [Consent, Demographics, EmotionalBeliefs, Loneliness, ScriptIntro, PreChatSurvey, ChatPage, PostChatSurvey, MyPage]