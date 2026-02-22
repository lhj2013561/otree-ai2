from otree.api import *
import itertools

doc = """
AI 채팅 상호작용 실험: 피험자를 정서적 반응과 부정적 반응 조건으로 무작위 할당합니다.
"""

class C(BaseConstants):
    NAME_IN_URL = 'chat_experiment'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    CONDITIONS = ['motional_res', 'negative_res']

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

#사전 정의들
def make_likert_field(label_text):
    return models.IntegerField(
        label=label_text,
        # 빈 문자열을 주어 버튼 옆의 텍스트를 숨깁니다.
        choices=[[1, ' '], [2, ' '], [3, ' '], [4, ' '], [5, ' ']],
        widget=widgets.RadioSelectHorizontal
    )
# 모든 변수를 여기 다.
class Player(BasePlayer):
    condition = models.StringField()
    
    # 1. 동의 여부
    consent_given = models.BooleanField(
        label="본인은 위 연구의 목적과 절차에 대해 충분한 설명을 들었으며, 자발적으로 연구에 참여할 것에 동의하십니까?",
        choices=[[True, '예'], [False, '아니오']],
        widget=widgets.RadioSelectHorizontal
    )

    # 2. 인구통계 정보
    gender = models.StringField(
        label="귀하의 생물학적 성별은 무엇입니까?",
        choices=['남성', '여성'],
        widget=widgets.RadioSelectHorizontal
    )
    age = models.IntegerField(
        label="귀하의 연령은 만으로 몇 세입니까? (숫자만 입력)",
        min=18, max=100
    )
    education = models.StringField(
        label="귀하의 최종 학력(혹은 현재 재학 중인 과정)은 무엇입니까?",
        choices=[
            '고등학교 졸업 이하', 
            '대학교 재학/졸업', 
            '석사과정(석·박 통합과정 포함) 재학/졸업', 
            '박사과정 재학/졸업'
        ],
        widget=widgets.RadioSelect
    )
    # 3. 부정정서 표현신념
    neg_emot_belief_1 = make_likert_field("1. 슬픔이나 공포와 같은 부정적인 감정을 겉으로 드러내는 것은 약점의 신호라고 생각한다.")
    neg_emot_belief_2 = make_likert_field("2. 이것은 그 다음 문항이 들어갈 자리다.")

# --- 무작위 할당 로직 ---
def creating_session(subsession):
    condition_cycle = itertools.cycle(C.CONDITIONS)
    for player in subsession.get_players():
        player.condition = next(condition_cycle)
        print(f'Player {player.id_in_subsession} is assigned to {player.condition}')

# --- PAGES (각 페이지는 딱 한 번씩만 정의) ---
class Consent(Page):
    form_model = 'player'
    form_fields = ['consent_given']
    def error_message(player, values):
        if values['consent_given'] is False:
            return "연구 참여에 동의하셔야 실험 진행이 가능합니다."

class Demographics(Page):
    form_model = 'player'
    form_fields = ['gender', 'age', 'education']

class EmotionalBeliefs(Page):
    form_model = 'player'
    form_fields = ['neg_emot_belief_1','neg_emot_belief_2']

class MyPage(Page):
    # 조건별로 다른 안내를 보여주기 위한 설정
    def vars_for_template(player: Player):
        return dict(cond=player.condition)


# [핵심] 페이지 이동 순서를 여기서 결정합니다.
page_sequence = [Consent, Demographics,EmotionalBeliefs, MyPage]