from groq import Groq
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def get_flights(source, destination, date):

    prompt = f"""
    Generate 5 realistic flight options.

    Source: {source}
    Destination: {destination}
    Date: {date}

    Return ONLY valid JSON.

    Example:

    [
      {{
        "airline":"IndiGo",
        "time":"10:00 AM",
        "price":"4500",
        "class":"Economy"
      }}
    ]
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role":"user",
                "content":prompt
            }
        ]
    )

    content = response.choices[0].message.content

    return json.loads(content)