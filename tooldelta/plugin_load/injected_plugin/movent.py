import time
import ujson as json
from typing import Any
from tooldelta.Frame import Frame,GameCtrl
from typing import Callable, Optional
from tooldelta.color_print import Print
from tooldelta.packets import Packet_CommandOutput


def check_avaliable(sth: Frame) -> Optional[AttributeError]:
    if sth is None:
        raise AttributeError(f"无法使用 {sth.__class__.__name__}, 因为其还未被初始化")


game_control: GameCtrl | None = None

def set_frame(my_frame: Frame) -> None:
    # 只有在系统启动后才能获得有效的 frame
    global frame, game_control
    frame = my_frame
    game_control = my_frame.get_game_control()


def sendcmd(
    cmd: str, waitForResp: bool = False, timeout: int = 30
) -> Callable[[str, bool, int], bytes | Packet_CommandOutput]:
    check_avaliable(game_control)
    if game_control.sendcmd is None:
        raise AttributeError(
            f"无法使用 {game_control.__class__.__name__}, 因为其还未被初始化"
        )
    return game_control.sendcmd(cmd=cmd, waitForResp=waitForResp, timeout=timeout)


def sendwscmd(
    cmd: str, waitForResp: bool = False, timeout: int | float = 30
) -> Callable[[str, bool, int], bytes | Packet_CommandOutput]:
    check_avaliable(game_control)
    return game_control.sendwscmd(cmd=cmd, waitForResp=waitForResp, timeout=timeout)


def sendwocmd(cmd: str) -> Callable[[str], None]:
    check_avaliable(game_control)
    game_control.sendwocmd(cmd=cmd)


def sendPacket(pktID: int, pkt: str) -> Callable[[int, str], None]:
    check_avaliable(game_control)
    game_control.sendPacket(pktID=pktID, pkt=pkt)


def sendPacketJson(pktID: int, pkt: str) -> Callable[[int, str], None]:
    # tip: 和sendPacket已经是同一个东西了
    check_avaliable(game_control)
    game_control.sendPacketJson(pktID=pktID, pkt=pkt)


def sendfbcmd(cmd: str) -> Callable[[str], None]:
    # 在除FastBuilder外的其他启动器上不可用
    check_avaliable(game_control)
    game_control.sendfbcmd(cmd=cmd)


def rawText(playername: str, text: str):

    sendcmd(
        r"""/tellraw %s {"rawtext":[{"text":"%s"}]}""" % (playername, text))


def tellrawText(playername: str, title: str | None = None, text: str = "") -> None:

    if title is None:
        sendcmd(
            r"""/tellraw %s {"rawtext":[{"text":"§r%s"}]}""" % (playername, text))
    else:
        sendcmd(
            r"""/tellraw %s {"rawtext":[{"text":"<%s> §r%s"}]}"""
            % (
                playername,
                title,
                text,
            )
        )


def get_all_player() -> list:
    check_avaliable(game_control)
    return game_control.allplayers


def is_op(playername: str) -> bool:
    check_avaliable(game_control)
    if playername not in get_all_player():
        return False
    return frame.launcher.is_op(playername)


def getTarget(sth: str, timeout: bool | int = 5) -> list:
    check_avaliable(game_control)
    "获取符合目标选择器实体的列表"
    if not sth.startswith("@"):
        raise Exception("Minecraft Target Selector is not correct.")
    result = (
        game_control.sendwscmd("/testfor %s" % sth, True, timeout)
        .OutputMessages[0]
        .Parameters
    )
    if result:
        result = result[0]
        return result.split(", ")
    else:
        return []


def find_key_from_value(dic: dict, val: Any) -> Any | None:
    # A bad method!
    for k, v in dic.items():
        if v == val:
            return k


def get_robotname() -> str:
    check_avaliable(game_control)
    return game_control.bot_name


def getPos(targetNameToGet: str, timeout: float | int = 5) -> dict:
    check_avaliable(game_control)

    if (
        (targetNameToGet not in get_all_player())
        and (targetNameToGet != game_control.bot_name)
        and (not targetNameToGet.startswith("@a"))
    ):
        raise Exception("Player not found.")
    result = sendwscmd("/querytarget " + targetNameToGet, True, timeout)
    if result.OutputMessages[0].Success == False:
        raise Exception(
            f"Failed to get the position: {result.OutputMessages[0]}"
        )
    parameter = result.OutputMessages[0].Parameters[0]
    if isinstance(parameter, str):
        resultList = json.loads(parameter)
    else:
        resultList = parameter
    result = {}
    for i in resultList:
        if game_control.players_uuid is None:
            raise Exception("Failed to get the players_uuid.")
        targetName = find_key_from_value(
            game_control.players_uuid, i["uniqueId"])
        x = i["position"]["x"] if i["position"]["x"] >= 0 else i["position"]["x"] - 1
        y = i["position"]["y"] - 1.6200103759765
        z = i["position"]["z"] if i["position"]["z"] >= 0 else i["position"]["z"] - 1
        position = {
            "x": float("%.2f" % x),
            "y": float("%.2f" % y),
            "z": float("%.2f" % z),
        }
        dimension = i["dimension"]
        yRot = i["yRot"]
        result[targetName] = {
            "dimension": dimension,
            "position": position,
            "yRot": yRot,
        }
    if targetNameToGet == "@a":
        return result
    else:
        if len(result) != 1:
            raise Exception("Failed to get the position.")
        if targetNameToGet.startswith("@a"):
            return list(result.values())[0]
        else:
            return result[targetNameToGet]


def countdown(delay: int | float, msg: str | None = None) -> None:

    if msg is None:
        msg = "Countdown"
    delayStart = time.time()
    delayStop = delayStart + delay
    while delay >= 0:
        if delay >= 0:
            delay = delayStop - time.time()
        else:
            delay = 0
        Print.print_inf("%s: %.2fs" % (msg, delay), end="\r")
        time.sleep(0.01)
    print("", end="\n")


def getBlockTile(x: int, y: int, z: int) -> str:
    "获取指定坐标的方块的ID"
    res = sendwscmd(f"/testforblock {x} {y} {z} air", True)
    if res.SuccessCount:
        return "air"
    else:
        print(res.OutputMessages[0].Parameters)
        return res.OutputMessages[0].Parameters[4].strip("%tile.").strip(".name")


def getTickingAreaList() -> dict:
    result = {}
    resultList = sendcmd(
        "/tickingarea list all-dimensions", True).OutputMessages
    if resultList[0].Success == False:
        return result
    for tickareaData in resultList[1].Message.split("%dimension.dimensionName")[1:]:
        tickareaDimension = tickareaData.split(": \n")[0]
        tickareaList = tickareaData.split(": \n")[1].split("\n")
        for tickarea in tickareaList:
            if not tickarea:
                continue
            tickareaName = tickarea.split("- ", 1)[1].split(": ", 1)[0]
            tickareaPos = {
                "start": tickarea.split(" ")[2:5],
                "end": tickarea.split(" ")[6:9],
            }
            tickareaPos["start"].pop(1)
            tickareaPos["end"].pop(1)
            result[tickareaName] = {"dimension": tickareaDimension}
            result[tickareaName].update(tickareaPos)
    return result
