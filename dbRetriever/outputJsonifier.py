import re
import ast

from typing import List

def find_locations(input_string: str, token: str):
    return [i for i, char in enumerate(input_string) if char == token]

def add_if_needed_after(input_string: str, locations: List[int], required: List[str], inserter: str):
    modified_string = list(input_string)
    added = 0
    for loc in locations:
        for i in range(loc + 1+added, len(modified_string)):
            if modified_string[i] not in ['\n', '\t', ' ']:
                if modified_string[i] not in required:
                    modified_string.insert(loc+1 + added, inserter)
                    added += len(inserter)
                break
            
    return ''.join(modified_string)

def add_if_need_before(input_string: str, locations: List[int], required: List[str], inserter: str):
    modified_string = list(input_string)
    
    for loc in reversed(locations):
        for i in range(loc - 1, -1, -1):
            if modified_string[i] not in ['\n', '\t', ' ']:
                if modified_string[i] not in required:
                    modified_string.insert(loc, inserter)
                break
            
    return ''.join(modified_string)

def merge_extra_elements(input_string: str):
    # Parse the string into a Python list
    parsed_list = ast.literal_eval(input_string)
    
    # Iterate through each sublist
    for i, sublist in enumerate(parsed_list):
        if isinstance(sublist, list) and len(sublist) > 2:
            # Join all elements from the second element onward into a single string
            merged_string = ' '.join(sublist[1:])
            parsed_list[i] = [sublist[0], merged_string]
    
    return parsed_list

def clean_incomplete_and_trailing_comma(input_string: str) -> List[List[str]] | List[str]:
    
    pattern = r'\[([^\[\]]*?)\]'
    matches = re.findall(pattern, input_string)
    input_string = '[' + '\n'.join(matches) + ']'
    
    input_string = input_string.replace(":", ",")
    
    input_string = re.sub(r'#.*', '', input_string)
    
    # Strip any trailing whitespace or newline characters
    input_string = input_string.strip()

    # Find the last occurrence of an opening bracket and closing bracket
    last_open_bracket = input_string.rfind('(')
    last_close_bracket = input_string.rfind(')')
    
    # If the last open bracket comes after the last closing bracket, remove incomplete tuple
    if last_open_bracket > last_close_bracket:
        input_string = input_string[:last_close_bracket + 1]
    
    # Check for a trailing comma after the last closing bracket
    if input_string[last_close_bracket + 1:].lstrip().startswith(','):
        input_string = input_string[:last_close_bracket + 1] + input_string[last_close_bracket + 2:]
    
    # Finally, ensure the string is properly closed with a square bracket
    if not input_string.endswith(']'):
        input_string += ']'
        
    closing_parentheses_locations = find_locations(input_string, ")")    
    input_string = add_if_needed_after(input_string, closing_parentheses_locations, [',', ']'], ',')
    closing_parentheses_locations = find_locations(input_string, ")")
    input_string = add_if_need_before(input_string, closing_parentheses_locations, ['"'], '"')
    
    closing_parentheses_locations = find_locations(input_string, "(")    
    input_string = add_if_needed_after(input_string, closing_parentheses_locations, ['"'], '"')
    closing_parentheses_locations = find_locations(input_string, "(")
    input_string = add_if_need_before(input_string, closing_parentheses_locations, ['[', ","], ',')
    
    closing_parentheses_locations = find_locations(input_string, ",")    
    input_string = add_if_needed_after(input_string, closing_parentheses_locations, ['"', "("], '"')
    closing_parentheses_locations = find_locations(input_string, ",")
    input_string = add_if_need_before(input_string, closing_parentheses_locations, [')', '"'], '"')
        
    
    input_string = input_string.replace('(', '[').replace(')', ']')
    
    result: List[List[str]] = merge_extra_elements(input_string)
    
    for i in range(len(result)):
        if len(result[i]) < 2:
            return []
        result[i] = [result[i][0], ", ".join(result[i][1:])]

    return result