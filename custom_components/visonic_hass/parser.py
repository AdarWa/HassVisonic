

def parseData(data: bytes) -> str:
    readable = data.hex()
    readable = ' '.join(readable[i:i + 2] for i in range(0, len(readable), 2))
    readable = readable.replace("0a", "0a\n").strip()
    dataBlock = ""
    for el in readable.split("\n"):
        add = el.strip().replace("\n","") + "\n" if el.strip() != "" and el.strip() != " " and el.strip() != "\n" else ""
        dataBlock += add if add[:2] == "0d" and add[-3:] == "0a\n" else ""

    return dataBlock

class chunky:
    datasize: int  # Bits -->  8 is 1 Byte, 1 is Bits, 4 is Nibbles, greater than 8 is total bits e.g. 40 is 5 Bytes
    index: int  # 3 is Zones,
    length: int
    data: bytearray

    def __str__(self):
        return f"datasize {self.datasize}  index {self.index}   length {self.length}    data {str(self.data)}"

def chunkme(data) -> list:
    message_type = data[0]
    if data[3] == 0xFF or (data[
                               3] != 0xFF and message_type == 2):  # Check validity of data chunk (it could be valid and have no chunks)
        overall_length = data[2]
        retval = []
        current = 3
        while current < len(data) and (
                data[current] == 0xFF or (data[current] != 0xFF and current == 3 and message_type == 2)):
            c = chunky()
            c.datasize = data[current + 1]
            c.index = data[current + 2]
            c.length = data[current + 3]
            c.data = data[current + 4: current + c.length + 4]
            current = current + c.length + 4
            retval.append(c)
        if current - 2 == overall_length:
            return retval
    else:
        print(
            f"[handle_msgtypeB0] ******************************************************** Got No Chunks for {message_type}  data is {str(data)} ********************************************************")
    return []

def _makeInt(data) -> int:
    val = data[0]
    for i in range(1, len(data)):
        val = val + (pow(256, i) * data[i])
    # if len(data) == 4:
    #    t = data[0]
    #    t = t + (0x100 * data[1])
    #    t = t + (0x10000 * data[2])
    #    t = t + (0x1000000 * data[3])
    #    if t != val:
    #        log.debug(f"[_makeInt] **************************************** Not the same ***************************************** {t} {val}")
    return val

def makeHex(string):
    return int(string,16)

def parsePDU(string: str, id_: int | None = None):
    if string == "":
        return None
    pdu = string.split(" ")
    pduType = pdu[1]
    if pduType == "a5":
        # State Change
        eventStatus = pdu[3]
        if eventStatus == "04":
            sysStatus = int(pdu[4], 16)
            if sysStatus in [0x03]:
                status = "Entry Delay"
            elif sysStatus in [0x04, 0x0A, 0x13, 0x14]:
                status = "Armed Home"
            elif sysStatus in [0x05, 0x0B, 0x15]:
                status = "Armed Away"
            elif sysStatus in [0x01, 0x11]:
                status = "Arming Home"
            elif sysStatus in [0x02, 0x12]:
                status = "Arming Away"
            elif sysStatus in [0x07]:
                status = "Disarmed - Downloading"
            elif sysStatus in [0x06, 0x08, 0x09]:
                status = "Disarmed - User Test"
            elif sysStatus > 0x15:
                status = "Disarmed"
            else:
                status = "Disarmed"
            return [status,None]
        elif eventStatus == "02":
            return [None, None]
        else:
            return None
    elif pduType == "b0":
        if id_ is None:
            return [None, None]
        d = list(map(makeHex,pdu[2:-2]))
        if len(d) < 3:
            return [None, None]
        if d[0] == 0x03 and d[1] == 0x18:
            state = _makeInt(chunkme(d)[0].data[0:4])
            return [None, bool(state & (1 << id_) != 0)]
        else:
            return [None, None]
        


def parseDataBlock(string: str, id_: int | None = None):
    data = string.split("\n")
    status = None
    for pdu in data:
        s = parsePDU(pdu, id_)
        if s is not None:
            status = s
    return status
