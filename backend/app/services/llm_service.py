import os
from typing import List, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

class ComplianceFinding(BaseModel):
    rule_id: str
    rule_text: str
    document_excerpt: str
    suggestion: str
    correction: Optional[str] = None

def get_compliance_suggestions(document_content: str, relevant_rules: List[Dict]) -> List[ComplianceFinding]:
    """
    Generates compliance suggestions using an LLM based on document content and relevant rules.
    """
    findings = []

    for i, rule_text in enumerate(relevant_rules):
        rule_id = f"rule_{i+1}" # Generate a simple rule ID

        prompt = f"""
        Analyze the following document content against the provided compliance rule. 
        Identify any potential non-compliance, suggest a solution, and propose a correction for the document.

        Document Content:
        {document_content}

        Compliance Rule (ID: {rule_id}):
        {rule_text}

        Provide your analysis in the following structured JSON format:
        {{
            "document_excerpt": "[Relevant excerpt from document]",
            "suggestion": "[Suggestion for compliance]",
            "correction": "[Proposed correction for the document content]"
        }}
        """

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",  # Or any other suitable model
                messages=[
                    {"role": "system", "content": "You are an AI compliance assistant. Your task is to identify non-compliance and provide actionable suggestions and corrections."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Assuming the response is a JSON string
            # You might need more robust parsing here
            import json
            llm_output = json.loads(response.choices[0].message.content)

            findings.append(ComplianceFinding(
                rule_id=rule_id,
                rule_text=rule_text,
                document_excerpt=llm_output.get("document_excerpt", ""),
                suggestion=llm_output.get("suggestion", ""),
                correction=llm_output.get("correction", None)
            ))
        except Exception as e:
            print(f"Error generating compliance suggestion for rule {rule_id}: {e}")
            findings.append(ComplianceFinding(
                rule_id=rule_id,
                rule_text=rule_text,
                document_excerpt="N/A",
                suggestion=f"Could not generate suggestion due to error: {e}",
                correction=None
            ))
    
    return findings
