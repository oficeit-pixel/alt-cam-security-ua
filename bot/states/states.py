from aiogram.fsm.state import State, StatesGroup


class CaptchaState(StatesGroup):
    waiting_for_captcha = State()


class TermsState(StatesGroup):
    waiting_for_accept = State()


class ClientQuizSG(StatesGroup):
    object_type = State()
    points_count = State()
    need_ups = State()
    photo_upload = State()
    confirm_order = State()


class ServiceSG(StatesGroup):
    fault_type = State()
    brand = State()
    problem_desc = State()
    contact_info = State()


class InstallerOnboardingSG(StatesGroup):
    prof_quiz = State()
    docs_upload = State()
    portfolio_upload = State()
    wait_approval = State()


class AuctionBidSG(StatesGroup):
    price_input = State()
    comment_input = State()
