"""Définition des protocoles de ré-identification."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class ReidProtocol:
    """Sujets et relations identité/retest d'un protocole RE-ID."""

    subject_pairs: Mapping[str, str]
    reference_subject: str
    n_points: int = 12

    def __post_init__(self) -> None:
        pairs = dict(self.subject_pairs)
        if self.reference_subject not in pairs:
            raise ValueError("Le sujet de référence doit appartenir à subject_pairs.")
        if self.n_points < 2:
            raise ValueError("n_points doit être supérieur ou égal à 2.")
        object.__setattr__(self, "subject_pairs", MappingProxyType(pairs))

    @property
    def intra_identity_subject(self) -> str:
        return self.subject_pairs[self.reference_subject]

    @property
    def comparison_subjects(self) -> tuple[str, ...]:
        return tuple(self.subject_pairs.values())

    @property
    def subjects(self) -> tuple[str, ...]:
        return (self.reference_subject, *self.comparison_subjects)


HCP_REID_PROTOCOL = ReidProtocol(
    subject_pairs={
        "103818": "103818_re",
        "135528": "135528_re",
        "143325": "143325_re",
        "177746": "177746_re",
        "194140": "194140_re",
        "250427": "250427_re",
        "433839": "433839_re",
        "627549": "627549_re",
        "783462": "783462_re",
        "861456": "861456_re",
    },
    reference_subject="103818",
)
