# for manually keying in codes
from summarizer.database import create_invite_code
from uuid import uuid4


code = uuid4()
code_str = str(code)
print("Code is", code_str)
print("Invite URL is https://t.me/url_summarizer_bot?start=" + code_str)
create_invite_code(code_str)
