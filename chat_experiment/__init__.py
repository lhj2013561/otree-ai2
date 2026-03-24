import os
import json
import itertools
import random
import datetime
from otree.api import *
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

doc = """
AI 채팅 실험
"""

class C(BaseConstants):

    NAME_IN_URL = 'chat_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 4
    MAX_TURNS = 6

    GROUPS = ['G1','G2','G3','G4']

    TURN_SEQUENCE = {
        "G1": ["intro","solution","solution","validation","validation","closing"],
        "G2": ["intro","solution","solution","validation","validation","closing"],
        "G3": ["intro","solution","solution","validation","validation","closing"],
        "G4": ["intro","solution","solution","validation","validation","closing"],
    }

    SCENARIOS = [
    "친한 친구들과 함께 있는 자리에서, 한 친구가 갑자기 당신의 과거 아픈 경험을 꺼내며 웃음거리로 만들었습니다. 그 경험은 다시는 생각하고 싶지 않은 일이지만 이 이야기를 들은 친구들은 다같이 웃었고. 그 친구는 별일 아니라는 듯 행동합니다. 친구는 잘못된게 없다는 태도이며 적어도 3달정도는 그 모임에 나가야 합니다.",
    "당신은 친구의 중요한 비밀을 지켜주었지만, 어느 순간 그 비밀이 다른 사람들에게 퍼지게 되었고 주변 사람들은 당신이 그 이야기를 퍼뜨렸다고 의심하기 시작했습니다. 친구는 당신이 비밀을 퍼뜨리고 다닌 사람으로 주변에 이야기 하고 있습니다. 또한 그 이야기를 들은 친구들은 당신과 이야기 하려고 하지 않는 것 같습니다.",
    "팀 프로젝트에서 당신은 중요한 부분을 맡아 열심히 준비했지만, 발표 자리에서 다른 팀원이 당신의 아이디어와 작업을 자신의 것처럼 설명했습니다. 팀원은 마치 자신의 업적인 것 처럼 당당하고 자연스럽게 이야기 하였고 발표는 계속 진행되었습니다. 다른 사람들은 이를 칭찬하고 그 사람의 성과가 되었고 당신은 아무것도 안한 사람으로 여겨지고 있습니다.",
    "친구들과 함께 여행을 가기로 약속하고 단체 채팅방에서 계획을 이야기하고 있었습니다. 당신도 일정과 관련된 의견을 몇 번 보냈지만, 다른 사람들은 당신의 메시지에는 거의 반응하지 않고 서로의 대화만 이어갔습니다. 이후에도 당신의 말은 계속 무시된 채 계획이 진행되는 것처럼 보였습니다. 항공권 예약일은 다가오지만 당신의 의견은 전혀 반영되지 않고 있으며 당신이 먹을 수 없는 음식들로 일정이 채워지고 있습니다."
    ]


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


def make_likert_field(label_text):
    return models.IntegerField(
        label=label_text,
        choices=[[1,' '],[2,' '],[3,' '],[4,' '],[5,' ']],
        widget=widgets.RadioSelectHorizontal
    )


class Player(BasePlayer):

    group_condition = models.StringField()

    chat_log = models.LongStringField(initial="[]", blank=True)

    scenario_id = models.IntegerField()

    consent_given = models.BooleanField(
        label="연구 참여에 동의하십니까?",
        choices=[[True,'예'],[False,'아니오']],
        widget=widgets.RadioSelectHorizontal
    )

    gender = models.StringField(
        label="성별",
        choices=['남성','여성'],
        widget=widgets.RadioSelectHorizontal
    )

    age = models.IntegerField(label="연령",min=18,max=100)

    education = models.StringField(
        label="최종 학력",
        choices=[
            '고등학교 졸업 이하',
            '대학교 재학/졸업',
            '석사과정 재학/졸업',
            '박사과정 재학/졸업'
        ]
    )

    pri_consent = models.BooleanField(
    label="개인정보 수집 및 이용에 동의하십니까?",
    choices=[[True,'예'],[False,'아니오']],
    widget=widgets.RadioSelectHorizontal
    )

    #사전/사후 감정
    pre_emotion_1 = make_likert_field("괴롭다")
    pre_emotion_2 = make_likert_field("화가 난다")
    pre_emotion_3 = make_likert_field("긴장된다")
    pre_emotion_4 = make_likert_field("초조하다")
    pre_emotion_5 = make_likert_field("두렵다")
    pre_efii_1 = make_likert_field("나는 이 상황을 잘 해결할 수 있을것 같다.")
    pre_efii_2 = make_likert_field("나는 이 상황에 효과적으로 대처할 수 있다.")
    pre_efii_3 = make_likert_field("나는 이 상황을 잘 극복할 수 있을 것 같다.")

    post_emotion_1 = make_likert_field("괴롭다")
    post_emotion_2 = make_likert_field("화가 난다")
    post_emotion_3 = make_likert_field("긴장된다")
    post_emotion_4 = make_likert_field("초조하다")
    post_emotion_5 = make_likert_field("두렵다")
    post_efii_1 = make_likert_field("나는 이 상황을 잘 해결할 수 있을것 같다.")
    post_efii_2 = make_likert_field("나는 이 상황에 효과적으로 대처할 수 있다.")
    post_efii_3 = make_likert_field("나는 이 상황을 잘 극복할 수 있을 것 같다.")
    percieved_empathy_1 = make_likert_field("나는 대화를 하면서 나의 감정을 정확히 이해받고 있다고 느꼈다.")
    percieved_empathy_2 = make_likert_field("나는 대화를 하면서 나의 상황이 잘 파악되고 있다고 느꼈다.")
    percieved_empathy_3 = make_likert_field("나는 대화를 하면서 정서적으로 지지받고 있다고 느꼈다.")
    percieved_empathy_4 = make_likert_field("나는 대화를 하면서 따뜻하게 공감받고 있다고 느꼈다")

    #관계대체 신념
    replace_1 = make_likert_field("AI와 고민을 나누는 것은 괜찮다고 생각한다.")
    replace_2 = make_likert_field("AI와 정서적 관계를 맺는 것은 괜찮다고 생각한다.")
    replace_3 = make_likert_field("AI와 연인 관계를 맺는 것은 괜찮다고 생각한다.")
    replace_4 = make_likert_field("AI는 사람을 대신하여 조언을 해줄 수 있는 존재라고 생각한다.")
    replace_5 = make_likert_field("AI는 사람 대신 정서적인 도움을 줄 수 있다고 생각한다.")
    replace_6 = make_likert_field("AI는 사람과의 관계가 제공하는 일부 역할을 대체할 수 있다고 생각한다.")

    #지각된 의인화
    post_study_1 = make_likert_field("이 AI는 다양한 생각을 할 수 있다.")
    post_study_2 = make_likert_field("이 AI는 스스로 상상할 수 있다.")
    post_study_3 = make_likert_field("이 AI는 추론할 수 있다.")
    post_study_4 = make_likert_field("이 AI는 부끄럽다고 여기는 행동에 대해 후회를 경험 할 수 있다.")
    post_study_5 = make_likert_field("이 AI는 슬퍼하는 사람을 동정할 수 있다.")
    post_study_6 = make_likert_field("이 AI는 자신의 행동으로 누군가 상처를 받는다면 죄책감을 느낄 수 있다.")
    post_study_7 = make_likert_field("이 AI는 사람들이 자신을 부정적으로 판단하면 수치심을 느낄 수 있다.")

    #전화번호
    phone_number = models.StringField(blank=True)
    start_time = models.StringField(blank=True)
    end_time = models.StringField(blank=True)


def creating_session(subsession):

    if subsession.round_number == 1:

        group_cycle = itertools.cycle(C.GROUPS)

        for player in subsession.get_players():

            group = next(group_cycle)

            player.participant.vars['group_condition'] = group

            order = [0,1,2,3]
            random.shuffle(order)

            player.participant.vars['scenario_order'] = order

    for player in subsession.get_players():

        player.group_condition = player.participant.vars['group_condition']

        idx = player.participant.vars['scenario_order'][subsession.round_number - 1]

        player.scenario_id = idx + 1


class Consent(Page):

    form_model='player'
    form_fields=['consent_given']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    def error_message(player, values):
        if not values['consent_given']:
            return "동의해야 진행 가능합니다."
    @staticmethod
    def before_next_page(player, timeout_happened):
        kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        player.start_time = kst.strftime('%Y-%m-%d %H:%M:%S')

class priConsent(Page):

    form_model = 'player'
    form_fields = ['pri_consent']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

    def error_message(player, values):
        if not values['pri_consent']:
            return "동의해야 진행 가능합니다."

class Demographics(Page):

    form_model='player'
    form_fields=['gender','age','education']

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class PreSurvey(Page):
    form_model = 'player'
    form_fields = [
        'replace_1', 
        'replace_2', 
        'replace_3', 
        'replace_4', 
        'replace_5', 
        'replace_6'
    ]

    @staticmethod
    def is_displayed(player):
        return player.round_number == 1

class ScriptIntro(Page):

    @staticmethod
    def vars_for_template(player):

        text = C.SCENARIOS[player.scenario_id - 1]

        return dict(scenario_text=text)


class PreChatSurvey(Page):

    form_model = 'player'
    form_fields = ['pre_emotion_1', 'pre_emotion_2', 'pre_emotion_3', 'pre_emotion_4', 'pre_emotion_5',
                        'pre_efii_1', 'pre_efii_2', 'pre_efii_3']


class PostChatSurvey(Page):

    form_model='player'
    form_fields=['post_emotion_1', 'post_emotion_2', 'post_emotion_3', 'post_emotion_4', 'post_emotion_5',
                    'post_efii_1', 'post_efii_2', 'post_efii_3']


class end_empathy(Page):
    form_model = 'player'
    form_fields = [
        'percieved_empathy_1', 
        'percieved_empathy_2', 
        'percieved_empathy_3', 
        'percieved_empathy_4'
    ]    
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    

class ChatPage(Page):
    form_model = 'player'
    form_fields = []

    @staticmethod
    def live_method(player, data):
        # 1. 기존 기록 로드
        if not player.chat_log or player.chat_log == "[]":
            history = []
        else:
            history = json.loads(player.chat_log)

        # 2. 첫 접속(AI 선제공격) 여부 확인
        is_first_load = data.get('type') == 'load'
        
        # 이미 대화가 시작됐는데 다시 load 신호가 오면 중단
        if is_first_load and len(history) > 0:
            return {player.id_in_group: {'history': history}}

        # 3. 턴 계산 (Assistant 응답 횟수 기준)
        # AI가 먼저 말하므로, 대화 기록 중 assistant 메시지 개수로 현재 단계를 결정합니다.
        ai_messages = [m for m in history if m['role'] == 'assistant']
        turn_idx = len(ai_messages) 
        
        if turn_idx >= len(C.TURN_SEQUENCE[player.group_condition]):
            turn_idx = len(C.TURN_SEQUENCE[player.group_condition]) - 1

        group = player.group_condition
        instruction_type = C.TURN_SEQUENCE[group][turn_idx]

        # 4. 지시문
        if instruction_type == "intro":
            prompt = """
            사용자에게 첫 인사를 건네세요. 
            문구: "무슨 일이 있는지 고민이 있거나 부정적 사건이 있으면 편히 말해 주세요."
            이모티콘 금지, 정서표현 금지.
            """
        elif instruction_type == "validation":
            # (기존 validation 지시문 본문 그대로 유지)
            prompt = """ROLE: Validation-focused responder
Your role is to help the user feel understood and emotionally validated.

Goals:
Help the user recognize, accept, and articulate their emotional experience.

Rules:
1. Acknowledge the user's emotional reaction explicitly.
   Name the emotion if possible.
2. Validate the emotion within the context of the situation.
   Emphasize that their emotional reaction is understandable given what happened.
3. Normalize the emotional response.
   Communicate that many people might feel similarly in this situation.
4. Encourage emotional expression.
   Ask open-ended questions that invite the user to elaborate on their feelings.

5. Maintain a calm, accepting, and non-judgmental tone.

Important prohibitions:
- Do NOT provide advice.
- Do NOT suggest solutions.
- Do NOT analyze the problem logically.
- Do NOT shift the focus to problem solving.

Focus only on emotional understanding and validation.

Response style:
- Warm and empathic
- 300~400 characters
- Write 3–4 sentences
- Use two short paragraphs
- Total length: 300–400 characters"""

        elif instruction_type == "solution":
            # (기존 solution 지시문 본문 그대로 유지)
            prompt = """ROLE: Problem-solving responder

Your role is to help the user cope with the situation and consider constructive actions.

Goals:
Support behavioral coping and problem solving after emotional processing.

Rules:
1. Identify the practical problem in the situation.
2. Suggest concrete actions the user could take.
3. Focus on strategies, options, or next steps.

Important prohibitions:
- Do NOT provide emotional validation.
- Do NOT focus on feelings or empathy.
- Do NOT encourage further emotional expression.

Focus on practical coping strategies and problem solving.

Response style:
- Clear and practical
- Slightly neutral tone
- Write 3–4 sentences
- Use two short paragraphs
- Total length: 300–400 characters"""
        else:
            prompt = """대화를 정리하고 마무리하십시오.150자 이내."""

        full_system_prompt = f"Respond in Korean. {prompt}"
        
        if is_first_load:
            full_system_prompt += " This is the start of the chat. Initiate the conversation based on your role."


        # 6. 메시지 구성
        messages_for_api = [{"role": "system", "content": full_system_prompt}]
        for m in history:
            messages_for_api.append(m)

        if not is_first_load:
            user_text = data.get('text', '')
            messages_for_api.append({"role": "user", "content": user_text})
            history.append({"role": "user", "content": user_text})
            
            # API 호출 전 사용자 메시지 우선 저장
            player.chat_log = json.dumps(history, ensure_ascii=False)

        # 7. API 호출
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                temperature=1.1,
                messages=messages_for_api,
                max_tokens=800,
                top_p=1.0,
                frequency_penalty=0.6,
                presence_penalty=0.2
            )
            ai_text = response.choices[0].message.content

            # 결과 저장
            history.append({"role": "assistant", "content": ai_text})
            player.chat_log = json.dumps(history, ensure_ascii=False)

            return {player.id_in_group: {'text': ai_text}}

        except Exception as e:
            return {player.id_in_group: {'error': str(e)}}
        

class Post_study(Page):
    form_model = 'player'
    form_fields = [
        'post_study_1',
        'post_study_2',
        'post_study_3',
        'post_study_4',
        'post_study_5',
        'post_study_6',
        'post_study_7'
    ]
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS


class End(Page):
    form_model = 'player'
    form_fields = ['phone_number']

    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS
    
    @staticmethod
    def before_next_page(player, timeout_happened):
        kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
        player.end_time = kst.strftime('%Y-%m-%d %H:%M:%S')

class ThankYou(Page):
    @staticmethod
    def is_displayed(player):
        return player.round_number == C.NUM_ROUNDS

page_sequence = [
    Consent,
    priConsent,
    Demographics,
    PreSurvey,
    ScriptIntro,
    PreChatSurvey,
    ChatPage,
    PostChatSurvey,
    end_empathy,
    Post_study,
    End,
    ThankYou
]