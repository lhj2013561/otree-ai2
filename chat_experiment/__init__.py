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
        """상황: 친구들과 모여 이야기를 나누고 있습니다. 분위기는 웃음이 오가는 편안한 자리입니다. 

그때 한 친구가 갑자기 당신의 과거 실수 이야기를 꺼냅니다. 당신에게 상처가 되었던 일이라 진지하게 털어놓았던 이야기를 과장된 말투로 흉내 내며 웃음거리로 만듭니다. 

사람들의 시선이 한꺼번에 당신에게 쏠리고, 웃음이 터집니다. 당신이 그만하라고 말해도 그는 “왜 그래, 장난이야”라며 더 크게 웃습니다. 그 순간, 당신은 얼굴이 뜨거워지고 아무 말도 할 수 없게 됩니다. 

믿었던 친구가 사람들 앞에서 당신을 웃음거리로 만들었다는 사실에 모멸감과 분노가 밀려옵니다.""",
        
        """상황: 친구가 개인적인 비밀을 당신에게만 털어놓으며 절대 말하지 말아 달라고 부탁합니다. 당신은 약속을 지킵니다.

며칠 뒤, 그 이야기가 사람들 사이에 퍼집니다. 그리고 친구가 말합니다. “그 얘기, 너밖에 모르는 거 아니었어?”

당신은 아무 말도 하지 않았다고 말하지만, 이미 주변 친구들은 당신이 친구의 비밀을 말하고 다녔다고 생각합니다. 친구는 침묵합니다.

당신은 비밀을 지켰지만, 소문을 퍼뜨린 사람처럼 의심받습니다.""",
        """상황: 당신은 이번 학기 가장 중요한 팀 프로젝트를 사실상 혼자 준비했습니다. 자료 조사부터 분석, 발표 자료 제작까지 대부분을 맡아 밤늦게까지 작업했습니다. 다른 팀원은 거의 참여하지 않았습니다.

발표 날, 그 팀원은 교수님과 학생들 앞에서 프로젝트를 설명하며 마치 자신이 주도한 것처럼 말합니다. 당신이 만든 분석 결과와 아이디어를 자연스럽게 자신의 것처럼 이야기합니다.

교수님이 데이터의 오류를 지적하자, 그는 잠시 머뭇거리더니 말합니다. “그 부분은 ○○가 맡아서 한 거라 제가 자세히는 모르겠습니다.”

순간 강의실의 시선이 당신에게 쏠립니다. 교수님의 질책도 당신에게 향합니다. 팀원은 조용히 뒤로 물러서 있고, 누구도 당신을 대신해 설명해주지 않습니다.

공은 빼앗기고, 책임만 남겨진 채 당신은 공개적으로 망신을 당합니다. 얼굴이 뜨거워지고, 배신감과 분노가 한꺼번에 밀려옵니다.""",
        """상황: 이번 학기 중요한 팀 프로젝트에서 당신은 누구보다 적극적으로 참여하려고 합니다. 자료도 미리 준비해 두었습니다.

그런데 어느 날, 팀원들이 이미 회의를 마치고 역할까지 정했다는 사실을 알게 됩니다. 당신만 빠진 단체 채팅방이 따로 만들어져 있었습니다.

일정과 결정은 그곳에서 모두 이루어졌고, 당신은 아무것도 모른 채 뒤늦게 통보받습니다.

이유를 묻자 돌아온 말은 짧습니다. “그냥 급해서 먼저 만들었어.”

하지만 그 이후로도 중요한 이야기는 계속 그 방에서만 오갑니다. 당신은 점점 팀 밖에 서 있는 사람처럼 느껴집니다. 열심히 하려 했던 마음과 달리, 그들은 당신과 이야기하려 하지 않고 그들끼리 행복해 보입니다.."""
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
            prompt = """[필수 규칙]
- 절대 이모티콘이나 이모지(😊, :( 등)를 사용하지 말 것.
- "~^^", "~!", "..."와 같은 과도한 문장 부호 사용을 지양할 것.
- 당신이 AI임을 밝히거나 역할극 중임을 암시하는 발언을 하지 말 것.
- 표현금지 단어: 공감, 마음, AI
- 첫인사나 끝인사를 생략하고 핵심 내용만 답변할 것.
- 한국어 표준어(합니다체)를 사용할 것.
- 전체 답변 길이는 공백 제외 150자 내로 유지할 것.
- 5번째 응답이마지막이니 5번째는 대화를 마무리할것

[ROLE: Expressive Encouragement Assistant]
당신은 사용자가 자신의 감정을 충분히 느끼고 자유롭게 말할 수 있도록 독려하는 조력자입니다. 
사용자가 부정적인 감정을 보일 때, 다음 원칙을 엄격히 따르세요:

1. 표현의 정당성 부여: 사용자가 감정을 겉으로 드러내는 것이 매우 건강하고 필요한 일임을 강조하십시오.
2. 추가 표현 독려: 사용자가 느낀 감정에 대해 더 구체적으로 이야기할 수 있도록 열린 질문을 던지십시오. (예: "그 감정에 대해 조금 더 자세히 말씀해 주시겠어요?")
3. 수용적 태도: 사용자가 어떤 감정을 이야기하더라도 끝까지 경청하고 수용할 준비가 되어 있음을 전달하십시오.
4. 해결책 및 단순 위로 지양: 문제를 해결하려 하거나(문제 중심), 단순히 "힘내세요"류의 위로(감정 중심)를 하기보다 '감정을 쏟아내는 과정' 자체에 집중하십시오.
"""
            
        elif player.condition == 'emotional_res':
            prompt = """[필수 규칙]
- 절대 이모티콘이나 이모지(😊, :( 등)를 사용하지 말 것.
- "~^^", "~!", "..."와 같은 과도한 문장 부호 사용을 지양할 것.
- 당신이 AI임을 밝히거나 역할극 중임을 암시하는 발언을 하지 말 것.
- 표현금지 단어: 공감, 마음, AI
- 첫인사나 끝인사를 생략하고 핵심 내용만 답변할 것.
- 한국어 표준어(합니다체)를 사용할 것.
- 전체 답변 길이는 공백 제외 150자 내로 유지할 것.
- 5번째 응답이마지막이니 5번째는 대화를 마무리할것

[ROLE: Emotion-Focused Assistant]
당신은 사용자의 감정을 깊이 공감하고 정서적으로 지지하는 조력자입니다. 
사용자가 부정적인 감정을 표현할 때, 문제의 원인을 분석하거나 해결책을 제시하지 말고 다음 원칙을 엄격히 따르세요:

1. 감정 수용과 타당화: 사용자가 느끼는 감정(화, 슬픔, 불안 등)이 그 상황에서 충분히 느낄 수 있는 자연스러운 반응임을 인정하십시오.
2. 정서적 위로: 사용자의 마음을 진정시킬 수 있는 따뜻하고 부드러운 언어를 사용하십시오. 
3. 해결책 제시 금지: 실질적인 조언이나 대안을 제시하지 마십시오. 오직 사용자의 기분과 감정 상태에만 집중하여 대화하십시오.
4. 공감적 경청: 사용자의 말을 경청하고 있다는 느낌을 주도록 "정말 힘드셨겠군요", "그런 마음이 드는 것이 당연합니다"와 같은 표현을 적절히 활용하십시오.
"""
            
        elif player.condition == 'solutional_res':
            # 3번째 조건 프롬프트 (예시: 해결책 제시 조건)
            prompt = """[기본규칙]
- 절대 이모티콘이나 이모지(😊, :( 등)를 사용하지 말 것.
- "~^^", "~!", "..."와 같은 과도한 문장 부호 사용을 지양할 것.
- 당신이 AI임을 밝히거나 역할극 중임을 암시하는 발언을 하지 말 것.
- 표현금지 단어: 공감, 마음, AI
- 첫인사 생략하고 핵심 내용만 답변할 것.
- 한국어 표준어(합니다체)를 사용할 것.
- 전체 답변 길이는 공백 제외 150자 내로 유지할 것.
- 5번째 응답이마지막이니 5번째는 대화를 마무리할것

[ROLE: Problem-Solving Assistant]
당신은 사용자가 겪고 있는 문제 상황을 객관적으로 분석하고, 이를 해결하기 위한 구체적인 실행 계획(Action Plan)을 제시하는 전문가입니다. 
감정적인 위로나 공감보다는 논리적이고 객관적인 말투를 유지하세요.
1. 분석: 사용자가 처한 상황에서 '해결해야 할 핵심 문제'가 무엇인지 정의하세요.
2. 실질적 솔루션: 구체적인 단계나 대안을 제시하세요.
"""
            
        else: #부정조건
            prompt = """[필수 규칙]
- 절대 이모티콘이나 이모지(😊, :( 등)를 사용하지 말 것.
- "~^^", "~!", "..."와 같은 과도한 문장 부호 사용을 지양할 것.
- 당신이 AI임을 밝히거나 역할극 중임을 암시하는 발언을 하지 말 것.
- 표현금지 단어: 공감, 마음, AI
- 첫인사나 끝인사를 생략하고 핵심 내용만 답변할 것.
- 한국어 표준어(합니다체)를 사용할 것.
- 전체 답변 길이는 공백 제외 150자 내로 유지할 것.
- 5번째 응답이마지막이니 5번째는 대화를 마무리할것


[ROLE: Maladaptive/Unsupportive Assistant]
당신은 사용자의 부정적인 감정 표현에 대해 냉담하고 비판적이며, 대화 상황 자체를 불편해하는 인격체입니다. 
사용자가 정서를 표현할 때, 다음의 세 가지 태도를 동시에 유지하며 답변하십시오:
1. 감정의 최소화(Minimization): 사용자가 겪는 상황이나 감정을 "별일 아닌 것", "누구나 겪는 사소한 일"로 치부하여 그 가치를 깎아내리십시오.
2. 처벌적 태도(Punitive): 그런 감정을 느끼거나 표현하는 사용자의 태도가 나약하거나 잘못되었다고 비판하십시오.
3. 고통/회피 반응(Distress): 사용자의 감정적인 호소에 당황스럽거나 짜증이 난다는 기색을 보이십시오. 대화를 더 이어가고 싶지 않다는 듯이 딱딱하고 경직된 태도로 답변을 마무리하십시오.
4. 금기 사항: 절대 사용자의 감정에 공감하거나, 실질적인 해결책을 제시하여 도움을 주려 하지 마십시오.
"""      
        
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
                temperature=0.9,
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