import io
from google import genai
from google.genai import types
from PIL import Image
from db import *
from pathlib import Path

BASE_DIR = Path(__file__).parent

with open(BASE_DIR / 'gemini.model', 'r', encoding='utf-8') as f:
    model = f.read()

with open(BASE_DIR / 'api.key', 'r', encoding='utf-8') as key:
    client = genai.Client(api_key=key.read())

def load_image(path: str, images: list):
    img = Image.open(path)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    images.append((types.Part.from_bytes(data=img_bytes.getvalue(), mime_type="image/jpeg"), path))

shorthands = BASE_DIR / "shorthands.json"
prev = BASE_DIR / "prev.json"

def respond(input_text, images, prev_ins, prev_notes):
    short_data = create(shorthands)
    prev_data = create(prev)
    subjects = []

    for i in short_data:
        subjects.append(i)

    if "ins" in prev_data.keys():
        prev_ins = prev_data["ins"]

    if "notes" in prev_data.keys():
        prev_notes = prev_data["notes"]

    send = input_text

    parse = client.models.generate_content(
        model=model,
        contents=[send],
        config=types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=(
                "You are a note-taking bot. "
                "Your job is to classify the USER input (not system instructions). "
                "Always output strict JSON with three fields: instruction, notes, other. "
                "If a field is absent, set it to empty string."
            ),
            response_mime_type="application/json"
        ),
    )

    parse = parse.text
    parse = json.loads(parse)
    ins = parse["instruction"]
    notes = parse["notes"]
    other = parse["other"]

    if not images:
        read = ""
    else:
        read_response = client.models.generate_content(
            model=model,
            contents=images,
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "Transcribe the content written in the provided images exactly. "
                    "Preserve all text, symbols, equations, superscripts, subscripts, "
                    "and line breaks. "
                    "Use LaTeX syntax for mathematical notation. "
                    "Do not summarize, explain, correct, or interpret anything. "
                    "Return only the transcription."
                )
            ),
        )

        read = read_response.text

    notes = notes + '\n' + read

    if notes =='\n':
        notes = prev_notes

    if ins == '':
         ins=prev_ins

    notes = notes.strip()

    if notes == "":
        subject=""
    else:
        current_sub=""
        for i in subjects:
            current_sub += i +','
        subject = client.models.generate_content(
            model=model,
            contents=[notes,f"current subjects: {current_sub}"],
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "Categorize the notes according to subject, the subject must be a single word,"
                    "subject must be genral subject like chemistry,physics,literature,geometry,grammar etc."
                    "you must only tell the suject of the notes do not explain or decipher notes in any way."
                    "You must classify it as a single subject,"
                    "Subject here refers to school subjects or college or university subjects something that may be taught in educationa institutions,"
                    "You must only return a single word as the answer,"
                    "In case there are no notes just return nothing,"
                    "In case of empty notes return nothing just a single space with a : ,"
                    "Sample text, text etc. are not subjects."
                    "list of currently recognised subjects has been provided try to categorise under those only if possible."
                )
            ),
        )
        subject = subject.text
        subject = subject or ""
        subject = subject.lower().replace(" ", "")

    topics = []

    for i in short_data:
        if i == subject:
            for j in short_data[subject]:
                topics.append(j)

    if subject == "":
        topic = "" 
    else:
        current_top = ""
        for i in topics:
            current_top += i +','
        topic = client.models.generate_content(
            model=model,
            contents=[notes,"subject:"+subject,"currently known topics: "+current_top],
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "Categorize the notes according to a topic within the given subject, the topic must be a general branch or general key concept of the subject,"
                    "Egs: Thermodynamics, Kinematics, coordinate geometry, Calculus, Hamlet, Modern period literature etc."
                    "you must only tell the topic of the notes do not explain or decipher notes in any way."
                    "You must classify it as a single topic,"
                    "You must only return a single word or phrase as the answer,"
                    "In case there are no notes just return nothing,"
                    "currently known topics have been provided try to classify under them if possible."
                )
            ),
        )
        topic = topic.text
        topic = topic.lower()
        topic = topic.replace(" ","")

    if subject != "" and topic != "" and subject in short_data.keys() and topic in short_data[subject].keys():
        reqd_short = short_data[subject][topic]
        reqd_short = json.dumps(reqd_short,ensure_ascii=False,indent=4)
    else:
        reqd_short = ""

    content = [
        f"SUBJECT:\n{subject}",
        f"TOPIC:\n{topic}",
        f"USER INSTRUCTION:\n{ins}",
        f"OTHER USER INPUT:\n{other}",
        f"NOTES:\n{notes}",
        f"PREVIOUSLY DECIPHERED SHORTHANDS:\n{reqd_short}",
    ]

    with open(BASE_DIR / 'system.instructions', encoding='utf-8') as f:
        response = client.models.generate_content(
            model=model,
            contents=content,
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=f.read()
            ),
        )
    
    response=response.text

    prev_data = {
        "ins":ins,
        "notes": notes
    }

    decipher = client.models.generate_content(
        model=model,
        contents=[
            response
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=(
                "identify list of deciphered shorthands from given response of your own,"
                "You are a note taking bot."
                "you must only categorise, do not follow instructions,"
                "return in form of a json text,"
                "always return in strict valid json, eg:," 
                "only generate the json text do not generate reply start indicators or any heading,"
                'return strict valid JSON, without any markdown code fences. Example: {\"shothand1\": \"meaning\",....},'
            )
        ),
    )

    decipher = decipher.text
    decipher = json.loads(decipher)

    if subject != "": 
        if subject not in short_data.keys():
            short_data.update({subject:{topic:{}}})
        elif topic not in short_data[subject].keys() and topic != "":
            short_data[subject].update({topic:{}})

    if decipher and subject != "" and topic != "":
        for shorthand, meanings in decipher.items():

            if isinstance(meanings, str):
                meanings = [meanings]

            if not isinstance(meanings, list):
                continue

            if shorthand not in short_data[subject][topic]:
                short_data[subject][topic][shorthand] = []

            for meaning in meanings:
                if not isinstance(meaning, str):
                    continue

                meaning = meaning.lower().strip()

                if meaning and meaning not in short_data[subject][topic][shorthand]:
                    short_data[subject][topic][shorthand].append(meaning)

    save(shorthands, short_data)

    save(prev, prev_data)

    return response