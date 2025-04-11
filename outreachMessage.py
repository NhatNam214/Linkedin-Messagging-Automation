from langchain.prompts import PromptTemplate
import google.generativeai as genai
import os
from dotenv import load_dotenv
load_dotenv()

class OutreachMessageGenerator:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        self.client = genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.prompt_template = PromptTemplate(
            input_variables=["fullName", "jobTitle", "companyName", "description", "additional_context", "writing_style"],
            template="""
            You are an expert in professional networking and personalized outreach.
            Your task is to analyze a LinkedIn profile and draft a compelling outreach message
            that feels natural, engaging, and relevant to the recipient's background.

            ### LinkedIn Profile Details:
            - **Full Name:** {fullName}
            - **Job Title:** {jobTitle}
            - **Company Name:** {companyName}
            - **Description of Company:** {description}

            ### Additional Context:
            {additional_context}

            ### Writing Style:
            {writing_style}

            ### Message Requirements:
            - Email format
            - Start with a friendly and professional greeting.
            - Acknowledge the recipient’s background and expertise.
            - Express a relevant reason for connecting.
            - Keep the message concise, around 3-5 sentences.
            - End with a clear next step or call to action.

            ### Instructions:
            - Do not preface your message with phrases like "Okay, here's the LinkedIn connection request message."
            - Provide only the outreach message in plain text, without any introductory statements.
            - Ensure the message is friendly, professional, and relevant, acknowledging the recipient's background and providing a clear reason for connecting.
            """
                    )

    def generate_message(self, fullName, jobTitle, companyName, description, additional_context="", writing_style=""):
        """
        Generate a personalized LinkedIn outreach message.
        """
        prompt = self.prompt_template.format(
            fullName=fullName,
            jobTitle=jobTitle,
            companyName=companyName,
            description=description,
            additional_context=additional_context,
            writing_style=writing_style
        )

        # Call Gemini API
        response = self.model.generate_content(prompt)
        return response.text if response.text else "No response generated."

if __name__ == "__main__":
    api_key = os.getenv("GOOGLE_API_KEY")
    generator = OutreachMessageGenerator(api_key)

    linkedin_data = {
        "fullName": "Thao Le",
        "jobTitle": "Manager | Banking, Financial Services, Technology & Professional Services",
        "companyName": "ManpowerGroup Vietnam",
        "description": '''ManpowerGroup is the largest global permanent recruitment, staffing and outsourcing company in Vietnam with offices in HCMC and Hanoi and many recruitment hubs nationwide.
        Apart from our top-notch permanent recruitment and executive search capability, we are the leading HR agency providing blue collar workers in manufacturing, technology, logistics/supply chain/e-commerce/warehouse as well as white collar workforce in finance, HR and office administration.
        With our 120+ highly experienced consultants, we are confident to provide you with innovative, tailor-made workforce solutions, enabling your business to win in the ever-changing world of work''',
        "additional_context": '''We’ve recently launched a new line of solar battery products that leverages advanced technology to enhance energy conversion efficiency and extend battery lifespan. 
        The solution is designed for both businesses and households seeking a more sustainable and cost-effective approach to energy usage. 
        I'm looking to connect with professionals in the clean energy space to exchange insights, explore potential collaborations, and discuss market opportunities where this solution can make a real impact.   
        ''',
        "writing_style": "Casual yet professional. Friendly greeting, acknowledges expertise, and includes a polite call to action."
    }

    message = generator.generate_message(**linkedin_data)
    print(message)