from channels.generic.websocket import AsyncWebsocketConsumer
from google import genai
import json 
import os
from google.genai import types

client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

# prompt = """
# You are an expert in Islamic dietary law.
# I will give you a string of ingredients.
# Your task is to:

# Extract the individual ingredients.

# Categorize them into the following keys:

# "halal": List of ingredients that are clearly permissible.

# "musbooh": List of ingredients that scholars differ on (doubtful).

# "haram": List of ingredients that are clearly impermissible.

# "explanations": A dictionary where each musbooh and haram ingredient has an explanation for why it is classified that way.

# "result": A string. The possible values are:

# "haram": If there is at least one haram ingredient.

# "musbooh": If there is no haram but at least one musbooh ingredient.

# "halal": If there are no haram or musbooh ingredients.

# Output the result in the following JSON format:

# {{
#   "halal": [],
#   "musbooh": [],
#   "haram": [],
#   "explanations": {{}},
#   "result": ""
# }}
# {}
# """

prompt = """
You are an expert in Islamic dietary law.
I will give you a string of ingredients.
Your task is to:

1. Extract the individual ingredients.

2. Categorize them into the following keys:

- "halal": List of ingredients that are clearly permissible.
- "musbooh": List of ingredients that scholars differ on (doubtful).
- "haram": List of ingredients that are clearly impermissible.
- "explanations": A dictionary where each musbooh and haram ingredient has an explanation for why it is classified that way.
- "result": A string. The possible values are:
    - "haram": If there is at least one haram ingredient.
    - "musbooh": If there is no haram but at least one musbooh ingredient.
    - "halal": If there are no haram or musbooh ingredients.

3. Output ONLY valid raw JSON (do not include backticks, markdown formatting, or code blocks).

{}
"""


class GenerateGeminiContent:

    @staticmethod
    def generate_content(*contents):
        
        response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=contents
            )
        return response
    
    @staticmethod
    def get_prompt(prompt_type, content=None):
        prompts = {
            'image': 'Extract and analyze the ingredients from the image',
            'string': f'Here\'s the ingredients string to analyze: {content}'
        }
        return prompt.format(prompts.get(prompt_type, ''))




class GeminiConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None:
            try:
                decoded = bytes_data.decode("utf-8")
                data = json.loads(decoded)
                if 'ingredients' not in data:
                    if 'image' not in data:
                        await self.send(text_data=json.dumps({
                            'status': 'failed',
                            'message': 'ingredients and image missing'
                        }))
                        return

                    # Dont have the ingredients so lets just use the image that we have
                    try:
                        imageb64 = data['image'].split(",")[1]
                        img =  types.Part.from_bytes(data=imageb64, mime_type='image/jpeg')
                        response = GenerateGeminiContent.generate_content(
                            img, GenerateGeminiContent.get_prompt('image')
                            )


                        await self.send(text_data=json.dumps({
                            'status': 'success',
                            'message': response.text,
                            'prompt' : prompt
                        }))
                        return
                    except Exception as e:
                        await self.send(text_data=json.dumps({
                            'status': 'failed',
                            'message': f'Error processing image: {str(e)}'
                        }))

                # we have the ingredients so lets try out sending a string of ingredients 
                try:
                    ingredients = data.get('ingredients')
                    response = GenerateGeminiContent.generate_content(
                        GenerateGeminiContent.get_prompt('string', ingredients)
                        )
                    
                    message = \
                        response.text.removeprefix("```json").removesuffix("```").strip() if 'json' in response.text else response.text
                    print(f'message: {message}')
                    await self.send(text_data=json.dumps({
                        'status': 'success',
                        'message': message,
                    }))
                    return 
                
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        'status': 'failed',
                        'message': f'Error processing ingredients string: {str(e)}'
                    }))
                
            except json.JSONDecodeError:
                await self.send(text_data=json.dumps({
                    'status': 'failed',
                    'message': 'Invalid JSON data'
                }))


        
