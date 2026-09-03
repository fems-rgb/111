import json,re,ast,logging
from typing import Any
logger=logging.getLogger(__name__)
def safe_json_parse(text,fallback=None,label=""):
    if not text or not isinstance(text,str):return fallback
    original=text.strip();tag=f"[{label}] " if label else ""
    try:return json.loads(original)
    except(json.JSONDecodeError,TypeError):pass
    cleaned=original
    if chr(96)*3 in cleaned:
        m=re.search(r"`{3}(?:json)?\s*\n?(.*?)\n?\s*`{3}",cleaned,re.DOTALL)
        if m:
            cleaned=m.group(1).strip()
            try:return json.loads(cleaned)
            except(json.JSONDecodeError,TypeError):pass
    for sc,ec in[("{","}"),("[","]")]: 
        s,e=cleaned.find(sc),cleaned.rfind(ec)
        if s>=0 and e>s:
            frag=cleaned[s:e+1]
            try:return json.loads(frag)
            except(json.JSONDecodeError,TypeError):
                fixed=re.sub(r",\s*([}\]])",r"\1",frag)
                try:return json.loads(fixed)
                except(json.JSONDecodeError,TypeError):pass
    try:
        result=ast.literal_eval(original);logger.warning(f"{tag}ast.literal_eval fallback");return result
    except(ValueError,SyntaxError):pass
    for sc,ec in[("{","}"),("[","]")]: 
        s,e=original.find(sc),original.rfind(ec)
        if s>=0 and e>s:
            frag=original[s:e+1]
            try:result=ast.literal_eval(frag);logger.warning(f"{tag}ast.literal_eval fragment");return result
            except(ValueError,SyntaxError):pass
    try:
        fixed=original.replace(chr(39),chr(34));return json.loads(fixed)
    except(json.JSONDecodeError,TypeError):pass
    logger.error(f"{tag}ALL FAILED: {original[:200]}");return fallback
