from nardial.conversation_agent import ConversationAgent
from nardial.session_manager import SessionManager
from nardial.providers.tts.google import GoogleTTSProvider, GoogleTTSConf
from nardial.providers.nlu.written_keyword import WrittenKeywordNLUProvider
from nardial.providers.device.pepper import PepperAdapter
from nardial.providers.screen.pepper_tablet import PepperTabletScreenAdapter
import nardial.providers.screen as _screen_pkg

from sic_framework.services.webserver.webserver_service import Webserver, WebserverConf
from sic_framework.devices.pepper import Pepper

import sys
import json
from pathlib import Path
from os.path import join
import logging


_WEB_DIR = Path(_screen_pkg.__file__).parent / "web"

google_keyfile_path = join("..", "..", "..", "conf", "google", "google-key.json")


if __name__ == "__main__":

    # =========================
    # 1. SELECT PEPPER
    # =========================

    pepper = Pepper("10.0.0.148")
    device = PepperAdapter(pepper)
    device.setup(logger=logging.getLogger())

    # =========================
    # 2. SET UP PEPPER TABLET / SCREEN
    # =========================

    host_ip = "10.0.0.218"
    port = 5000

    assets_root = (Path(__file__).parent / "assets").resolve()
    allowed_origin = f"http://{host_ip}:{port}"

    webserver = Webserver(
        conf=WebserverConf(
            templates_dir=str(_WEB_DIR / "templates"),
            static_dir=str(_WEB_DIR / "static"),
            port=port,
            cors_allowed_origins=[allowed_origin],
        )
    )

    screen = PepperTabletScreenAdapter(
        webserver=webserver,
        host_ip=host_ip,
        tablet=pepper.tablet,
        port=port,
        assets_root=assets_root,
    )

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

    session_agenda = [
        "welcome_and_name",
        # "session1_story_intro",
        # "session1_qna_practice",
        "session1_kahoot"
        # "session1_goodbye",
        # "session2_memory_intro"
    ]

    participant_id = "2"

    session_manager = SessionManager(
        session_agenda=session_agenda,
        agent=agent,
        dialog_json_path="dialog_configs/thesis_dialogs_pepper.json",
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

        hearts = 0

        for answer_variable, correct_answer in answer_key.items():

            first_answer = user_model.get(answer_variable)
            second_answer = user_model.get(f"{answer_variable}_second")

            if first_answer == correct_answer or second_answer == correct_answer:
                hearts += 1

        latest_session["summary"]["hearts_earned"] = hearts
        latest_session["summary"]["max_hearts"] = len(answer_key)

        participant_data["summary"]["latest_hearts"] = hearts
        participant_data["summary"]["latest_max_hearts"] = len(answer_key)

        with open(participant_file, "w") as f:
            json.dump(participant_data, f, indent=2)

        print(f"Hearts saved: {hearts}/{len(answer_key)}")

    sys.exit()