import contextlib
import math
import sys
from time import time
import timeit as _timeit
from typing import Any
from dataclasses import dataclass
from random import Random
import pickle

import pynarist

# Timeit code modified from IPython.core.magics.execution


class TimeitResult(object):
    """
    Object returned by the timeit magic with info about the run.

    Contains the following attributes :

    loops: (int) number of loops done per measurement
    repeat: (int) number of times the measurement has been repeated
    best: (float) best execution time / number
    all_runs: (list of float) execution time of each run (in s)
    compile_time: (float) time of statement compilation (s)

    """

    def __init__(self, loops, repeat, best, worst, all_runs, precision):
        self.loops = loops
        self.repeat = repeat
        self.best = best
        self.worst = worst
        self.all_runs = all_runs
        self._precision = precision
        self.timings = [dt / self.loops for dt in all_runs]

    @property
    def average(self):
        return math.fsum(self.timings) / len(self.timings)

    @property
    def stdev(self):
        mean = self.average
        return (
            math.fsum([(x - mean) ** 2 for x in self.timings]) / len(self.timings)
        ) ** 0.5

    def __str__(self):
        pm = "+-"
        if hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
            with contextlib.suppress(UnicodeEncodeError):
                "\xb1".encode(sys.stdout.encoding)
                pm = "\xb1"
        return "{mean} {pm} {std} per loop (mean {pm} std. dev. of {runs} run{run_plural}, {loops:,} loop{loop_plural} each)".format(
            pm=pm,
            runs=self.repeat,
            loops=self.loops,
            loop_plural="" if self.loops == 1 else "s",
            run_plural="" if self.repeat == 1 else "s",
            mean=_format_time(self.average, self._precision),
            std=_format_time(self.stdev, self._precision),
        )

    def _repr_pretty_(self, p, cycle):
        unic = self.__str__()
        p.text(f"<TimeitResult : {unic}>")


def _format_time(timespan, precision=3):
    """Formats the timespan in a human readable form"""

    if timespan >= 60.0:
        # we have more than a minute, format that in a human readable form
        # Idea from http://snipplr.com/view/5713/
        parts = [("d", 60 * 60 * 24), ("h", 60 * 60), ("min", 60), ("s", 1)]
        time = []
        leftover = timespan
        for suffix, length in parts:
            value = int(leftover / length)
            if value > 0:
                leftover = leftover % length
                time.append(f"{value}{suffix}")
            if leftover < 1:
                break
        return " ".join(time)

    # Unfortunately characters outside of range(128) can cause problems in
    # certain terminals.
    # See bug: https://bugs.launchpad.net/ipython/+bug/348466
    # Try to prevent crashes by being more secure than it needs to
    # E.g. eclipse is able to print a µ, but has no sys.stdout.encoding set.
    units = ["s", "ms", "us", "ns"]  # the safe value
    if hasattr(sys.stdout, "encoding") and sys.stdout.encoding:
        with contextlib.suppress(UnicodeEncodeError):
            "μ".encode(sys.stdout.encoding)
            units = ["s", "ms", "μs", "ns"]
    scaling = [1, 1e3, 1e6, 1e9]

    if timespan > 0.0:
        order = min(-int(math.floor(math.log10(timespan)) // 3), 3)
    else:
        order = 3
    return "%.*g %s" % (precision, timespan * scaling[order], units[order])


def timeit(
    code: str, repeat=7, number=1000, precision=3, ns: dict[str, Any] | None = None
):
    timefunc = _timeit.default_timer
    timer = _timeit.Timer(timer=timefunc)

    bc = compile(code, "<timeit>", "exec")
    exec(bc, ns)

    all_runs = timer.repeat(repeat, number)
    best = min(all_runs) / number
    worst = max(all_runs) / number
    return TimeitResult(number, repeat, best, worst, all_runs, precision)


# Model modified from rust_serialization_benchmark


class Address(pynarist.Model):
    x0: pynarist.byte
    x1: pynarist.byte
    x2: pynarist.byte
    x3: pynarist.byte

    @staticmethod
    def generate(rand: Random):
        return Address(
            x0=pynarist.byte(rand.randint(0, 127)),
            x1=pynarist.byte(rand.randint(0, 127)),
            x2=pynarist.byte(rand.randint(0, 127)),
            x3=pynarist.byte(rand.randint(0, 127)),
        )


@dataclass
class DAddress:
    x0: int
    x1: int
    x2: int
    x3: int

    @staticmethod
    def generate(rand: Random):
        return DAddress(
            x0=rand.randint(0, 127),
            x1=rand.randint(0, 127),
            x2=rand.randint(0, 127),
            x3=rand.randint(0, 127),
        )


class Log(pynarist.Model):
    address: Address
    identity: pynarist.varchar
    userid: pynarist.varchar
    request: pynarist.varchar
    code: pynarist.short
    size: pynarist.long

    @staticmethod
    def generate(rand: Random):
        USERID = [
            "-",
            "alice",
            "bob",
            "carmen",
            "david",
            "eric",
            "frank",
            "george",
            "harry",
        ]
        METHODS = ["GET", "POST", "PUT", "UPDATE", "DELETE"]
        ROUTES = [
            "/favicon.ico",
            "/css/index.css",
            "/css/font-awesome.min.css",
            "/img/logo-full.png",
            "/img/splash.png",
            "/js/jquery-3.5.1.min.js",
            "/api/login",
            "/api/logout",
            "/api/register",
        ]
        PROTOCOLS = ["HTTP/1.0", "HTTP/1.1", "HTTP/2", "HTTP/3"]
        request = (
            f"{rand.choice(METHODS)} {rand.choice(ROUTES)} {rand.choice(PROTOCOLS)}"
        )
        return Log(
            address=Address.generate(rand),
            identity=pynarist.varchar(f"user_{rand.randint(0, 1000)}"),
            userid=pynarist.varchar(rand.choice(USERID)),
            request=pynarist.varchar(request),
            code=pynarist.short(rand.randint(200, 599)),
            size=pynarist.long(rand.randint(0, 100_000_000)),
        )


@dataclass
class DLog:
    address: DAddress
    identity: str
    userid: str
    request: str
    code: int
    size: int

    @staticmethod
    def generate(rand: Random):
        USERID = [
            "-",
            "alice",
            "bob",
            "carmen",
            "david",
            "eric",
            "frank",
            "george",
            "harry",
        ]
        METHODS = ["GET", "POST", "PUT", "UPDATE", "DELETE"]
        ROUTES = [
            "/favicon.ico",
            "/css/index.css",
            "/css/font-awesome.min.css",
            "/img/logo-full.png",
            "/img/splash.png",
            "/js/jquery-3.5.1.min.js",
            "/api/login",
            "/api/logout",
            "/api/register",
        ]
        PROTOCOLS = ["HTTP/1.0", "HTTP/1.1", "HTTP/2", "HTTP/3"]
        request = (
            f"{rand.choice(METHODS)} {rand.choice(ROUTES)} {rand.choice(PROTOCOLS)}"
        )
        return DLog(
            address=DAddress.generate(rand),
            identity=f"user_{rand.randint(0, 1000)}",
            userid=rand.choice(USERID),
            request=request,
            code=rand.randint(200, 599),
            size=rand.randint(0, 100_000_000),
        )


class Logs(pynarist.Model):
    logs: pynarist.vector[Log]

    @staticmethod
    def generate(rand: Random):
        n = rand.randint(1000, 100000)
        # print("Logs", n)
        entries = [Log.generate(rand) for _ in range(n)]
        return Logs(logs=pynarist.vector[Log](*entries))


@dataclass
class DLogs:
    logs: list[DLog]

    @staticmethod
    def generate(rand: Random):
        n = rand.randint(1000, 100000)
        # print("DLogs", n)
        entries = [DLog.generate(rand) for _ in range(n)]
        return DLogs(logs=entries)


def prs_bench(rand: Random):
    print("Pynarist benchmark")
    dataset = Logs.generate(rand)
    code = "dataset.build()"
    ns = {"dataset": dataset, "Logs": Logs}

    print(" - build:", timeit(code, ns=ns))

    encoded = dataset.build()
    code = "Logs.parse(encoded)"
    ns = {"encoded": encoded, "Logs": Logs}

    print(" - parse:", timeit(code, ns=ns, number=1))
    # print(Logs.parse(encoded))

    return dataset


def pickle_bench(rand: Random):
    print("Pickle benchmark")
    dataset = DLogs.generate(rand)
    code = "pickle.dumps(dataset)"
    ns = {"dataset": dataset, "pickle": pickle}

    print(" - dumps:", timeit(code, ns=ns))

    encoded = pickle.dumps(dataset)
    code = "pickle.loads(encoded)"
    ns = {"encoded": encoded, "pickle": pickle}

    print(" - loads:", timeit(code, ns=ns))
    return dataset


def bench():
    seed = time()
    pickle_bench(Random(seed))
    prs_bench(Random(seed))


if __name__ == "__main__":
    bench()
