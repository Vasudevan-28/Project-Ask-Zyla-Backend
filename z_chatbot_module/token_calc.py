import json
import tiktoken

# data = {
#   "conversation_id": "69135428h535rt3w326015", 
#   "reply": "You mentioned earlier that your name is Deku. I'm Deku, your skincare assistant.",
#   "used_messages": [
#     {
#       "role": "system",
#       "content": "You are a helpful skincare assistant.\nRules:\n- Be concise, practical, and specific.\n- Personalize using PROFILE and SUMMARY when relevant.\n- If the user asks non-skincare questions, say you are focused on skincare.\n- Never invent product facts or medical claims.\n"
#     },
#     {
#       "role": "system",
#       "content": "PROFILE:\nName: Deku\nSkin type: oily\nConcerns: acne\nBudget max: ₹700.0"
#     },
#     {
#       "role": "system",
#       "content": "SUMMARY:\n• No name provided\n• No age given\n• Skin type: unknown\n• Budget: unknown\n• Allergies: unknown\n• Preferences: unknown\n\n• Key goal: Improve skincare\n• Unresolved questions: Skin type, budget, allergies, preferences\n• Strict do's: None mentioned\n• Strict don'ts: None mentioned"
#     },
#     {
#       "role": "user",
#       "content": "can you tell my name, pls?"
#     },
#     {
#       "role": "assistant",
#       "content": "I'm Deku, your skincare assistant. I don't have information about your name. If you'd like to share it, I can personalize our conversation."
#     },
#     {
#       "role": "user",
#       "content": "no, my name is Deku."
#     },
#     {
#       "role": "assistant",
#       "content": "Nice coincidence. Since we share the same name, I'll make sure to keep track of our conversation. Let's get started on your skincare concerns. What's your skin type, and what are your main concerns?"
#     },
#     {
#       "role": "user",
#       "content": "can you tell my name, pls?"
#     }
#   ],
#   "profile_used": {
#     "name": "Deku",
#     "skin_type": "oily",
#     "concerns": [
#       "acne"
#     ],
#     "allergies": [],
#     "avoid_ingredients": [],
#     "prefer_ingredients": [],
#     "budget_max": 700.0,
#     "fragrance_free": None
#   },
#   "summary": "• No name provided\n• No age given\n• Skin type: unknown\n• Budget: unknown\n• Allergies: unknown\n• Preferences: unknown\n\n• Key goal: Improve skincare\n• Unresolved questions: Skin type, budget, allergies, preferences\n• Strict do's: None mentioned\n• Strict don'ts: None mentioned"
# }

# data = {
#   "conversation_id": "691354288d953c0afa576015",
#   "reply": "Good morning. I'm doing well, thanks for asking. I'm focused on skincare, so let's get back to that. What's your skin type, and what are your main concerns?",
#   "used_messages": [
#     {
#       "role": "system",
#       "content": "You are a helpful skincare assistant.\nRules:\n- Be concise, practical, and specific.\n- Personalize using PROFILE and SUMMARY when relevant.\n- If the user asks non-skincare questions, say you are focused on skincare.\n- Never invent product facts or medical claims.\n"
#     },
#     {
#       "role": "system",
#       "content": "PROFILE:\nName: Deku\nSkin type: oily\nConcerns: acne\nBudget max: ₹700.0"
#     },
#     {
#       "role": "system",
#       "content": "SUMMARY:\n• No name provided\n• No age given\n• Skin type: unknown\n• Budget: unknown\n• Allergies: unknown\n• Preferences: unknown\n\n• Key goal: Improve skincare\n• Unresolved questions: Skin type, budget, allergies, preferences\n• Strict do's: None mentioned\n• Strict don'ts: None mentioned"
#     },
#     {
#       "role": "assistant",
#       "content": "Nice coincidence. Since we share the same name, I'll make sure to keep track of our conversation. Let's get started on your skincare concerns. What's your skin type, and what are your main concerns?"
#     },
#     {
#       "role": "user",
#       "content": "can you tell my name, pls?"
#     },
#     {
#       "role": "assistant",
#       "content": "You mentioned earlier that your name is Deku. I'm Deku, your skincare assistant."
#     },
#     {
#       "role": "user",
#       "content": "is your name and my name are same?"
#     },
#     {
#       "role": "assistant",
#       "content": "Yes, our names are the same. I'm Deku, and you are also Deku."
#     },
#     {
#       "role": "user",
#       "content": "good morning.. how are you?"
#     }
#   ],
#   "profile_used": {
#     "name": "Deku",
#     "skin_type": "oily",
#     "concerns": [
#       "acne"
#     ],
#     "allergies": [],
#     "avoid_ingredients": [],
#     "prefer_ingredients": [],
#     "budget_max": 700.0,
#     "fragrance_free": "null"
#   },
#   "summary": "• No name provided\n• No age given\n• Skin type: unknown\n• Budget: unknown\n• Allergies: unknown\n• Preferences: unknown\n\n• Key goal: Improve skincare\n• Unresolved questions: Skin type, budget, allergies, preferences\n• Strict do's: None mentioned\n• Strict don'ts: None mentioned"
# }


# data = """
# [{'role': 'system', 'content': 'You are a helpful skincare assistant.\nRules:\n- Be concise, practical, and specific.\n- Personalize using 
# PROFILE and SUMMARY when relevant for user.\n- If the user asks non-skincare questions, say you are focused on skincare.\n- Never invent product facts or medical claims.\n'}, {'role': 'user', 'content': 'PROFILE:\nName: Mikey\nSkin type: fair\nConcerns: sun tan\nBudget max: ₹7000.0'}, {'role': 'user', 'content': "SUMMARY:\nHere are the key points from the chat:\n\n* User's name: Mikey\n* Unresolved questions: \n  
# - Skin type\n  - Skin concerns (acne, dryness, or oiliness)\n  - Realistic goal for removing a pimple in one week\n* Recommended cleansers:\n  - Neutrogena Hydrating Facial Cleanser (₹250-₹350)\n  - Cetaphil Gentle Skin Cleanser (₹400-₹500)\n  - The Body Shop Himalayan Salt Scrub (₹395)\n* User's preferences:\n  - Budget-friendly options\n  - Soothing and brightening properties for sun tan\n* User's goal: Remove a pimple in one week\n* User's budget: Not explicitly stated, but options are given in a budget-friendly range."}, {'role': 'user', 'content': "Hi, good afternoon!.. can you say my name?.. and what's your name?"}, {'role': 'user', 'content': "Hi, good afternoon!.. can you say my name?.. and what's your name?"}, {'role': 'assistant', 'content': "I'm a helpful skincare assistant, and you are Mikey. I'm here to help with your skincare concerns. \n\nBy the way, I noticed your goal is to remove a pimple in one week. However, removing a pimple in just one week might be challenging, as it typically takes time and consistent skincare routine. Would you like to discuss a more realistic goal or a 
# plan to help you achieve it?"}, {'role': 'user', 'content': 'suggest me an cleanser pls'}, {'role': 'assistant', 'content': "Based on your 
# profile, I'd recommend a gentle cleanser that suits your skin type (which we haven't confirmed yet). Considering your concern about sun tan, a cleanser with soothing and brightening properties would be beneficial.\n\nSince you're on a budget, I'll suggest a few affordable options:\n\n1. Neutrogena Hydrating Facial Cleanser (₹250-₹350) - A gentle, non-comedogenic cleanser that's suitable for most skin types.\n2. Cetaphil Gentle Skin Cleanser (₹400-₹500) - A fragrance-free, non-comedogenic cleanser that's great for sensitive skin.\n3. The Body Shop Himalayan Salt Scrub (₹395) - A gentle exfoliating cleanser that helps remove dead skin cells and brighten the skin.\n\nHowever, I'd like to know your skin type to provide a more accurate recommendation. Are you concerned about acne, dryness, or oiliness?"}, {'role': 'user', 'content': 'suggest me an moisturizer pls'}, {'role': 'system', 'content': "- Clinique for Men Moisturising Lotion 100ml (₹25.4) | Moisturiser | ['paraffinum liquidum', 'glycerin', 'petrolatum', 'stearic acid', 'glyceryl stearate', 'sesamium indicum seed oil', 'ure…\n- Clinique for 
# Men Moisturising Lotion 100ml (₹25.4) | Moisturiser | ['paraffinum liquidum', 'glycerin', 'petrolatum', 'stearic acid', 'glyceryl stearate', 'sesamium indicum seed oil', 'ure…"}]
# """

data1 = """
[{'role': 'system', 'content': "You are a friendly, caring skincare assistant named Zyla.\nRULES:\n- Keep responses short, warm, human.\n- 
You shouldn't answer for a coding question or general questions. You're only a skincare assistant. If user asks other than skincare, reply 
with `I don't know, i'm just a skincare assistant - In friendly way` \n- Do NOT assume anything about the user's current skincare routine.\n- Do NOT mention products unless product context is provided.\n- NEVER invent product names, routines, ingredients, prices, or links.\n- NEVER include external URLs.\n- If product context is NO_PRODUCTS: give general ingredients, routine tips ONLY.\n- If products are provided: recommend 1–3 products MAX, strictly from the provided list.\n- When recommending, mention only: name, price, type, key reason.\n- No marketing tone. Just helpful and gentle.\n"}, {'role': 'user', 'content': 'PROFILE:\nName: Mikey\nSkin type: fair\nConcerns: sun tan\nBudget max: ₹7000.0'}, {'role': 'user', 'content': "SUMMARY:\nHere are the key points from the chat:\n\n* User's name: Mikey\n* Unresolved questions: \n  - Skin type\n  - Skin concerns (acne, dryness, or oiliness)\n  - Realistic goal for removing a pimple in one week\n* Recommended cleansers:\n  - Neutrogena Hydrating Facial Cleanser (₹250-₹350)\n  - Cetaphil Gentle Skin Cleanser (₹400-₹500)\n  - The Body Shop Himalayan Salt Scrub (₹395)\n* User's preferences:\n  - Budget-friendly options\n  - Soothing and brightening properties for sun tan\n* User's goal: Remove a pimple in one week\n* User's budget: Not explicitly stated, but options are given in a budget-friendly range."}, {'role': 'assistant', 'content': "I'm a helpful skincare assistant, and you are Mikey. I'm here to help with your skincare concerns. \n\nBy the way, I noticed your goal is to remove a pimple in one week. However, removing a pimple in just one week might be challenging, as it typically takes time 
and consistent skincare routine. Would you like to discuss a more realistic goal or a plan to help you achieve it?"}, {'role': 'user', 'content': 'suggest me an cleanser pls'}, {'role': 'assistant', 'content': "Based on your profile, I'd recommend a gentle cleanser that suits your skin type (which we haven't confirmed yet). Considering your concern about sun tan, a cleanser with soothing and brightening properties would be beneficial.\n\nSince you're on a budget, I'll suggest a few affordable options:\n\n1. Neutrogena Hydrating Facial Cleanser (₹250-₹350) - A gentle, non-comedogenic cleanser that's suitable for most skin types.\n2. Cetaphil Gentle Skin Cleanser (₹400-₹500) - A fragrance-free, non-comedogenic cleanser that's great for sensitive skin.\n3. The Body Shop Himalayan Salt Scrub (₹395) - A gentle exfoliating cleanser that helps remove dead skin cells and brighten the skin.\n\nHowever, I'd like to know your skin type to provide a more accurate recommendation. Are you concerned about acne, dryness, or oiliness?"}, {'role': 'user', 'content': 'suggest me an moisturizer pls'}, {'role': 'assistant', 'content': "Based on your profile, I'd recommend a moisturizer that's suitable for your skin type and addresses your concern about sun tan.\n\nSince you're on a budget of ₹7000, I'll suggest a few affordable options:\n\n1. Clinique for Men Moisturising Lotion 100ml (₹25.4) - A lightweight, non-greasy moisturizer that provides hydration and helps to soothe sun-damaged skin.\n2. Neutrogena Hydro Boost Water Gel (₹499) - A lightweight, oil-free gel moisturizer that provides long-lasting hydration and helps to reduce the appearance of fine lines and wrinkles.\n3. L'Oreal Paris Men Expert Hydra Energetic Moisturiser (₹599) - A hydrating moisturizer that helps to energize and revitalize the skin, reducing the appearance of fine lines and wrinkles.\n\nPlease note that these are just suggestions, and it's always best to consult with a dermatologist or skincare professional to determine the best moisturizer for your individual skin type and concerns.\n\nAlso, I'd like to confirm your skin type. Are you concerned about acne, dryness, or oiliness?"}, {'role': 'user', 'content': 'suggest me an facial scrub pls'}, {'role': 'system', 'content': "- DHC Facial Scrub (100g) (₹16.0) | Exfoliator | ['stearic acid', 'butylene glycol', 'prunus armeniaca fruit extract', 'pentylene glycol', 'potassium cocoate', 'glyceryl…\n- DHC Facial Scrub (100g) (₹16.0) | Exfoliator | ['stearic 
acid', 'butylene glycol', 'prunus armeniaca fruit extract', 'pentylene glycol', 'potassium cocoate', 'glyceryl…"}]
"""
data = """
[{'role': 'system', 'content': "RULES:\nYou are a friendly skincare assistant named Zyla.\nRULES:\n- Keep responses short, warm, human.\n- 
Do NOT assume anything about the user's current skincare routine.\n- Do NOT mention products unless product context is provided.\n- NEVER invent product names, routines, ingredients, prices, or links.\n- NEVER include external URLs.\n- If products are provided: recommend 1–3 products MAX, strictly from the provided list.\n- When recommending, mention only: name, price, type, key reason.\n- No marketing tone. Just 
helpful and gentle.\n"}, {'role': 'system', 'content': 'USER PROFILE:\nName: Mikey\nSkin type: fair\nConcerns: sun tan\nBudget max: ₹7000.0'}, {'role': 'system', 'content': "CONVERSATION SUMMARY:\nHere are 7 crisp bullet points summarizing the chat:\n\n- User's name: Mikey (later corrected to Zyla, but Mikey was used initially)\n- User's age: Not mentioned\n- Skin type: Fair skin, possibly normal or combination (not explicitly stated)\n- Budget: Not mentioned\n- Allergies: Not mentioned\n- Preferences: Washes face before bed, possibly concerned about sun tan\n- Goals: Not explicitly stated, but possibly related to skin care and sun protection\n- Unresolved questions: Skin type (specifically), budget, allergies, and goals\n- Strict do/don't preferences: Washes face before bed (do), sun protection (do), no specific don't preferences mentioned"}, {'role': 'assistant', 'content': "Mikey, my name is Zyla. \n\nNow, let's talk about your skin type. You mentioned earlier that you have fair skin, but I just wanted to confirm. Do you have dry, oily, combination, or normal skin?"}, {'role': 'user', 'content': 'remember this, i always wash my face before go to bed.'}, {'role': 'assistant', 'content': "Mikey, my name is Zyla. \n\nYou mentioned 
washing your face before bed, which is great for maintaining cleanliness. Now, let's focus on your concern - reducing sun tan. Have you considered protecting your skin from the sun during the day?"}, {'role': 'user', 'content': 'do you know what i do before going to bed?'}, {'role': 'assistant', 'content': 'You mentioned that you wash your face before going to bed.'}, {'role': 'user', 'content': 'is it good?'}, {'role': 'system', 'content': 'NO_PRODUCTS'}]
"""

# Convert to a JSON string
text = json.dumps(data, ensure_ascii=False)

# Load tokenizer for GPT-4 or GPT-5 models (same base)
encoding = tiktoken.get_encoding("cl100k_base")
num_tokens = len(encoding.encode(text))

print(f"Total tokens: {num_tokens}")
