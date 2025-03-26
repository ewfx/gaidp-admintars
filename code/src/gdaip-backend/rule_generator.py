import json
import re
from typing import List, Dict, Optional
from deepseek_adapter import DeepSeekAdapter
# import Optional

class RuleGenerator:
    def __init__(self, api_key: str):
        self.llm_adapter = DeepSeekAdapter(api_key)
    
    def generate_profiling_rules(self, requirements: List[Dict]) -> List[Dict]:
        """Generate executable profiling rules with robust JSON parsing"""
        prompt = f"""
            ### STRICT INSTRUCTIONS ###
            1. Respond ONLY with valid JSON that can be parsed with json.loads()
            2. Ensure all strings are properly quoted and escaped
            3. Do not include any text outside the JSON structure
            4. Ensure all brackets and braces are properly closed

            Convert these requirements into data profiling rules. Format as:
            {{
                "rules": [
                    {{
                        "description": "rule description",
                        "fields": ["field1", "field2"],
                        "validation_logic": "python-like validation code",
                        "parameters": {{"param": "default"}}
                    }}
                ]
            }}

            Requirements:
            {self._safe_json_dumps(requirements)}
            """
        
        result = self.llm_adapter.generate(prompt, max_tokens=3000, temperature=0.3)
        print("In rules_generator.py")
        print("#################################################")
        return self._parse_llm_response(result)

    def _safe_json_dumps(self, data: any) -> str:
        """Safely convert data to JSON string with error handling"""
        try:
            return json.dumps(data, indent=2)
        except (TypeError, ValueError) as e:
            return str(data)

    def _parse_llm_response(self, response: str) -> List[Dict]:
        """Robust parsing of LLM response with multiple fallback strategies"""
        try:
            # Strategy 1: Direct JSON parse
            try:
                data = json.loads(response)
                if isinstance(data, dict) and 'rules' in data:
                    return data['rules']
                return data if isinstance(data, list) else [data]
            except json.JSONDecodeError:
                pass

            # Strategy 2: Extract JSON from markdown
            md_json = self._extract_json_from_markdown(response)
            if md_json:
                return md_json

            # Strategy 3: Find JSON-like substring
            json_str = self._find_json_substring(response)
            if json_str:
                return json.loads(json_str)

            # Strategy 4: Manual repair attempts
            repaired = self._attempt_json_repair(response)
            if repaired:
                return json.loads(repaired)

            # Strategy 5: If all else fails, return empty list
            print(f"WARNING: Could not parse LLM output. Raw response:\n{response[:500]}...")
            return []

        except Exception as e:
            raise ValueError(
                f"Failed to parse LLM output: {str(e)}\n"
                f"Original response:\n{response[:500]}..."  # Truncate for readability
            )

    def _extract_json_from_markdown(self, text: str) -> Optional[List[Dict]]:
        """Extract JSON from markdown code blocks"""
        try:
            pattern = r'```(?:json)?\n(.*?)\n```'
            matches = re.findall(pattern, text, re.DOTALL)
            if matches:
                return json.loads(matches[0])
        except (json.JSONDecodeError, re.error):
            pass
        return None

    def _find_json_substring(self, text: str) -> Optional[str]:
        """Find the most likely JSON substring in malformed response"""
        try:
            # Look for outermost brackets
            start = text.find('[')
            end = text.rfind(']') + 1
            if start >= 0 and end > start:
                candidate = text[start:end]
                # Validate by attempting parse
                json.loads(candidate)
                return candidate
        except json.JSONDecodeError:
            pass
        return None

    def _attempt_json_repair(self, text: str) -> Optional[str]:
        """Attempt to repair common JSON issues"""
        try:
            # Fix common issues
            repaired = text.strip()
            
            # Remove non-JSON prefix/suffix
            if not repaired.startswith('[') and not repaired.startswith('{'):
                repaired = repaired[repaired.find('['):]
            
            # Ensure proper termination
            if not repaired.endswith(']') and not repaired.endswith('}'):
                last_brace = max(repaired.rfind(']'), repaired.rfind('}'))
                if last_brace > 0:
                    repaired = repaired[:last_brace+1]
            
            # Escape newlines in strings
            repaired = re.sub(r'(?<!\\)"', r'\"', repaired)
            
            # Validate the repair
            json.loads(repaired)
            return repaired
        except json.JSONDecodeError:
            return None

    def generate_executable_code(self, rules: List[Dict]) -> str:
        """Generate Python code with strict output formatting"""
        prompt = f"""
        ### CODE GENERATION INSTRUCTIONS ###
        1. Respond ONLY with the Python code
        2. Do not include markdown formatting
        3. Ensure all quotes are properly escaped
        4. The code must be syntactically valid

        Create a validate_transaction function implementing these rules:
        {self._safe_json_dumps(rules)}
        """
        
        print("In rules_generator.py, generate_executable_code")
        print("#################################################")
        result = self.llm_adapter.generate(prompt, max_tokens=3000, temperature=0.1)
        return self._clean_code_output(result)

    def _clean_code_output(self, code: str) -> str:
        """Clean code output from LLM artifacts"""
        # Remove markdown code blocks
        code = re.sub(r'```(?:python)?\n?', '', code)
        
        # Remove any remaining non-code text
        lines = [line for line in code.split('\n') 
                if not line.strip().startswith(('#', '//', '/*'))]
        
        return '\n'.join(lines).strip()