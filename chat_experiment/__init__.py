import os
import json
import itertools
import random
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
    MAX_TURNS = 5

    GROUPS = ['G1','G2','G3','G4']

    TURN_SEQUENCE = {
        "G1": ["solution","solution","validation","validation","closing"],
        "G2": ["solution","solution","validation","validation","closing"],
        "G3": ["solution","solution","validation","validation","closing"],
        "G4": ["solution","solution","validation","validation","closing"],
    }

    SCENARIOS = [
        "친구가 사람들 앞에서 당신의 과거 아픈 상처를 웃음거리로 만들었습니다.",
        "친구의 비밀을 지켰지만 당신이 퍼뜨렸다는 의심을 받습니다.",
        "팀 프로젝트에서 당신이 한 일을 다른 팀원이 자신의 것처럼 발표했습니다.",
        "팀원들이 당신만 빼고 단체 채팅방을 만들어 프로젝트를 진행했습니다."
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

    pre_emotion_1 = make_likert_field("1. 이 상황에 대해 화가 난다.")
    pre_emotion_2 = make_likert_field("2. 이 상황을 잘 대응할 수 있을것 같다.")
    post_emotion_1 = make_likert_field("1. 이 상황에 대해 화가 난다.")
    post_emotion_2 = make_likert_field("2. 이 상황을 잘 대응할 수 있을것 같다.")



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


class Demographics(Page):

    form_model='player'
    form_fields=['gender','age','education']

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
    form_fields = ['pre_emotion_1', 'pre_emotion_2']


class PostChatSurvey(Page):

    form_model='player'
    form_fields=['post_emotion_1', 'post_emotion_2']


class ChatPage(Page):

    form_model='player'
    form_fields=['chat_log']

    @staticmethod
    def live_method(player, data):

        if not player.chat_log or player.chat_log=="[]":
            history=[]
        else:
            history=json.loads(player.chat_log)

        history=[m for m in history if m['role']!='system']

        turn = len(history)//2 + 1

        group = player.group_condition

        if turn > C.MAX_TURNS:
            turn = C.MAX_TURNS

        instruction_type = C.TURN_SEQUENCE[group][turn-1]

        if instruction_type == "validation":

            prompt = """
ROLE: Validation-focused responder
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
- Total length: 300–400 characters
"""

        elif instruction_type == "solution":

            prompt = """
ROLE: Problem-solving responder

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
- Total length: 300–400 characters
"""

        else:

            prompt = """
대화를 정리하고 마무리하십시오.
150자 이내.
"""

        history.insert(0,{"role":"system","content":prompt})

        user_text=data.get('text','')

        history.append({"role":"user","content":user_text})

        try:

            response=client.chat.completions.create(
                model="gpt-4o",
                messages=history,
                temperature=0.9,
                max_tokens=800,
                top_p=0.9
            )

            ai_text=response.choices[0].message.content

            clean=[m for m in history if m['role']!='system']

            clean.append({"role":"assistant","content":ai_text})

            player.chat_log=json.dumps(clean)

            print(f"[{player.group_condition}][turn{turn}] {ai_text}")

            return {player.id_in_group:{'text':ai_text}}

        except Exception as e:

            return {player.id_in_group:{'error':str(e)}}


class End(Page):

    @staticmethod
    def is_displayed(player):
        return player.round_number==C.NUM_ROUNDS


page_sequence = [
    Consent,
    Demographics,
    ScriptIntro,
    PreChatSurvey,
    ChatPage,
    PostChatSurvey,
    End
]