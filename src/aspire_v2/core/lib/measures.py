from .interfaces import Measure


class Accuracy(Measure):
    display_name = "Accuracy"

    def __init__(self, *, rel: int, cutoff: int) -> None:
        self.rel = rel
        self.cutoff = cutoff

    @property
    def measure_name(self) -> str:
        self._measure_name = f"Accuracy(rel={self.rel})@{self.cutoff}"


class AlphaDCG(Measure):
    display_name = "Alpha DCG"

    def __init__(
        self, *, rel: int, cutoff: int, alpha: float, judged_only: bool
    ) -> None:
        self.rel = rel
        self.cutoff = cutoff
        self.alpha = alpha
        self.judged_only = judged_only

    @property
    def measure_name(self) -> str:
        return (
            f"alpha_DCG(alpha={self.alpha},rel={self.rel},judged_only={self.judged_only})"
            f"@{self.cutoff}"
        )


class AlphaNDCG(Measure):
    display_name = "Alpha nDCG"

    def __init__(
        self, *, rel: int, cutoff: int, alpha: float, judged_only: bool
    ) -> None:
        self.rel = rel
        self.cutoff = cutoff
        self.alpha = alpha
        self.judged_only = judged_only

    @property
    def measure_name(self) -> str:
        return (
            f"alpha_nDCG(alpha={self.alpha},rel={self.rel},judged_only={self.judged_only})"
            f"@{self.cutoff}"
        )


class AveragePrecision(Measure):
    display_name = "Average Precision"

    def __init__(
        self, *, rel: int, cutoff: int, alpha: float, judged_only: bool
    ) -> None:
        self.rel = rel
        self.cutoff = cutoff
        self.judged_only = judged_only

    @property
    def measure_name(self) -> str:
        return f"AP(rel={self.rel},judged_only={self.judged_only})@{self.cutoff}"


class IntentAwareAveragePrecision(Measure):
    display_name = "Intent-aware Average Precison"

    def __init__(
        self, *, rel: int, cutoff: int, alpha: float, judged_only: bool
    ) -> None:
        self.rel = rel
        self.judged_only = judged_only

    @property
    def measure_name(self) -> str:
        return f"AP_IA(rel={self.rel},judged_only={self.judged_only})"


class BejeweledPlayerModel(Measure):
    display_name = "Bejeweled Player Model"

    def __init__(self, *, min_rel: int, max_rel: int, cutoff: int, T: float) -> None:
        self.min_rel = min_rel
        self.max_rel = max_rel
        self.cutoff = cutoff
        self.T = T

    @property
    def measure_name(self) -> str:
        return (
            f"BPM(T={self.T},min_rel={self.min_rel},max_rel={self.max_rel})"
            f"@{self.cutoff}"
        )


class BinaryPreference(Measure):
    display_name = "Binary Preference"

    def __init__(self, *, rel: int) -> None:
        self.rel = rel

    @property
    def measure_name(self) -> str:
        return f"Bpref(rel={self.rel})"


class NumberOfQueries(Measure):
    display_name = "Number of Queries"

    @property
    def measure_name(self) -> str:
        return "NumQ"


class NumberOfRelevantDocuments(Measure):
    display_name = "Numbe of Relevant Documents"

    def __init__(self, *, rel: int) -> None:
        self.rel = rel

    @property
    def measure_name(self) -> str:
        return f"NumRel(rel={self.rel})"


class NumberOfResults(Measure):
    display_name = "Numbe of Results"

    def __init__(self, *, rel: int) -> None:
        self.rel = rel

    @property
    def measure_name(self) -> str:
        return f"NumRet(rel={self.rel})"
