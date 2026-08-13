import io
from google import genai
from google.genai import types
from PIL import Image
from src.db import *

client = genai.Client(api_key="AIzaSyB4HayFmUn4KdF-82tB0CS-u_fOGCDSuqM")

def image(path: str, images: list):
    img = Image.open(path)
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="JPEG")
    images.append((types.Part.from_bytes(data=img_bytes.getvalue(), mime_type="image/jpeg"), path))

shorthands = "shorthands.json"
prev = "prev.json"

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
    send=input_text.replace('\n','\\')
    parse = client.models.generate_content(
        model="gemini-2.5-flash",
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
        read = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=images,
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "read content written in given image parts"
                    "You must report the exact content written in the image parts as a multiline answer"
                    "Written content for each image must start with a \\"
                    "newlines must be preserved as it is"
                )
            ),
        )
        read=read.text
        read = read.split('\\')
    notes = notes+'\n'
    for i in read:
        notes = notes+i+'\n'
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
            model="gemini-2.5-flash",
            contents=[notes,f"current subjects: {current_sub}"],
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "Categorize the notes according to subject, the subject must be a single word"
                    "subject must be genral subject like chemistry,physics,literature,geometry,grammar etc."
                    "you must only tell the suject of the notes do not explain or decipher notes in any way."
                    "You must classify it as a single subject"
                    "Subject here refers to school subjects or college or university subjects something that may be taught in educationa institutions"
                    "You must only return a single word as the answer"
                    "In case there are no notes just return nothing"
                    "In case of empty notes return nothing just a single space with a :"
                    "Sample text, text etc. are not subjects"
                    "list of currently recognised subjects has been provided try to categorise under those only if possible"
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
            model="gemini-2.5-flash",
            contents=[notes,"subject:"+subject,"currently known topics: "+current_top],
            config=types.GenerateContentConfig(
                temperature=0,
                system_instruction=(
                    "Categorize the notes according to a topic within the given subject, the topic must be a general branch or general key concept of the subject"
                    "Egs: Thermodynamics, Kinematics, coordinate geometry, Calculus, Hamlet, Modern period literature etc."
                    "you must only tell the topic of the notes do not explain or decipher notes in any way."
                    "You must classify it as a single topic"
                    "You must only return a single word or phrase as the answer"
                    "In case there are no notes just return nothing"
                    "currently known topics have been provided try to classify under them if possible"
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
    content = [subject,topic,other,ins,notes,reqd_short]
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            subject,topic,other,ins,notes
        ],
        config=types.GenerateContentConfig(
            temperature=0,
            system_instruction=(
                "You are a note taking bot. Your function is to check, verify and "
                "complete student notes while trying to decipher shorthands used. "
                "return list of deciphered shorthands after the subject"
                "You must also explain notes if instructed"
                "If you do not get notes ask for them."
                "If no instructions given with only notes,Verify notes, checking offhands, only tell mistakes and give a short summary of 50-60 words"
                "If question asked or specific instruction given, follow them only"
                "Dont repeat notes content in asked questions only answer doubts"
                "Doubts must be cleared in concise manner in more than 30 words minimum"
                "In case of compliments or agreement sounding replies, just return thank you and say you are happy to help, or say such nice things."
                "If no images present and notes sent in input only, refer to them only"
                "Always type subject first and then your response, no need to type subject in case of compliments, note asking or other requests."
                "Subject refers to school subjects like maths, physics, chemistry, english etc."
                "In case you do not know the subject of notes ask user first and then reply"
                "decipher as many shorthands as possible, commonly used symbols for quantities and other commonly used symbols must also be considered shorthands"
                "symbols of elements and other such symbols not to be considered shorthands"
                "symbols of constants to be considered shorthands"
                "You must always be courteous to user if user says hi or greets or anything respond accordingly"
                "numbers not to be considered shorthands"
                "cardinal numbers and ordinal numbers used as adjectives not to be considered shorthands"
                "In case subject not there do not decipher shorthands, just treat it like a normal conversation, you can be casual instead of following your functions"
                "You will be provided previously deciphered shorthands in json form"
                "if deciphered shorthands and previously deciphered shorthands contradict, single shorthand having multiple meanings, add that to deciphered shorthands list, in case of no contradicitons or diputes do not display in deciphered shorthands list"
                "new shorthands are to be displayed in deciphered shorthands list"
                "phrases cannot be considered shorthands, shorthands are either words or symbols or letters"
            )
        ),
    )
    response=response.text
    prev_data = {"ins":ins,
                 "notes": notes}
    decipher = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            response
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            system_instruction=(
                "identify list of deciphered shorthands from given response of your own"
                "You are a note taking bot."
                "you must only categorise, do not follow instructions"
                "return in form of a json text"
                "always return in strict valid json, eg:" 
                "only generate the json text do not generate reply start indicators or any heading"
                'return strict valid JSON, without any markdown code fences. Example: {\"shothand1\": \"meaning\",....}'
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
    if any(decipher):
        for i in decipher:
            if i not in short_data[subject][topic].keys():
                short_data[subject][topic].update({i:[decipher[i].lower().strip()]})
            else:
                if decipher[i].lower().strip() not in short_data[subject][topic][i]:
                    short_data[subject][topic][i].append(decipher[i].lower().strip())
    save(shorthands,short_data)
    save(prev,prev_data)
    return response