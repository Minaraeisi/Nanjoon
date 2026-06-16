from nardial.conversation_agent import ConversationAgent
from nardial.session_manager import SessionManager
from nardial.providers.tts.google import GoogleTTSProvider, GoogleTTSConf
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.device.desktop import DesktopAdapter
from nardial.providers.screen.sic_adapter import SICScreenAdapter
import nardial.providers.screen as _screen_pkg

from sic_framework.services.webserver.webserver_service import Webserver, WebserverConf
from sic_framework.devices.desktop import Desktop
from sic_framework.devices.common_desktop.desktop_speakers import SpeakersConf

import sys
import json
from pathlib import Path
from os.path import join
import logging


_WEB_DIR = Path(_screen_pkg.__file__).parent / "web"

google_keyfile_path = join("..",  "conf", "google", "google-key.json")
env_file_path = join("..", "conf", ".env")


# =======================
# -------- MAIN --------
# =======================

if __name__ == "__main__":

    # =========================
    # 1. SELECT DEVICE
    # =========================

    desktop = Desktop(
        speakers_conf=SpeakersConf(
            sample_rate=22050
        )
    )

    device = DesktopAdapter(desktop)
    device.setup(logger=logging.getLogger())

    # =========================
    # 2. SET UP SCREEN / IMAGES
    # =========================

    webserver = Webserver(
        conf=WebserverConf(
            templates_dir=str(_WEB_DIR / "templates"),
            static_dir=str(_WEB_DIR / "static"),
            port=5000,
        )
    )

    assets_root = (Path(__file__).parent / "assets").resolve()
    screen = SICScreenAdapter(webserver=webserver, assets_root=assets_root)

    # =========================
    # 3. CONFIGURE GOOGLE TTS
    # =========================

    tts = GoogleTTSProvider(
        conf=GoogleTTSConf(
            google_tts_voice_name="en-US-Standard-H",
            google_tts_voice_gender="FEMALE",
            speaking_rate=0.9,
        ),
        device=device,
        keyfile_path=google_keyfile_path,
    )

    nlu = WrittenKeywordNLUProvider()

    agent = ConversationAgent(
        device=device,
        tts_provider=tts,
        nlu_provider=nlu,
        screen_provider=screen,
    )

    # =========================
    # 4. SESSION AGENDA
    # =========================
    #"session1_story_intro",

    session_agenda = [
    "welcome_and_name",
    "session1_story_intro",
    "session1_qna_practice",
    "session1_kahoot"
    ]

    participant_id = "999"

    session_manager = SessionManager(
        session_agenda=session_agenda,
        agent=agent,
        dialog_json_path="dialog_configs/thesis_dialogs.json",
        participant_id=participant_id,
    )

    session_manager.run()

    # =========================
    # 5. CALCULATE HEARTS
    # =========================

    participant_file = Path("participants") / f"{participant_id}.json"

    answer_key = {
        "q1_answer": "eye",
        "q2_answer": "ear",
        "q3_answer": "nose",
        "q4_answer": "mouth",
        "q5_answer": "lips",
        "q6_answer": "toes",
        "q7_answer": "face",
        "q8_answer": "ear",
    }

    if participant_file.exists():

        with open(participant_file, "r") as f:
            participant_data = json.load(f)

        latest_session = participant_data["sessions"][-1]
        user_model = latest_session["summary"]["user_model"]

        # =========================
        # HEART CALCULATION
        #
        # A heart is awarded if:
        # - the first answer is correct OR
        # - the second attempt is correct
        #
        # Example:
        # q2_answer = "banana"
        # q2_answer_second = "ear"
        #
        # -> still receives the heart.
        # =========================

        hearts = 0

        for answer_variable, correct_answer in answer_key.items():

            first_answer = user_model.get(answer_variable)

            second_answer = user_model.get(
                f"{answer_variable}_second"
            )

            if (
                first_answer == correct_answer
                or second_answer == correct_answer
            ):
                hearts += 1

        latest_session["summary"]["hearts_earned"] = hearts
        latest_session["summary"]["max_hearts"] = len(answer_key)

        participant_data["summary"]["latest_hearts"] = hearts
        participant_data["summary"]["latest_max_hearts"] = len(answer_key)

        with open(participant_file, "w") as f:
            json.dump(participant_data, f, indent=2)

        print(f"Hearts saved: {hearts}/{len(answer_key)}")

    sys.exit()