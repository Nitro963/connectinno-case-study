from enum import Enum

from pydantic import BaseModel


class MsgEnum(str, Enum):
    text = 'text'
    auto = 'auto'


class Msg(BaseModel):
    msg: str
    msg_type: MsgEnum = MsgEnum.text


class AutoMsgPlaceHolder(Msg):
    msg: str = 'placeholder'
    msg_type: MsgEnum = MsgEnum.auto
