import copy
import re

ROMAN_HINDI_HINTS = ["nahi", "gaadi", "gadi", "awaaz", "aawaz", "garam", "thanda", "khich", "jhattke"]

QUESTION_LOCALIZATION_MAP = {
    "Is the engine having difficulty starting?": "Engine start karne me dikkat aa rahi hai?",
    "Do you feel jerking or misfire during acceleration?": "Acceleration pe jerk ya misfire feel hota hai?",
    "Do you feel power loss during acceleration?": "Acceleration pe power loss feel hota hai?",
    "Is the check engine light on?": "Check engine light ON hai?",
    "Does the engine jerk during acceleration?": "Acceleration pe engine jerk karta hai?",
    "Has the mileage dropped suddenly?": "Mileage suddenly kam ho gaya hai?",
    "Has the car lost pickup?": "Car me pickup kam ho gaya hai?",
    "Do you notice a drop in mileage?": "Mileage drop feel ho raha hai?",
    "Is the RPM fluctuating at idle?": "Idle pe RPM up-down ho raha hai?",
    "Does the car stall occasionally?": "Car kabhi-kabhi band ho jaati hai?",
    "Do you hear a thud during acceleration?": "Acceleration pe thud sound aati hai?",
    "Is engine vibration stronger at idle?": "Idle pe engine vibration zyada feel hota hai?",
    "Do you hear rattling noise during a cold start?": "Cold start pe rattling noise aati hai?",
    "Do you hear unusual noise immediately after start?": "Engine start karte hi ajeeb awaaz aati hai?",
    "Is the idle RPM higher than normal?": "Idle pe RPM normal se zyada hai?",
    "Do you hear a hissing sound from the engine?": "Engine se hissing sound aati hai?",
    "Is the coolant level low?": "Coolant level low hai?",
    "Is the temperature warning showing?": "Temperature warning aa rahi hai?",
    "Is the radiator fan not running?": "Fan chal nahi raha?",
    "Does the car overheat in traffic?": "Car traffic me overheat hoti hai?",
    "Does overheating happen even at high speed?": "High speed pe bhi overheating ho rahi hai?",
    "Does the engine heat up quickly?": "Engine jaldi heat ho jata hai?",
    "Does the temperature rise suddenly?": "Temperature suddenly shoot karta hai?",
    "Is coolant leakage visible?": "Coolant leak visible hai?",
    "Is the engine overheating continuously?": "Engine continuously overheat ho raha hai?",
    "Do you hear squeaking while braking?": "Brake lagate time squeaking sound aati hai?",
    "Do the brakes feel weak?": "Brake performance weak feel ho raha hai?",
    "Does the steering vibrate while braking?": "Brake lagate waqt steering vibrate karti hai?",
    "Is vibration stronger during high-speed braking?": "High speed braking pe vibration zyada hota hai?",
    "Does the brake pedal feel soft?": "Brake pedal soft lag raha hai?",
    "Is the brake warning light on?": "Brake warning light ON hai?",
    "Does the car pull to one side while braking?": "Brake lagate waqt car ek side khich rahi hai?",
    "Is one wheel heating up more than the others?": "Ek wheel zyada heat ho raha hai?",
    "Is the ABS light on in the dashboard?": "ABS light dashboard pe ON hai?",
    "Do you hear a humming sound while driving?": "Driving ke time humming ya ghurrr sound aati hai?",
    "Does the noise increase with speed?": "Speed badhne pe noise increase hota hai?",
    "Does the car pull to one side on a straight road?": "Car seedhi road pe ek side khich rahi hai?",
    "Does the steering fail to stay centered?": "Steering center me nahi rehta?",
    "Is the car starting slowly?": "Car start slow ho rahi hai?",
    "Do the headlights look dim?": "Headlights dim lag rahe hain?",
    "Is the battery discharging repeatedly?": "Battery bar-bar discharge ho rahi hai?",
    "Does the battery light come on while driving?": "Driving ke time battery light ON ho jaati hai?",
    "Do you hear a clicking sound while starting?": "Start karte time clicking sound aati hai?",
    "Is the engine not cranking?": "Engine crank nahi ho raha?",
    "Does the RPM rise without an increase in speed?": "RPM badh raha hai lekin speed nahi badh rahi?",
    "Do you notice a burning smell from the clutch?": "Clutch se burning smell aati hai?",
    "Has gear shifting become hard?": "Gear shift hard ho gaya hai?",
    "Is there noise coming from the gearbox?": "Gearbox se noise aa rahi hai?",
    "Has AC cooling become weak?": "AC cooling weak ho gayi hai?",
    "Is the AC running but not blowing cold air?": "AC chal raha hai par thandi hawa nahi aa rahi?",
    "Is the AC not cooling at all?": "AC bilkul cooling nahi kar raha?",
    "Do you hear noise as soon as the AC is turned on?": "AC on karte hi noise aati hai?",
    "Has the car lost power?": "Car ki power kam ho gayi hai?",
    "Is there a loud noise coming from the car?": "Car se loud awaaz aa rahi hai?",
    "Is there no specific problem right now?": "Koi specific problem nahi hai?",
    "Would you like a general health check?": "General check karwana chahte ho?",
    "Does the problem appear during acceleration?": "Kya problem acceleration pe feel hoti hai?",
    "Does the issue happen while starting the car?": "Kya issue start time pe aata hai?",
    "Do you hear any abnormal sound?": "Kya abnormal sound aa raha hai?"
}


PHRASE_MAPPINGS = {
    "low power": [
        "pickup nahi hai", "power nahi hai", "gaadi mein power nahi",
        "acceleration slow", "speed nahi badh rahi", "race nahi leti",
        "gaadi bhaag nahi rahi", "weak acceleration", "power kam hai",
        "pickup kam hai", "கார் பவர் இல்லை", "పవర్ లేదు", "পাওয়ার নেই"
    ],
    "vibration": [
        "gaadi hil rahi hai", "car hil rahi hai", "engine hil raha hai",
        "kampan ho rahi hai", "body vibration", "steering vibration",
        "vibrate kar rahi", "vibrate ho rahi", "vibration aa rahi",
        "கம்பனம்", "కంపనం", "কম্পন", "വൈബ്രേഷൻ", "ಕಂಪನ"
    ],
    "brake vibration": [
        "brake lagate vibration", "brake pe vibration", "braking pe vibration",
        "brake lagate steering hilti", "brake lagate car hilti",
        "brake lagane par vibration", "brake lagane par steering vibrate"
    ],
    "misfire": [
        "jhattke maar rahi hai", "jerk aa raha", "engine skip kar raha",
        "engine cut ho raha", "uneven running", "engine miss kar raha",
        "jerking", "jerks", "குலுக்கு", "ঝাঁকুনি", "జర్క్"
    ],
    "not starting": [
        "start nahi ho rahi", "self maarne par start nahi",
        "car start nahi hoti", "engine start issue", "crank nahi ho raha",
        "gaadi start nahi", "gadi start nahi", "self nahi le rahi",
        "start nahi leti", "start nahi ho raha", "no crank",
        "ஸ்டார்ட் ஆகவில்லை", "స్టార్ట్ కావడం లేదు",
        "স্টার্ট নিচ্ছে না", "സ്റ്റാർട്ട് ആവുന്നില്ല", "start avvatledu",
        "start aagavillai", "start hocche na", "ஆகவில்லை",
        "ആവുന്നില്ല", "ಆಗುತ್ತಿಲ್ಲ"
    ],
    "stalling": [
        "engine band ho jata hai", "drive karte band ho jati hai",
        "idle pe band ho jati hai", "suddenly band ho jati hai",
        "band ho rahi hai", "stall ho rahi hai", "বন্ধ হয়ে যাচ্ছে",
        "ஆஃப் ஆகிறது", "ఆగిపోతుంది"
    ],
    "noise": [
        "awaaz aa rahi hai", "ajeeb sound", "tik tik sound",
        "khad khad sound", "noise aa raha hai", "sound aa raha hai",
        "humming noise", "ghurrr sound", "speed badhne par awaaz",
        "சத்தம்", "শব্দ", "శబ్దం", "శబ్దం వస్తోంది", "ശബ്ദം", "ಶಬ್ದ",
        "கேட்கிறது", "করে", "వస్తోంది", "കേൾക്കുന്നു", "ಬರುತ್ತಿದೆ"
    ],
    "humming sound while driving": [
        "speed badhne par humming", "speed badhne par humming noise",
        "driving ke time humming", "ghurrr sound speed ke sath",
        "humming noise while driving"
    ],
    "squeaking while braking": [
        "brake squeak", "brake squeaking", "brake se cheekh awaaz",
        "brake lagate squeaking", "braking squeak"
    ],
    "car pulling to one side while braking": [
        "brake lagate ek side", "braking pe pull", "pulls to one side while braking",
        "car pulls to one side while braking", "brake lagate car khich rahi"
    ],
    "knocking": [
        "knocking sound", "tak tak sound", "engine knocking",
        "pinging sound", "டக் டக்", "টক টক", "టక్ టక్"
    ],
    "overheating": [
        "engine garam ho raha hai", "heat ho rahi hai",
        "temperature high", "overheat ho raha hai", "bahut garam",
        "heat issue", "கார் அதிக சூடு", "ఇంజిన్ వేడెక్కుతోంది",
        "ইঞ্জিন গরম হচ্ছে", "engine heat", "వేడెక్కుతోంది",
        "গরম হচ্ছে", "அதிக சூடு", "ചൂടാകുന്നു"
    ],
    "fan not working": [
        "fan nahi chal raha", "fan chal nahi raha", "radiator fan nahi chal raha",
        "fan not running", "fan not turning", "fan dead"
    ],
    "brake failure": [
        "brake kaam nahi kar raha", "brake fail", "brake nahi lag rahe",
        "ब्रेक नहीं लग रहे", "brake not working"
    ],
    "brake weak": [
        "brake weak hai", "brake kam lag rahe", "rukne me time lag raha",
        "brake soft", "ബ്രേക്ക് വീക്ക്", "ব্রেক কম ধরছে"
    ],
    "steering heavy": [
        "steering tight hai", "steering hard hai", "hard steering",
        "steering bahut heavy", "ஸ்டீயரிங் ஹார்ட்", "స్టీరింగ్ గట్టిగా ఉంది"
    ],
    "pulling": [
        "ek side khich rahi", "ek side khinch rahi", "left pull",
        "right pull", "car left ja rahi", "car right ja rahi",
        "seedhi road pe khich rahi", "one side pull"
    ],
    "steering loose": [
        "steering halka hai", "control loose hai", "steering loose",
        "play in steering"
    ],
    "burning smell": [
        "jalne ki smell", "burn smell", "garam smell", "burning smell",
        "எரியும் வாசனை", "পোড়া গন্ধ"
    ],
    "bad smell": [
        "bad smell", "gandi smell", "smell aa rahi hai", "odor",
        "வாசனை", "গন্ধ", "వాసన"
    ],
    "tail light stays on after ignition off": [
        "tail light ignition off ke baad bhi on", "tail light band nahi ho rahi",
        "rear light car off ke baad on", "parking light band nahi ho rahi",
        "brake light car band hone ke baad on", "tail lamp on after key off"
    ],
    "headlight throw low": [
        "head light throw low", "headlight throw kam hai", "low beam weak",
        "headlight low throw", "raat me visibility kam", "headlight dim throw",
        "headlight light throw poor"
    ],
    "check engine light": [
        "check engine light on", "engine check light", "engine warning light",
        "yellow engine light", "malfunction indicator lamp", "mil light"
    ],
    "check engine light flashing": [
        "check engine light blink", "check engine light flashing",
        "engine light blink kar rahi", "engine warning blink"
    ],
    "oil pressure warning light": [
        "oil light on", "red oil light", "engine oil light",
        "oil pressure light", "oil lamp on"
    ],
    "temperature warning light": [
        "temperature light on", "red temperature light", "engine temperature warning",
        "coolant temperature light", "temp warning"
    ],
    "brake warning light": [
        "brake light dashboard", "red brake light", "parking brake light on",
        "brake warning on", "brake fluid light"
    ],
    "tpms warning light": [
        "tpms light", "tyre pressure light", "tire pressure light",
        "low tyre pressure symbol", "low tire pressure symbol"
    ],
    "basic maintenance question": [
        "basic maintenance", "routine maintenance", "maintenance question",
        "service schedule", "periodic service", "what maintenance should i do",
        "general maintenance", "service checklist"
    ],
    "engine oil change question": [
        "when to change engine oil", "engine oil kab change", "oil change due",
        "engine oil service", "which engine oil interval", "oil service kab"
    ],
    "tyre pressure question": [
        "tyre pressure kitna", "tire pressure kitna", "tyre pressure check",
        "tyre rotation kab", "when to rotate tyres", "tyre maintenance"
    ],
    "battery maintenance question": [
        "battery kab change", "battery health check", "battery maintenance",
        "when to replace battery", "battery weak prevention"
    ],
    "brake maintenance question": [
        "brake pad kab change", "brake maintenance", "brake service",
        "brake fluid kab change", "brake inspection"
    ],
    "coolant maintenance question": [
        "coolant kab change", "coolant maintenance", "coolant level check",
        "radiator coolant", "cooling system maintenance"
    ],
    "filter maintenance question": [
        "air filter kab change", "cabin filter kab change", "filter maintenance",
        "fuel filter kab change", "service filter checklist"
    ],
    "long trip maintenance checklist": [
        "long trip checklist", "long drive checklist", "road trip maintenance",
        "trip se pehle maintenance", "highway trip car check"
    ],
    "dashboard warning light photo uploaded": [
        "dashboard light photo uploaded", "dash light photo uploaded",
        "warning light image uploaded", "dashboard symbol photo uploaded"
    ],
    "white smoke": [
        "safed dhuan", "white dhuan", "white smoke", "exhaust se safed dhuan",
        "silencer se white smoke"
    ],
    "black smoke": [
        "black smoke", "kala dhuan", "exhaust se kala dhuan",
        "silencer se black smoke", "acceleration pe black smoke"
    ],
    "blue smoke": [
        "blue smoke", "neela dhuan", "oil burning smoke",
        "exhaust se blue smoke", "oil jalne ka smoke"
    ],
    "ac not cooling": [
        "ac thanda nahi kar raha", "ac cooling nahi hai", "ac cooling problem",
        "ac not cold", "ac thandi hawa nahi de raha", "blower chal raha par cooling nahi",
        "ac hawa garam hai", "குளிர்ச்சி இல்லை", "చల్లగా లేదు", "ঠান্ডা করছে না"
    ],
    "ac weak": [
        "ac weak hai", "cooling kam hai", "airflow weak"
    ],
    "coolant loss": [
        "coolant kam ho raha hai", "pani kam ho raha hai", "coolant leak",
        "கூலண்ட் குறைகிறது", "కూలెంట్ తగ్గుతోంది", "কুল্যান্ট কমছে"
    ],
    "rough running": [
        "gaadi ajeeb chal rahi hai", "smooth nahi chal rahi",
        "rough chal rahi hai", "idle rough", "engine rough"
    ],
    "clutch slip under load": [
        "clutch slipping", "clutch slip", "rpm badh raha speed nahi",
        "rpm increases speed not increasing", "rpm badhta hai speed nahi",
        "speed nahi badh rahi rpm badh raha"
    ],
    "airbag warning light on": [
        "airbag light", "airbag warning", "srs light", "srs warning"
    ],
    "abs warning light": [
        "abs light", "abs warning", "abs light dashboard"
    ],
    "car shuts off while driving": [
        "car shuts off while driving", "driving me car band ho gayi",
        "chalti gaadi band", "drive karte car band", "engine shuts off while driving"
    ]
}


TERM_MAPPINGS = {
    "gaadi": "car",
    "gadi": "car",
    "car": "car",
    "engine": "engine",
    "brake": "brake",
    "battery": "battery",
    "coolant": "coolant",
    "radiator": "radiator",
    "fan": "fan",
    "steering": "steering",
    "clutch": "clutch",
    "gear": "gear",
    "ac": "ac",
    "pickup": "pickup",
    "power": "power",
    "mileage": "mileage",
    "start": "start",
    "self": "start",
    "awaaz": "noise",
    "aawaz": "noise",
    "garam": "hot",
    "thanda": "cool",
    "kampan": "vibration",
    "jhattke": "jerk",
    "jerk": "jerk",
    "khich": "pulling",
    "khinch": "pulling",
    "pull": "pulling",
    "pulling": "pulling",
    "light": "light",
    "dashboard": "dashboard",
    "dash": "dashboard",
    "ignition": "ignition",
    "tail": "tail",
    "lamp": "light",
    "headlight": "headlight",
    "head": "head",
    "tpms": "tpms",
    "smell": "smell",
    "dhuan": "smoke",
    "dhua": "smoke",
    "safed": "white",
    "kala": "black",
    "neela": "blue",
    "கார்": "car",
    "ஸ்டார்ட்": "start",
    "இன்ஜின்": "engine",
    "எஞ்சின்": "engine",
    "பிரேக்": "brake",
    "ஸ்டீயரிங்": "steering",
    "கூலண்ட்": "coolant",
    "பேட்டரி": "battery",
    "கியர்": "gear",
    "சத்தம்": "noise",
    "வெப்பம்": "heat",
    "ஆகவில்லை": "not starting",
    "స్టార్ట్": "start",
    "కారు": "car",
    "ఇంజిన్": "engine",
    "బ్రేక్": "brake",
    "స్టీరింగ్": "steering",
    "కూలెంట్": "coolant",
    "బ్యాటరీ": "battery",
    "గేర్": "gear",
    "శబ్దం": "noise",
    "వేడెక్కుతోంది": "overheating",
    "গাড়ি": "car",
    "স্টার্ট": "start",
    "ইঞ্জিন": "engine",
    "ব্রেক": "brake",
    "স্টিয়ারিং": "steering",
    "কুল্যান্ট": "coolant",
    "ব্যাটারি": "battery",
    "গিয়ার": "gear",
    "শব্দ": "noise",
    "গরম": "hot",
    "കാർ": "car",
    "സ്റ്റാർട്ട്": "start",
    "എഞ്ചിൻ": "engine",
    "ബ്രേക്ക്": "brake",
    "സ്റ്റിയറിംഗ്": "steering",
    "കൂളന്റ്": "coolant",
    "ബാറ്ററി": "battery",
    "ശബ്ദം": "noise",
    "ചൂടാകുന്നു": "overheating",
    "ആവുന്നില്ല": "not starting",
    "ಗಾಡಿ": "car",
    "ಸ್ಟಾರ್ಟ್": "start",
    "ಎಂಜಿನ್": "engine",
    "ಬ್ರೆಕ್": "brake",
    "ಸ್ಟೀರಿಂಗ್": "steering",
    "ಬ್ಯಾಟರಿ": "battery",
    "ಶಬ್ದ": "noise",
    "ಆಗುತ್ತಿಲ್ಲ": "not starting"
}


FAILURE_DB_PHRASE_REPLACEMENTS = [
    (r"engine start karne me dikkat aa rahi hai\??", "Is the engine having difficulty starting?"),
    (r"acceleration pe jerk ya misfire feel hota hai\??", "Do you feel jerking or misfire during acceleration?"),
    (r"acceleration pe power loss feel hota hai\??", "Do you feel power loss during acceleration?"),
    (r"check engine light on hai\??", "Is the check engine light on?"),
    (r"acceleration pe engine jerk karta hai\??", "Does the engine jerk during acceleration?"),
    (r"mileage suddenly kam ho gaya hai\??", "Has the mileage dropped suddenly?"),
    (r"car me pickup kam ho gaya hai\??", "Has the car lost pickup?"),
    (r"mileage drop feel ho raha hai\??", "Do you notice a drop in mileage?"),
    (r"idle pe rpm up-down ho raha hai\??", "Is the RPM fluctuating at idle?"),
    (r"car kabhi-kabhi band ho jaati hai\??", "Does the car stall occasionally?"),
    (r"acceleration pe thud sound aati hai\??", "Do you hear a thud during acceleration?"),
    (r"idle pe engine vibration zyada feel hota hai\??", "Is engine vibration stronger at idle?"),
    (r"cold start pe rattling noise aati hai\??", "Do you hear rattling noise during a cold start?"),
    (r"engine start karte hi ajeeb awaaz aati hai\??", "Do you hear unusual noise immediately after start?"),
    (r"idle pe rpm normal se zyada hai\??", "Is the idle RPM higher than normal?"),
    (r"engine se hissing sound aati hai\??", "Do you hear a hissing sound from the engine?"),
    (r"coolant level low hai\??", "Is the coolant level low?"),
    (r"temperature warning aa rahi hai\??", "Is the temperature warning showing?"),
    (r"fan chal nahi raha\??", "Is the radiator fan not running?"),
    (r"car traffic me overheat hoti hai\??", "Does the car overheat in traffic?"),
    (r"high speed pe bhi overheating ho rahi hai\??", "Does overheating happen even at high speed?"),
    (r"engine jaldi heat ho jata hai\??", "Does the engine heat up quickly?"),
    (r"temperature suddenly shoot karta hai\??", "Does the temperature rise suddenly?"),
    (r"coolant leak visible hai\??", "Is coolant leakage visible?"),
    (r"engine continuously overheat ho raha hai\??", "Is the engine overheating continuously?"),
    (r"brake lagate time squeaking sound aati hai\??", "Do you hear squeaking while braking?"),
    (r"brake performance weak feel ho raha hai\??", "Do the brakes feel weak?"),
    (r"brake lagate waqt steering vibrate karti hai\??", "Does the steering vibrate while braking?"),
    (r"high speed braking pe vibration zyada hota hai\??", "Is vibration stronger during high-speed braking?"),
    (r"brake pedal soft lag raha hai\??", "Does the brake pedal feel soft?"),
    (r"brake warning light on hai\??", "Is the brake warning light on?"),
    (r"brake lagate waqt car ek side khich rahi hai\??", "Does the car pull to one side while braking?"),
    (r"ek wheel zyada heat ho raha hai\??", "Is one wheel heating up more than the others?"),
    (r"abs light dashboard pe on hai\??", "Is the ABS light on in the dashboard?"),
    (r"driving ke time humming ya ghurrr sound aati hai\??", "Do you hear a humming sound while driving?"),
    (r"speed badhne pe noise increase hota hai\??", "Does the noise increase with speed?"),
    (r"car seedhi road pe ek side khich rahi hai\??", "Does the car pull to one side on a straight road?"),
    (r"steering center me nahi rehta\??", "Does the steering fail to stay centered?"),
    (r"car start slow ho rahi hai\??", "Is the car starting slowly?"),
    (r"headlights dim lag rahe hain\??", "Do the headlights look dim?"),
    (r"battery bar-bar discharge ho rahi hai\??", "Is the battery discharging repeatedly?"),
    (r"driving ke time battery light on ho jaati hai\??", "Does the battery light come on while driving?"),
    (r"start karte time clicking sound aati hai\??", "Do you hear a clicking sound while starting?"),
    (r"engine crank nahi ho raha\??", "Is the engine not cranking?"),
    (r"rpm badh raha hai lekin speed nahi badh rahi\??", "Does the RPM rise without an increase in speed?"),
    (r"clutch se burning smell aati hai\??", "Do you notice a burning smell from the clutch?"),
    (r"gear shift hard ho gaya hai\??", "Has gear shifting become hard?"),
    (r"gearbox se noise aa rahi hai\??", "Is there noise coming from the gearbox?"),
    (r"ac cooling weak ho gayi hai\??", "Has AC cooling become weak?"),
    (r"ac chal raha hai par thandi hawa nahi aa rahi\??", "Is the AC running but not blowing cold air?"),
    (r"ac bilkul cooling nahi kar raha\??", "Is the AC not cooling at all?"),
    (r"ac on karte hi noise aati hai\??", "Do you hear noise as soon as the AC is turned on?"),
    (r"car ki power kam ho gayi hai\??", "Has the car lost power?"),
    (r"car se loud awaaz aa rahi hai\??", "Is there a loud noise coming from the car?"),
    (r"koi specific problem nahi hai\??", "Is there no specific problem right now?"),
    (r"general check karwana chahte ho\??", "Would you like a general health check?")
]


GENERIC_TEXT_REPLACEMENTS = {
    " kya ": " do ",
    " hai?": "?",
    " hai ": " ",
    " ho raha hai": " happening",
    " ho rahi hai": " happening",
    " aa rahi hai": " present",
    " aa raha hai": " present",
    " kam ": " low ",
    " zyada ": " excessive ",
    " start ": " start ",
    " mileage ": " mileage ",
    " power loss feel hota hai": " power loss",
    " weak feel ho raha hai": " feel weak",
    " on hai": " on",
    " bilkul ": " completely "
}


KEYWORDS = [
    "engine", "brake", "clutch", "gear", "battery", "alternator",
    "fuel", "injector", "filter", "turbo", "radiator", "coolant",
    "fan", "ac", "compressor", "steering", "suspension",
    "mount", "tyre", "alignment", "sensor", "misfire", "vibration",
    "noise", "overheating", "stalling", "not starting", "power loss",
    "maintenance", "service", "checklist", "engine oil", "tyre pressure",
    "brake fluid", "road trip"
]


def _clean_spaces(text):
    return re.sub(r"\s+", " ", text).strip()


def _apply_term_mappings(text):
    for source, target in TERM_MAPPINGS.items():
        text = text.replace(source.lower(), target)
    return text


def normalize_text(text):

    text = (text or "").lower().strip()
    text = _apply_term_mappings(text)

    for standard, variations in PHRASE_MAPPINGS.items():
        for phrase in variations:
            if phrase.lower() in text:
                text += " " + standard

    for source, target in GENERIC_TEXT_REPLACEMENTS.items():
        text = text.replace(source, target)

    for keyword in KEYWORDS:
        if keyword in text:
            text += " " + keyword

    return _clean_spaces(text)


def detect_input_language(text):

    sample = (text or "").strip()

    if not sample:
        return "en"

    if any("\u0900" <= ch <= "\u097f" for ch in sample):
        return "hi"

    lowered = sample.lower()

    hint_matches = sum(1 for token in ROMAN_HINDI_HINTS if token in lowered)

    if hint_matches >= 1:
        return "hi"

    return "en"


def translate_failure_db_text(text):

    normalized = (text or "").strip()

    for pattern, replacement in FAILURE_DB_PHRASE_REPLACEMENTS:
        normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)

    if normalized == text:
        lowered = _clean_spaces(_apply_term_mappings(text.lower()))
        for source, target in GENERIC_TEXT_REPLACEMENTS.items():
            lowered = lowered.replace(source.strip(), target.strip())
        normalized = lowered.capitalize()
        if normalized and not normalized.endswith("?") and text.strip().endswith("?"):
            normalized += "?"

    return _clean_spaces(normalized)


def normalize_failure_database_entries(entries):

    normalized_entries = copy.deepcopy(entries)

    for entry in normalized_entries:
        entry["questions"] = [
            {
                **question,
                "text": translate_failure_db_text(question.get("text", ""))
            }
            for question in entry.get("questions", [])
        ]

        entry["user_checks"] = [
            translate_failure_db_text(item)
            for item in entry.get("user_checks", [])
        ]

        entry["symptoms"] = [
            _clean_spaces(_apply_term_mappings(item.lower()))
            for item in entry.get("symptoms", [])
        ]

    return normalized_entries


def localize_question_text(text, language_code):

    if language_code != "hi":
        return text

    return QUESTION_LOCALIZATION_MAP.get(text, text)


def localize_questions(questions, language_code):

    localized = []

    for question in questions or []:
        localized.append({
            **question,
            "text": localize_question_text(question.get("text", ""), language_code)
        })

    return localized
