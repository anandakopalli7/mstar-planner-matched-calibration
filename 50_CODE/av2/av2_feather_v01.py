"""av2_feather_v01: a minimal, pure-Python reader for Arrow IPC (Feather v2) files (Claude line, 1 Nov 2026).

Why: the CANMOT environment has no pyarrow, and installing one would mean downloading packages. The Argoverse 2 tables we
need (annotations.feather, city_SE3_egovehicle.feather) are small Arrow IPC files. This module parses the IPC footer,
schema and record batches with a hand-written flatbuffer reader, and decompresses LZ4-frame or uncompressed buffers.
Supported column types: signed/unsigned integers, float32/float64, bool, utf8 / large_utf8 strings, and
dictionary-encoded strings. Anything else raises NotImplementedError (fail loudly, never guess).

The files are untrusted data: this module only parses bytes; nothing is executed. Run under `python -I`.

Usage:
    from av2_feather_v01 import read_feather
    cols = read_feather(path)      # dict name -> numpy array (strings as numpy unicode arrays)
"""
import struct

import numpy as np

MAGIC = b"ARROW1"

# ----------------------------------------------------------------------------------------------- flatbuffers


class FB:
    """Read-only view of one flatbuffer table."""

    def __init__(self, buf, pos):
        self.buf, self.pos = buf, pos
        vt = pos - struct.unpack_from("<i", buf, pos)[0]
        self.vt_len = struct.unpack_from("<H", buf, vt)[0]
        self.vt = vt

    def _off(self, i):
        o = 4 + 2 * i
        if o >= self.vt_len:
            return 0
        return struct.unpack_from("<H", self.buf, self.vt + o)[0]

    def scalar(self, i, fmt, default=0):
        o = self._off(i)
        return default if o == 0 else struct.unpack_from("<" + fmt, self.buf, self.pos + o)[0]

    def table(self, i):
        o = self._off(i)
        if o == 0:
            return None
        p = self.pos + o
        return FB(self.buf, p + struct.unpack_from("<I", self.buf, p)[0])

    def _vec(self, i):
        o = self._off(i)
        if o == 0:
            return None, 0
        p = self.pos + o
        v = p + struct.unpack_from("<I", self.buf, p)[0]
        return v + 4, struct.unpack_from("<I", self.buf, v)[0]

    def string(self, i):
        start, n = self._vec(i)
        return None if start is None else bytes(self.buf[start:start + n]).decode("utf-8")

    def tables(self, i):
        start, n = self._vec(i)
        if start is None:
            return []
        out = []
        for k in range(n):
            p = start + 4 * k
            out.append(FB(self.buf, p + struct.unpack_from("<I", self.buf, p)[0]))
        return out

    def structs(self, i, fmt, size):
        start, n = self._vec(i)
        if start is None:
            return []
        return [struct.unpack_from("<" + fmt, self.buf, start + size * k) for k in range(n)]


def root(buf, pos=0):
    return FB(buf, pos + struct.unpack_from("<I", buf, pos)[0])


# ----------------------------------------------------------------------------------------------- LZ4 frame


def _lz4_block(src, out):
    i, n = 0, len(src)
    while i < n:
        token = src[i]
        i += 1
        lit = token >> 4
        if lit == 15:
            while True:
                b = src[i]
                i += 1
                lit += b
                if b != 255:
                    break
        out += src[i:i + lit]
        i += lit
        if i >= n:
            break
        off = src[i] | (src[i + 1] << 8)
        i += 2
        if off == 0:
            raise ValueError("lz4: zero offset")
        ml = token & 15
        if ml == 15:
            while True:
                b = src[i]
                i += 1
                ml += b
                if b != 255:
                    break
        ml += 4
        start = len(out) - off
        if start < 0:
            raise ValueError("lz4: offset before start")
        if off >= ml:
            out += out[start:start + ml]
        else:
            for k in range(ml):
                out.append(out[start + k])
    return out


def lz4_frame_decompress(data):
    data = memoryview(data)
    if struct.unpack_from("<I", data, 0)[0] != 0x184D2204:
        raise ValueError("not an LZ4 frame")
    flg = data[4]
    if (flg >> 6) != 1:
        raise ValueError("lz4: unsupported frame version")
    block_checksum, content_size, content_checksum, dict_id = (flg >> 4) & 1, (flg >> 3) & 1, (flg >> 2) & 1, flg & 1
    if dict_id:
        raise NotImplementedError("lz4: dictionary id")
    p = 6 + (8 if content_size else 0) + 1  # FLG, BD, [size], HC
    out = bytearray()
    while True:
        bs = struct.unpack_from("<I", data, p)[0]
        p += 4
        if bs == 0:
            break
        raw, size = bs >> 31, bs & 0x7FFFFFFF
        chunk = bytes(data[p:p + size])
        p += size
        if raw:
            out += chunk
        else:
            _lz4_block(chunk, out)
        if block_checksum:
            p += 4
    if content_checksum:
        p += 4
    return bytes(out)


# ----------------------------------------------------------------------------------------------- Arrow IPC

T_INT, T_FLOAT, T_UTF8, T_BOOL, T_LARGE_UTF8 = 2, 3, 5, 6, 20


def _field_info(f):
    tt = f.scalar(2, "B")
    t = f.table(3)
    info = {"name": f.string(0), "type": tt}
    if tt == T_INT:
        info["bits"], info["signed"] = t.scalar(0, "i"), bool(t.scalar(1, "B"))
    elif tt == T_FLOAT:
        info["precision"] = t.scalar(0, "h")
    elif tt in (T_UTF8, T_LARGE_UTF8, T_BOOL):
        pass
    else:
        raise NotImplementedError("arrow type id %d (column %s)" % (tt, info["name"]))
    d = f.table(4)
    if d is not None:
        it = d.table(1)
        info["dict_id"] = d.scalar(0, "q")
        info["index_bits"] = it.scalar(0, "i") if it is not None else 32
        info["index_signed"] = bool(it.scalar(1, "B")) if it is not None else True
    if f.tables(5):
        raise NotImplementedError("nested arrow type (column %s)" % info["name"])
    return info


def _int_dtype(bits, signed):
    return np.dtype(("<i%d" if signed else "<u%d") % (bits // 8))


class _Batch:
    def __init__(self, buf, meta_pos, body_pos):
        msg = root(buf, meta_pos)
        self.header_type = msg.scalar(1, "B")
        self.header = msg.table(2)
        self.body = body_pos
        self.buf = buf

    def record_batch(self):
        rb = self.header if self.header_type == 3 else self.header.table(1)
        comp = rb.table(3)
        codec = None if comp is None else comp.scalar(0, "b")
        if codec not in (None, 0):
            raise NotImplementedError("arrow body compression codec %r (only LZ4_FRAME supported)" % codec)
        return rb.scalar(0, "q"), rb.structs(1, "qq", 16), rb.structs(2, "qq", 16), codec

    def buffer(self, off, length, codec):
        raw = bytes(self.buf[self.body + off:self.body + off + length])
        if codec is None or length == 0:
            return raw
        ulen = struct.unpack_from("<q", raw, 0)[0]
        if ulen == -1:
            return raw[8:]
        out = lz4_frame_decompress(raw[8:])
        if len(out) != ulen:
            raise ValueError("lz4: length mismatch")
        return out


def _decode(info, n, null_count, bufs, index_mode=False):
    tt = info["type"]
    valid = bufs[0]
    if null_count:
        bits = np.unpackbits(np.frombuffer(valid, np.uint8), bitorder="little")[:n].astype(bool)
    else:
        bits = None
    if index_mode:
        a = np.frombuffer(bufs[1], _int_dtype(info["index_bits"], info["index_signed"]), count=n).astype(np.int64)
        return a, bits
    if tt == T_INT:
        a = np.frombuffer(bufs[1], _int_dtype(info["bits"], info["signed"]), count=n).copy()
    elif tt == T_FLOAT:
        a = np.frombuffer(bufs[1], {0: "<f2", 1: "<f4", 2: "<f8"}[info["precision"]], count=n).astype(np.float64)
        if bits is not None:
            a[~bits] = np.nan
    elif tt == T_BOOL:
        a = np.unpackbits(np.frombuffer(bufs[1], np.uint8), bitorder="little")[:n].astype(bool)
    else:
        offs = np.frombuffer(bufs[1], "<i4" if tt == T_UTF8 else "<i8", count=n + 1)
        data = bufs[2]
        a = np.array([data[offs[k]:offs[k + 1]].decode("utf-8") for k in range(n)], dtype=str)
    if bits is not None and tt in (T_INT, T_BOOL, T_UTF8, T_LARGE_UTF8) and not bits.all():
        raise NotImplementedError("nulls in non-float column %s" % info["name"])
    return a, bits


def _consume(info, nodes, buffers, b, codec, n_buffers):
    node = nodes.pop(0)
    bl = [b.buffer(buffers[k][0], buffers[k][1], codec) for k in range(n_buffers)]
    del buffers[:n_buffers]
    return node, bl


def read_feather(path, columns=None):
    """Return {column: numpy array}. Strings come back as numpy unicode arrays."""
    with open(path, "rb") as fh:
        buf = fh.read()
    if buf[:6] != MAGIC or buf[-6:] != MAGIC:
        raise ValueError("not an Arrow IPC file: %s" % path)
    flen = struct.unpack_from("<i", buf, len(buf) - 10)[0]
    footer = root(buf, len(buf) - 10 - flen)
    schema = footer.table(1)
    fields = [_field_info(f) for f in schema.tables(1)]
    # Block struct: offset int64, metaDataLength int32, pad int32, bodyLength int64
    dict_blocks = footer.structs(2, "qiiq", 24)
    rb_blocks = footer.structs(3, "qiiq", 24)

    def open_block(blk):
        off, mlen, _, _ = blk
        p = off
        if struct.unpack_from("<I", buf, p)[0] == 0xFFFFFFFF:
            p += 8
        else:
            p += 4
        return _Batch(buf, p, off + mlen)

    dictionaries = {}
    for blk in dict_blocks:
        b = open_block(blk)
        if b.header_type != 2:
            raise ValueError("expected a dictionary batch")
        did = b.header.scalar(0, "q")
        if b.header.scalar(2, "B"):
            raise NotImplementedError("delta dictionaries")
        n, nodes, buffers, codec = b.record_batch()
        node, bl = _consume({"type": T_UTF8}, list(nodes), list(buffers), b, codec, 3)
        vals, _ = _decode({"type": T_UTF8, "name": "dict%d" % did}, node[0], node[1], bl)
        dictionaries[did] = vals
    out = {f["name"]: [] for f in fields}
    for blk in rb_blocks:
        b = open_block(blk)
        if b.header_type != 3:
            raise ValueError("expected a record batch")
        n, nodes, buffers, codec = b.record_batch()
        nodes, buffers = list(nodes), list(buffers)
        for f in fields:
            nb = 3 if (f["type"] in (T_UTF8, T_LARGE_UTF8) and "dict_id" not in f) else 2
            node, bl = _consume(f, nodes, buffers, b, codec, nb)
            if "dict_id" in f:
                idx, bits = _decode(f, node[0], node[1], bl, index_mode=True)
                if bits is not None and not bits.all():
                    raise NotImplementedError("nulls in dictionary column %s" % f["name"])
                out[f["name"]].append(dictionaries[f["dict_id"]][idx])
            else:
                a, _ = _decode(f, node[0], node[1], bl)
                out[f["name"]].append(a)
        if nodes or buffers:
            raise ValueError("unconsumed nodes/buffers: schema walk failed")
    res = {}
    for k, v in out.items():
        if columns is not None and k not in columns:
            continue
        res[k] = np.concatenate(v) if v else np.array([])
    return res


def describe(path):
    with open(path, "rb") as fh:
        buf = fh.read()
    flen = struct.unpack_from("<i", buf, len(buf) - 10)[0]
    footer = root(buf, len(buf) - 10 - flen)
    fields = [_field_info(f) for f in footer.table(1).tables(1)]
    return {"fields": fields, "dict_batches": len(footer.structs(2, "qiiq", 24)),
            "record_batches": len(footer.structs(3, "qiiq", 24))}
